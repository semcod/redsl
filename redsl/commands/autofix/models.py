"""Models for autofix package."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProjectFixResult:
    """Result of autofix processing for a single project."""

    name: str
    path: str
    had_todo: bool = False
    todo_generated: bool = False
    todo_issues_before: int = 0
    todo_issues_after: int = 0
    hybrid_applied: int = 0
    hybrid_errors: int = 0
    gate_violations: int = 0
    gate_fixed: int = 0
    gate_manual: int = 0
    py_files: int = 0
    total_loc: int = 0
    avg_cc: float = 0.0
    max_cc: int = 0
    critical_count: int = 0
    hotspots: list[tuple[str, int]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
