"""Batch pyqual orchestrator — multi-project quality pipeline.

For each project in a workspace:
1. Detect if pyqual.yaml exists → generate if missing
2. Run ReDSL analysis + auto-fix (DSL decisions)
3. Run pyqual gates to verify quality thresholds
4. Run pyqual pipeline (optional: fix → verify → report)
5. Git commit + push results
6. Produce aggregate Markdown report

This module bridges ReDSL's code intelligence (analyzers, DSL engine,
LLM orchestrator) with pyqual's declarative quality gates and CI/CD
automation.
"""

from __future__ import annotations

from .config_gen import _PYQUAL_YAML_TEMPLATE, _generate_pyqual_yaml, _detect_publish_configured
from .discovery import _find_packages, _filter_packages, _is_package, _normalize_patterns, _matches_any, _git_status_lines
from .models import PyqualProjectResult
from .pipeline import process_project as _process_project
from .reporting import _build_summary, _save_report, _print_summary
from .runner import run_pyqual_batch, _resolve_profile, _pyqual_cli_available
from .verdict import compute_verdict as _compute_verdict

__all__ = [
    "run_pyqual_batch",
    "PyqualProjectResult",
    # Private exports for tests
    "_find_packages",
    "_filter_packages",
    "_build_summary",
    "_compute_verdict",
    "_process_project",
    "_PYQUAL_YAML_TEMPLATE",
    "_resolve_profile",
    "_save_report",
    "_git_status_lines",
    "_print_summary",
    "_pyqual_cli_available",
]
