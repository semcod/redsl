"""Autofix package - batch autofix pipeline for reDSL."""

from __future__ import annotations

from .models import ProjectFixResult
from .runner import run_autofix_batch

__all__ = [
    "ProjectFixResult",
    "run_autofix_batch",
    # Private exports for tests
    "_is_package",
    "_find_packages",
    "_process_project",
    "_build_summary",
    "_print_summary",
    "_save_reports",
    "_generate_todo_md",
    "_count_todo_issues",
    "_append_gate_violations_to_todo",
    "_run_hybrid_fix",
]

from .discovery import _is_package, _find_packages
from .pipeline import _process_project
from .reporting import _build_summary, _print_summary, _save_reports
from .todo_gen import _generate_todo_md, _count_todo_issues, _append_gate_violations_to_todo
from .hybrid import _run_hybrid_fix
