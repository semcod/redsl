"""pyqual.yaml configuration generation."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def _run_cmd(cmd: list[str], cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout, cwd=str(cwd),
    )

_PYQUAL_YAML_TEMPLATE = """\
pipeline:
  name: quality-loop-{name}

  metrics:
    cc_max: 15
    critical_max: 30
    coverage_min: 20
    coverage_branch_min: 15
    completion_rate_min: 75
    ruff_errors_max: 150
    mypy_errors_max: 100

  stages:
    - name: ruff-lint
      tool: ruff
      when: always
      optional: true

    - name: mypy-types
      tool: mypy
      when: always
      optional: true

    - name: verify
      tool: vallm-verify
      optional: true
      when: after_fix

    - name: report
      tool: report
      when: always
      optional: true

    - name: push
      tool: git-push
      when: always
      optional: true

  loop:
    max_iterations: 3
    on_fail: report

  env:
    LLM_MODEL: openrouter/qwen/qwen3-coder-next
"""


def _pyqual_cli_available() -> bool:
    """Check if pyqual CLI is available."""
    return shutil.which("pyqual") is not None


def _generate_pyqual_yaml(project: Path, profile: str, pyqual_available: bool) -> bool:
    """Generate pyqual.yaml for a project."""
    if pyqual_available:
        proc = _run_cmd(["pyqual", "init", "--profile", profile, "."], project, timeout=60)
        return proc.returncode == 0 and (project / "pyqual.yaml").exists()
    content = _PYQUAL_YAML_TEMPLATE.format(name=project.name)
    (project / "pyqual.yaml").write_text(content, encoding="utf-8")
    return True


def _detect_publish_configured(pyqual_yaml: Path) -> bool:
    """Check if pyqual.yaml has publish configuration."""
    if not pyqual_yaml.exists():
        return False
    try:
        content = pyqual_yaml.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return any(token in content for token in ("publish", "twine-publish", "make-publish", "release-check"))
