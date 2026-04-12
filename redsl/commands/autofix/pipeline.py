"""Project pipeline for autofix package."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ...autonomy.quality_gate import run_quality_gate, _collect_python_files as _collect_python_files_impl, _measure_metrics as _measure_metrics_impl
from .models import ProjectFixResult
from .todo_gen import _generate_todo_md, _count_todo_issues, _append_gate_violations_to_todo
from .hybrid import _run_hybrid_fix

logger = logging.getLogger(__name__)


def _stage_collect_metrics(project: Path, result: ProjectFixResult) -> dict[str, Any]:
    """Stage 1: Collect project metrics."""
    try:
        py_files = _collect_python_files_impl(project)
        metrics = _measure_metrics_impl(project, py_files)
        result.py_files = metrics["total_files"]
        result.total_loc = metrics["total_lines"]
        result.avg_cc = round(metrics["cc_mean"], 2)
        result.critical_count = metrics["critical"]
        if metrics.get("functions"):
            result.max_cc = max(f["cc"] for f in metrics["functions"])
            result.hotspots = [
                (f["path"], f["cc"])
                for f in sorted(metrics["functions"], key=lambda x: -x["cc"])[:5]
                if f["cc"] > 5
            ]
        return metrics
    except Exception as exc:
        result.errors.append(f"Metrics: {exc}")
        return {"functions": [], "files": []}


def _stage_ensure_todo(project: Path, result: ProjectFixResult, metrics: dict[str, Any]) -> Path:
    """Stage 2-3: Check TODO.md and generate if missing."""
    todo_file = project / "TODO.md"
    result.had_todo = todo_file.exists()
    result.todo_issues_before = _count_todo_issues(todo_file)

    if not result.had_todo or result.todo_issues_before == 0:
        print(f"    Generating TODO.md from scan findings...")
        try:
            gate_verdict = run_quality_gate(project)
            gate_violations = gate_verdict.violations
        except Exception:
            gate_violations = []

        todo_content = _generate_todo_md(project, metrics, gate_violations)
        todo_file.write_text(todo_content, encoding="utf-8")
        result.todo_generated = True
        result.todo_issues_before = _count_todo_issues(todo_file)
        print(f"    Generated TODO.md with {result.todo_issues_before} issues")

    return todo_file


def _stage_apply_fixes(project: Path, result: ProjectFixResult, max_changes: int) -> None:
    """Stage 4: Apply hybrid quality fixes."""
    if result.todo_issues_before > 0 or result.critical_count > 0:
        print(f"    Applying hybrid quality fixes (max {max_changes})...")
        applied, errors = _run_hybrid_fix(project, max_changes)
        result.hybrid_applied = applied
        result.hybrid_errors = errors
        if applied > 0:
            print(f"    Applied {applied} fixes ({errors} errors)")


def _stage_quality_gate_check(project: Path, result: ProjectFixResult, todo_file: Path) -> None:
    """Stage 5: Run quality gate check and record violations."""
    try:
        gate_verdict = run_quality_gate(project)
        result.gate_violations = len(gate_verdict.violations)
        if gate_verdict.violations:
            print(f"    Quality gate: {len(gate_verdict.violations)} violations -> appending to TODO.md")
            _append_gate_violations_to_todo(todo_file, gate_verdict.violations)
            result.gate_manual = len(gate_verdict.violations)
        else:
            print(f"    Quality gate: PASSED")
    except Exception as exc:
        result.errors.append(f"Gate: {exc}")


def _stage_pyqual_gates(project: Path) -> None:
    """Stage 6: Run pyqual gates if available."""
    pyqual_yaml = project / "pyqual.yaml"
    if not pyqual_yaml.exists():
        return
    try:
        from ...validation.pyqual_bridge import is_available as pyqual_available, check_gates
        if pyqual_available():
            gate_result = check_gates(project)
            if gate_result.get("available"):
                passed = gate_result.get("passed", True)
                print(f"    pyqual gates: {'PASS' if passed else 'FAIL'}")
    except Exception as exc:
        logger.debug("pyqual bridge: %s", exc)


def _process_project(project: Path, max_changes: int = 30) -> ProjectFixResult:
    """Full autofix pipeline for a single project."""
    result = ProjectFixResult(name=project.name, path=str(project))

    # Stage 1: Collect metrics
    metrics = _stage_collect_metrics(project, result)

    # Stage 2-3: Ensure TODO.md exists
    todo_file = _stage_ensure_todo(project, result, metrics)

    # Stage 4: Apply fixes
    _stage_apply_fixes(project, result, max_changes)

    # Stage 5: Quality gate check
    _stage_quality_gate_check(project, result, todo_file)

    # Stage 6: pyqual gates
    _stage_pyqual_gates(project)

    # Stage 7: Final count
    result.todo_issues_after = _count_todo_issues(todo_file)

    return result
