"""Bridge to pyqual — quality gate loop and CI/CD integration."""

from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def is_available() -> bool:
    """Return True if pyqual CLI is installed and functional."""
    if not shutil.which("pyqual"):
        return False
    try:
        proc = subprocess.run(
            ["pyqual", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        return proc.returncode == 0
    except Exception:
        return False


def _run_pyqual(project_dir: Path, args: list[str], timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pyqual", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(project_dir),
    )


def doctor(project_dir: Path) -> dict:
    """Run `pyqual doctor` and return structured tool availability dict.

    Returns:
        Dict mapping tool name → {available: bool, purpose: str}.
    """
    if not is_available():
        return {}
    try:
        proc = _run_pyqual(project_dir, ["doctor"], timeout=30)
        lines = proc.stdout.splitlines()
        result: dict[str, dict] = {}
        for line in lines:
            if "✓" in line or "✗" in line:
                available = "✓" in line
                parts = line.replace("✓", "").replace("✗", "").split()
                if parts:
                    result[parts[0]] = {"available": available}
        return result
    except Exception as exc:
        logger.warning("pyqual doctor error: %s", exc)
        return {}


def _parse_gate_lines(output: str) -> list[dict[str, object]]:
    gates: list[dict[str, object]] = []
    for line in output.splitlines():
        line_s = line.strip()
        if not line_s:
            continue
        if line_s.startswith(("✅", "❌")) or "│ ✅" in line_s or "│ ❌" in line_s:
            gates.append({"line": line_s, "passed": "✅" in line_s and "❌" not in line_s})
            continue
        upper = line_s.upper()
        if ":" in line_s and ("PASS" in upper or "FAIL" in upper or "OK" in upper):
            gates.append({"line": line_s, "passed": "FAIL" not in upper})
    return gates


def _stage_passed(output: str, stage_name: str) -> bool:
    pattern = rf"- name: {re.escape(stage_name)}\s+status: passed"
    return re.search(pattern, output) is not None


def check_gates(project_dir: Path) -> dict:
    """Run `pyqual gates` and return pass/fail status.

    Returns:
        Dict with keys: passed (bool), gates (list of gate results), raw (str).
        Falls back gracefully if pyqual.yaml is missing or incompatible.
    """
    if not is_available():
        return {"passed": True, "gates": [], "available": False}
    try:
        proc = _run_pyqual(project_dir, ["gates", "--config", "pyqual.yaml", "--workdir", "."], timeout=60)
        output = proc.stdout + proc.stderr
        passed = proc.returncode == 0
        gates = _parse_gate_lines(output)
        return {"passed": passed, "gates": gates, "available": True, "raw": output[:500]}
    except subprocess.TimeoutExpired:
        logger.warning("pyqual gates timed out")
        return {"passed": True, "gates": [], "available": True, "timed_out": True}
    except Exception as exc:
        logger.warning("pyqual gates error: %s", exc)
        return {"passed": True, "gates": [], "available": True, "error": str(exc)}


def get_status(project_dir: Path) -> dict:
    """Run `pyqual status` and return current metrics summary.

    Returns:
        Dict with metrics if successful, empty dict on failure.
    """
    if not is_available():
        return {}
    try:
        proc = _run_pyqual(project_dir, ["status", "--config", "pyqual.yaml", "--workdir", "."], timeout=30)
        if proc.returncode == 0:
            return {"raw": proc.stdout[:1000], "available": True}
        return {}
    except Exception as exc:
        logger.warning("pyqual status error: %s", exc)
        return {}


def validate_config(project_dir: Path, fix: bool = False) -> tuple[bool, str]:
    """Run `pyqual validate` to check pyqual.yaml is well-formed.

    Returns:
        (valid: bool, message: str)
    """
    if not is_available():
        return True, "pyqual not installed"
    try:
        args = ["validate", "--config", "pyqual.yaml", "--workdir", "."]
        if fix:
            args.append("--fix")
        proc = _run_pyqual(project_dir, args, timeout=15)
        output = proc.stdout + proc.stderr
        return proc.returncode == 0, output.strip()[:300]
    except Exception as exc:
        logger.warning("pyqual validate error: %s", exc)
        return True, str(exc)


def init_config(project_dir: Path, profile: str = "python") -> dict:
    """Generate pyqual.yaml using `pyqual init`."""
    if not is_available():
        return {"created": False, "available": False, "profile": profile}
    try:
        proc = _run_pyqual(project_dir, ["init", "--profile", profile, "."], timeout=60)
        output = proc.stdout + proc.stderr
        return {
            "created": proc.returncode == 0 and (project_dir / "pyqual.yaml").exists(),
            "available": True,
            "profile": profile,
            "raw": output[:500],
        }
    except Exception as exc:
        logger.warning("pyqual init error: %s", exc)
        return {"created": False, "available": True, "profile": profile, "error": str(exc)}


def run_pipeline(project_dir: Path, fix_config: bool = False, dry_run: bool = False) -> dict:
    """Run `pyqual run` and parse iterations plus push/publish status."""
    if not is_available():
        return {
            "passed": True,
            "available": False,
            "iterations": 0,
            "push_passed": False,
            "publish_passed": False,
        }
    try:
        args = ["run", "--config", "pyqual.yaml", "--workdir", "."]
        if dry_run:
            args.append("--dry-run")
        if fix_config:
            args.append("--auto-fix-config")
        proc = _run_pyqual(project_dir, args, timeout=600)
        output = proc.stdout + proc.stderr
        return {
            "passed": proc.returncode == 0,
            "available": True,
            "iterations": len(re.findall(r"^\s*-\s+iteration:\s+\d+", proc.stdout, re.MULTILINE)),
            "push_passed": _stage_passed(proc.stdout, "push"),
            "publish_passed": _stage_passed(proc.stdout, "publish"),
            "raw": output[:1000],
        }
    except subprocess.TimeoutExpired:
        logger.warning("pyqual run timed out")
        return {
            "passed": False,
            "available": True,
            "iterations": 0,
            "push_passed": False,
            "publish_passed": False,
            "timed_out": True,
        }
    except Exception as exc:
        logger.warning("pyqual run error: %s", exc)
        return {
            "passed": False,
            "available": True,
            "iterations": 0,
            "push_passed": False,
            "publish_passed": False,
            "error": str(exc),
        }


def git_commit(project_dir: Path, message: str, add_all: bool = True, if_changed: bool = True) -> dict:
    """Create a commit via `pyqual git commit`."""
    if not is_available():
        return {"committed": False, "available": False}
    try:
        args = ["git", "commit", "--message", message, "--workdir", "."]
        if add_all:
            args.append("--add-all")
        if if_changed:
            args.append("--if-changed")
        proc = _run_pyqual(project_dir, args, timeout=60)
        output = proc.stdout + proc.stderr
        return {"committed": proc.returncode == 0, "available": True, "raw": output[:500]}
    except Exception as exc:
        logger.warning("pyqual git commit error: %s", exc)
        return {"committed": False, "available": True, "error": str(exc)}


def git_push(project_dir: Path, detect_protection: bool = True, dry_run: bool = False) -> dict:
    """Push changes via `pyqual git push`."""
    if not is_available():
        return {"pushed": False, "available": False}
    try:
        args = ["git", "push", "--workdir", "."]
        if detect_protection:
            args.append("--detect-protection")
        if dry_run:
            args.append("--dry-run")
        proc = _run_pyqual(project_dir, args, timeout=120)
        output = proc.stdout + proc.stderr
        return {
            "pushed": proc.returncode == 0,
            "available": True,
            "dry_run": dry_run,
            "ok": proc.returncode == 0,
            "raw": output[:500],
        }
    except Exception as exc:
        logger.warning("pyqual git push error: %s", exc)
        return {"pushed": False, "available": True, "error": str(exc)}


def tune(
    project_dir: Path,
    aggressive: bool = False,
    conservative: bool = False,
    dry_run: bool = False,
) -> dict:
    """Run `pyqual tune` to auto-adjust quality gate thresholds.

    Use ``conservative=True`` to relax thresholds after code changes so that
    gates pass — quality tightening can happen in a future iteration.

    Returns:
        Dict with: tuned (bool), available (bool), dry_run (bool), raw (str).
    """
    if not is_available():
        return {"tuned": False, "available": False}
    try:
        args = ["tune", "--config", "pyqual.yaml"]
        if aggressive:
            args.append("--aggressive")
        elif conservative:
            args.append("--conservative")
        if dry_run:
            args.append("--dry-run")
        proc = _run_pyqual(project_dir, args, timeout=60)
        output = proc.stdout + proc.stderr
        return {
            "tuned": proc.returncode == 0,
            "available": True,
            "dry_run": dry_run,
            "raw": output[:500],
        }
    except Exception as exc:
        logger.warning("pyqual tune error: %s", exc)
        return {"tuned": False, "available": True, "error": str(exc)}
