"""Standalone redsl-dispatch logic — extract of c2004 healing-webhook.

This is the minimal piece of FastAPI that c2004 uses to translate
Prometheus alerts into `redsl gate check` / `redsl improve --dry-run`
invocations. Strip out the Prometheus client + planfile parts to keep
the example focused on the redsl integration.

Run locally:

    pip install fastapi uvicorn
    uvicorn webhook_dispatch:app --port 8810

Then POST a synthetic alert:

    curl -X POST http://localhost:8810/alertmanager \
      -H 'Content-Type: application/json' \
      -d @synthetic_alert.json
"""

from __future__ import annotations

import os
import subprocess
import time
from collections import deque
from typing import Any

from fastapi import FastAPI, Request

REPO_PATH = os.getenv("REPO_PATH", "/repo")
REDSL_IMAGE = os.getenv("REDSL_IMAGE", "semcod/redsl:local")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() in {"1", "true", "yes"}
MAX_ACTIONS_PER_HOUR = int(os.getenv("MAX_ACTIONS_PER_HOUR", "4"))

app = FastAPI(title="redsl-dispatch demo")
_recent: deque[float] = deque(maxlen=MAX_ACTIONS_PER_HOUR * 4)


def _rate_limit_ok() -> bool:
    now = time.time()
    while _recent and now - _recent[0] > 3600:
        _recent.popleft()
    return len(_recent) < MAX_ACTIONS_PER_HOUR


def _run_redsl(cmd_tail: list[str], timeout: int = 300) -> dict[str, Any]:
    """Run `docker run --rm <REDSL_IMAGE> <cmd_tail>` and return outcome."""
    argv = [
        "docker", "run", "--rm",
        "-v", f"{REPO_PATH}:/mnt/project:rw",
        "-w", "/mnt/project",
        REDSL_IMAGE,
        *cmd_tail,
    ]
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    return {
        "exit": proc.returncode,
        "stdout": proc.stdout[-500:],
        "stderr": proc.stderr[-500:],
        "outcome": "success" if proc.returncode == 0 else "failed",
    }


def heal_redsl_gate(component: str, detail: dict) -> dict:
    """Severity=error → just check, never write."""
    return {
        "action": "redsl_gate",
        **_run_redsl(["python", "-m", "redsl", "gate", "check", "/mnt/project"], timeout=120),
    }


def heal_redsl_improve(component: str, detail: dict) -> dict:
    """Severity=critical → propose a 1-action patch (always dry-run by default)."""
    if not _rate_limit_ok():
        return {"action": "redsl_improve", "outcome": "rate_limited"}
    _recent.append(time.time())
    cmd = ["python", "-m", "redsl", "improve", "/mnt/project", "--max-actions", "1"]
    if DRY_RUN:
        cmd.append("--dry-run")
    return {
        "action": "redsl_improve",
        **_run_redsl(cmd, timeout=300),
    }


STRATEGIES = {
    "redsl_gate": heal_redsl_gate,
    "redsl_improve": heal_redsl_improve,
}


@app.get("/healthz")
def healthz() -> dict:
    return {
        "ok": True,
        "dry_run": DRY_RUN,
        "rate_budget": MAX_ACTIONS_PER_HOUR - len(_recent),
    }


@app.post("/alertmanager")
async def alertmanager_webhook(request: Request) -> dict:
    """Translate Alertmanager v4 webhook payload → redsl invocations."""
    payload = await request.json()
    results = []
    for alert in payload.get("alerts", []):
        labels = alert.get("labels", {})
        if alert.get("status") != "firing":
            continue
        strategy = STRATEGIES.get(labels.get("healing_strategy"))
        if not strategy:
            continue
        results.append(
            strategy(
                labels.get("component", "unknown"),
                {"labels": labels, "annotations": alert.get("annotations", {})},
            )
        )
    return {"received": len(payload.get("alerts", [])), "results": results}
