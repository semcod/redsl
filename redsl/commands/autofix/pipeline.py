"""Project pipeline for autofix package."""

from __future__ import annotations

import logging
from pathlib import Path

from ...autonomy.quality_gate import run_quality_gate, _collect_python_files as _collect_python_files_impl, _measure_metrics as _measure_metrics_impl
from .models import ProjectFixResult
from .todo_gen import _generate_todo_md, _count_todo_issues, _append_gate_violations_to_todo
from .hybrid import _run_hybrid_fix

logger = logging.getLogger(__name__)


def _process_project(project: Path, max_changes: int = 30) -> ProjectFixResult:
    """Full autofix pipeline for a single project."""
    result = ProjectFixResult(name=project.name, path=str(project))

    # 1. Collect metrics
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
    except Exception as exc:
        result.errors.append(f"Metrics: {exc}")
        metrics = {"functions": [], "files": []}

    # 2. Check TODO.md
    todo_file = project / "TODO.md"
    result.had_todo = todo_file.exists()
    result.todo_issues_before = _count_todo_issues(todo_file)

    # 3. If no TODO.md or empty -> generate from scan
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

    # 4. Apply hybrid quality fixes
    if result.todo_issues_before > 0 or result.critical_count > 0:
        print(f"    Applying hybrid quality fixes (max {max_changes})...")
        applied, errors = _run_hybrid_fix(project, max_changes)
        result.hybrid_applied = applied
        result.hybrid_errors = errors
        if applied > 0:
            print(f"    Applied {applied} fixes ({errors} errors)")

    # 5. Run quality gate check (non-LLM: record violations in TODO.md)
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

    # 6. Run pyqual gates (if pyqual.yaml exists and pyqual CLI available)
    pyqual_yaml = project / "pyqual.yaml"
    if pyqual_yaml.exists():
        try:
            from ...validation.pyqual_bridge import is_available as pyqual_available, check_gates
            if pyqual_available():
                gate_result = check_gates(project)
                if gate_result.get("available"):
                    passed = gate_result.get("passed", True)
                    print(f"    pyqual gates: {'PASS' if passed else 'FAIL'}")
        except Exception as exc:
            logger.debug("pyqual bridge: %s", exc)

    # 7. Re-count TODO issues after fixes
    result.todo_issues_after = _count_todo_issues(todo_file)

    return result
