# Example 11 — c2004 Healing Loop (alerts → redsl improve)

Real-world wiring of `redsl` into a production observability pipeline:
when a Prometheus alert or TestQL probe failure fires in the
[c2004 fleet management monorepo](https://github.com/maskservice/c2004),
a FastAPI webhook decides — based on alert labels — whether to invoke
`redsl gate check` or `redsl improve --max-actions 1 --dry-run` and ships
the result to the developer as an LLM-ready planfile ticket.

> **TL;DR** — c2004 turns redsl into the **autonomous quality-keeper**
> for a 60k-LOC monorepo. Every alert becomes either an "investigate"
> action (redsl gate) or a "propose-a-fix" action (redsl improve), all
> wrapped in `DRY_RUN=true` safety so the bot can't break the repo.

---

## Why redsl, why c2004?

c2004 has 4 quality-tool layers that all want to talk to LLMs:

| Layer | Tool | Output |
|---|---|---|
| Static metrics | code2llm + lizard | CSV |
| Refactor proposals | **redsl** | RefactorWorkflow plan + diff |
| Walk + restore | rebuild | walk artifacts + endpoint diff |
| Universal tickets | planfile | YAML schema |

`redsl` plays the **decision-maker** role in the healing loop. The
webhook never decides _what_ to change — it just decides _which redsl
mode_ to invoke based on alert severity. This separation lets c2004
treat redsl as a black-box quality service.

---

## Decision matrix

The healing-webhook reads the alert's `healing_strategy` label and dispatches:

| Alert label                 | redsl invocation                                          | Outcome |
|-----------------------------|-----------------------------------------------------------|---------|
| `healing_strategy=annotate` | none (just log)                                           | Grafana annotation |
| `healing_strategy=redsl_gate` | `redsl gate check /mnt/project`                          | exit 0/1 + violations.json |
| `healing_strategy=redsl_improve` | `redsl improve /mnt/project --max-actions 1 --dry-run` | proposed-patch.diff |
| `healing_strategy=rebuild_restore` | (rebuild — see rebuild example)                       | endpoint restored |

Every invocation is wrapped in `docker run --rm semcod/redsl:local …`
so the webhook image stays tiny.

---

## c2004's redsl.yaml — the contract

The workflow definition is at
[`c2004/redsl.yaml`](https://github.com/maskservice/c2004/blob/main/redsl.yaml).
Key sections:

```yaml
apiVersion: redsl.workflow/v1
kind: RefactorWorkflow
metadata:
  name: c2004-fleet-management

spec:
  perceive:
    use_code2llm: false
    use_redup: true                  # detect duplicate patterns

  decide:
    max_actions_per_run: 1           # one change at a time
    cost_limit_usd: 0.50

  act:
    write_changes: false             # DRY_RUN first
    rollback_on_failure: true

  validate:
    run_tests: true
    test_command: task test
    quality_gate:
      max_complexity: 15
      max_module_size: 300
      forbidden_patterns:
        - "**/*_pb2*.py"             # never touch generated code
        - "archive/**"
        - "_archive/**"
```

The webhook hands `/mnt/project` to the redsl container and lets it read
this manifest as the source of truth for *all* limits.

---

## healing-webhook integration (Python)

[`monitoring/healing-webhook/app.py`](https://github.com/maskservice/c2004/blob/main/monitoring/healing-webhook/app.py)
implements the dispatch:

```python
def heal_redsl_gate(component: str, detail: dict) -> dict:
    code, out, err = _run_docker(
        REDSL_IMAGE,
        ["python", "-m", "redsl", "gate", "check", "/mnt/project"],
    )
    return {"action": "redsl_gate", "exit": code, "outcome": "success" if code == 0 else "violations"}


def heal_redsl_improve(component: str, detail: dict) -> dict:
    if not _rate_limit_ok():
        return {"action": "redsl_improve", "outcome": "rate_limited"}
    cmd = ["python", "-m", "redsl", "improve", "/mnt/project", "--max-actions", "1"]
    if DRY_RUN:
        cmd.append("--dry-run")
    code, out, err = _run_docker(REDSL_IMAGE, cmd, timeout=300)
    return {"action": "redsl_improve", "exit": code, "outcome": "success" if code == 0 else "failed"}


def _run_docker(image: str, cmd: list[str], timeout: int = 120) -> tuple[int, str, str]:
    argv = ["docker", "run", "--rm",
            "--network=c2004-quality-net",
            "-v", f"{REPO_PATH}:/mnt/project:rw",
            "-w", "/mnt/project",
            image, *cmd]
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr
```

Notes:

- `DRY_RUN=true` is the **default** — flip via `HEALING_DRY_RUN=false` only
  when you trust the recommendations.
- `MAX_ACTIONS_PER_HOUR=4` is enforced **outside** redsl — the webhook
  refuses the call before docker even spins up. This avoids wasting LLM
  budget on the same flapping alert.

---

## Closed-loop demo (paste into c2004 repo root)

```bash
# 1. Build the redsl image once
task quality:up

# 2. Bring up monitoring + healing webhook
task monitor:up

# 3. Fire a synthetic alert (DRY_RUN-safe)
task monitor:test-heal STRATEGY=redsl_improve

# 4. Watch redsl run inside docker
docker logs -f c2004-healing-webhook
# → … running ['docker', 'run', '--rm', '...', 'redsl', 'improve', '...', '--dry-run']

# 5. The proposed patch is now an LLM-ready ticket in planfile.yaml
task planfile:list:llm

# 6. Show the ticket — has the redsl proposal + the 7-section schema
task planfile:show ID=PLF-XXX

# 7. Hand it to your favourite agent
task planfile:export ID=PLF-XXX OUT=fix.md
```

---

## Why this works for any project (not just c2004)

The webhook is ~250 LOC of FastAPI; the only c2004-specific bit is the
list of endpoints in `monitoring/prometheus/prometheus.yml`. Drop in your
own scrape targets and you get the same loop. The redsl invocation is
fully driven by `redsl.yaml`, so each project tunes:

- which directories redsl may touch (`forbidden_patterns`)
- how aggressive (`max_actions_per_run`)
- how to validate (`test_command`)
- where memories persist (`memory.path`)

---

## Files in this example

| File | Purpose |
|---|---|
| `README.md` (this file) | Walkthrough of the integration. |
| `redsl.yaml` | Trimmed copy of c2004's RefactorWorkflow. |
| `webhook_dispatch.py` | Standalone version of the redsl-dispatch logic. |
| `synthetic_alert.json` | Sample Alertmanager payload that triggers `redsl_improve`. |

---

## See also

- c2004 master doc: [`docs/planfile-llm-guide.md`](https://github.com/maskservice/c2004/blob/main/docs/planfile-llm-guide.md)
- Companion examples:
  - [`semcod/planfile/examples/c2004-healing/`](https://github.com/semcod/planfile/tree/main/examples/c2004-healing)
  - [`semcod/rebuild/docs/c2004.md`](https://github.com/semcod/rebuild/blob/main/docs/c2004.md)
- redsl deep-dives:
  - [`examples/03-full-pipeline/`](../03-full-pipeline/) — perceive→decide→act→validate
  - [`examples/09-pr-bot/`](../09-pr-bot/) — autonomous PR creation
