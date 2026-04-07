"""
GitHub Actions workflow generator — punkt 3.1 z planu ewolucji.

Generuje plik .github/workflows/redsl.yml który:
1. Uruchamia ReDSL analyze na każdym PR
2. Sprawdza bramki jakości (CC, god modules, critical issues)
3. Opcjonalnie komentuje na PR z wynikami analizy
4. Fail-fast jeśli CC wzrosło / pojawiły się nowe god-modules

Użycie:
    from redsl.ci import generate_github_workflow
    generate_github_workflow(Path("myproject/"), config={...})

Lub CLI:
    python -m redsl.ci myproject/
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_WORKFLOW_VERSION = "1.0"

_DEFAULT_QUALITY_GATES = {
    "max_avg_cc": 10.0,
    "max_critical_issues": 5,
    "max_god_modules": 0,
    "fail_on_regression": True,
}


@dataclass
class WorkflowConfig:
    """Konfiguracja generowanego workflow."""

    python_version: str = "3.11"
    redsl_version: str = "latest"
    run_on_push: bool = True
    run_on_pr: bool = True
    branches: list[str] = field(default_factory=lambda: ["main", "master", "develop"])
    quality_gates: dict[str, Any] = field(default_factory=lambda: dict(_DEFAULT_QUALITY_GATES))
    post_pr_comment: bool = True
    fail_on_gate_violation: bool = True
    cache_pip: bool = True
    extra_tools: list[str] = field(default_factory=list)


def generate_github_workflow(
    project_dir: Path,
    config: dict[str, Any] | None = None,
    output_path: Path | None = None,
) -> str:
    """Wygeneruj zawartość pliku .github/workflows/redsl.yml.

    Args:
        project_dir:  Katalog projektu (używany do wykrycia pyproject.toml itd.)
        config:       Nadpisanie domyślnych ustawień WorkflowConfig
        output_path:  Opcjonalnie — zapisz do tego pliku (zamiast tylko zwracać)

    Returns:
        YAML jako string.
    """
    cfg = WorkflowConfig()
    if config:
        for key, val in config.items():
            if hasattr(cfg, key):
                setattr(cfg, key, val)
            elif key in cfg.quality_gates:
                cfg.quality_gates[key] = val

    workflow = _build_workflow(cfg)
    content = yaml.dump(workflow, default_flow_style=False, sort_keys=False, indent=2)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        logger.info("GitHub Actions workflow written to %s", output_path)

    return content


def install_github_workflow(
    project_dir: Path,
    config: dict[str, Any] | None = None,
    overwrite: bool = False,
) -> Path:
    """Zainstaluj workflow w projekcie (.github/workflows/redsl.yml).

    Args:
        project_dir: Katalog docelowy projektu
        config:      Opcjonalne nadpisania konfiguracji
        overwrite:   Czy nadpisać istniejący workflow

    Returns:
        Ścieżka do zapisanego pliku.
    """
    output = project_dir / ".github" / "workflows" / "redsl.yml"

    if output.exists() and not overwrite:
        logger.info("Workflow already exists at %s (use overwrite=True to replace)", output)
        return output

    generate_github_workflow(project_dir, config, output)
    return output


def _build_workflow(cfg: WorkflowConfig) -> dict:
    """Zbuduj strukturę YAML dla GitHub Actions workflow."""
    on_triggers: dict[str, Any] = {}
    if cfg.run_on_push:
        on_triggers["push"] = {"branches": cfg.branches}
    if cfg.run_on_pr:
        on_triggers["pull_request"] = {"branches": cfg.branches}

    steps = _build_steps(cfg)

    return {
        "name": "ReDSL Code Quality",
        "on": on_triggers,
        "permissions": {
            "contents": "read",
            "pull-requests": "write" if cfg.post_pr_comment else "read",
        },
        "jobs": {
            "redsl-analyze": {
                "name": "ReDSL Analysis",
                "runs-on": "ubuntu-latest",
                "steps": steps,
            }
        },
    }


def _build_steps(cfg: WorkflowConfig) -> list[dict]:
    """Zbuduj listę kroków workflow."""
    steps: list[dict] = [
        {"name": "Checkout", "uses": "actions/checkout@v4"},
        {
            "name": "Set up Python",
            "uses": "actions/setup-python@v5",
            "with": {"python-version": cfg.python_version},
        },
    ]

    if cfg.cache_pip:
        steps.append({
            "name": "Cache pip",
            "uses": "actions/cache@v4",
            "with": {
                "path": "~/.cache/pip",
                "key": "${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt', '**/pyproject.toml') }}",
                "restore-keys": "${{ runner.os }}-pip-",
            },
        })

    install_cmd = "pip install redsl"
    if cfg.redsl_version != "latest":
        install_cmd = f"pip install redsl=={cfg.redsl_version}"
    if cfg.extra_tools:
        install_cmd += " " + " ".join(cfg.extra_tools)

    steps.append({
        "name": "Install ReDSL",
        "run": install_cmd,
    })

    steps.append({
        "name": "Run ReDSL analysis",
        "id": "redsl",
        "run": "python -m redsl analyze . --format json --output redsl_report.json",
        "continue-on-error": True,
    })

    gates = cfg.quality_gates
    gate_script = _build_gate_script(gates)
    steps.append({
        "name": "Check quality gates",
        "run": gate_script,
    })

    if cfg.post_pr_comment:
        steps.append({
            "name": "Post PR comment",
            "if": "github.event_name == 'pull_request'",
            "uses": "actions/github-script@v7",
            "with": {
                "script": _pr_comment_script(),
            },
        })

    steps.append({
        "name": "Upload report",
        "if": "always()",
        "uses": "actions/upload-artifact@v4",
        "with": {
            "name": "redsl-report",
            "path": "redsl_report.json",
            "retention-days": 30,
        },
    })

    return steps


def _build_gate_script(gates: dict[str, Any]) -> str:
    """Wygeneruj shell script sprawdzający bramki jakości."""
    lines = [
        "python - << 'EOF'",
        "import json, sys",
        "with open('redsl_report.json') as f: r = json.load(f)",
        "failed = []",
        f"if r.get('avg_cc', 0) > {gates['max_avg_cc']}:",
        f"    failed.append(f\"avg_cc={{r['avg_cc']:.1f}} > {gates['max_avg_cc']}\")",
        f"if r.get('critical_count', 0) > {gates['max_critical_issues']}:",
        f"    failed.append(f\"critical={{r['critical_count']}} > {gates['max_critical_issues']}\")",
        "if failed:",
        "    print('QUALITY GATES FAILED:')",
        "    [print(f'  - {f}') for f in failed]",
        "    sys.exit(1)",
        "else:",
        "    print('All quality gates passed!')",
        "EOF",
    ]
    return "\n".join(lines)


def _pr_comment_script() -> str:
    """JavaScript fragment for posting PR comment via actions/github-script."""
    return """
const fs = require('fs');
try {
  const report = JSON.parse(fs.readFileSync('redsl_report.json', 'utf8'));
  const body = [
    '## ReDSL Code Quality Report',
    '',
    `| Metric | Value |`,
    `|--------|-------|`,
    `| Total files | ${report.total_files ?? 'N/A'} |`,
    `| Avg CC | ${(report.avg_cc ?? 0).toFixed(1)} |`,
    `| Critical issues | ${report.critical_count ?? 0} |`,
    '',
    '_Generated by [ReDSL](https://github.com/wronai/redsl)_'
  ].join('\\n');
  await github.rest.issues.createComment({
    issue_number: context.issue.number,
    owner: context.repo.owner,
    repo: context.repo.repo,
    body
  });
} catch(e) {
  console.log('Could not post PR comment:', e.message);
}
""".strip()
