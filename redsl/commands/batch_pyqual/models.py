"""Data models for batch pyqual pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PyqualProjectResult:
    """Result of pyqual pipeline for a single project."""

    name: str
    path: str
    has_pyqual_yaml: bool = False
    pyqual_yaml_generated: bool = False
    profile_used: str = ""
    config_valid: bool = True
    config_fixed: bool = False
    config_message: str = ""
    publish_requested: bool = False
    publish_configured: bool = False

    # ReDSL analysis
    py_files: int = 0
    total_loc: int = 0
    avg_cc: float = 0.0
    max_cc: int = 0
    critical_count: int = 0
    redsl_fixes_applied: int = 0
    redsl_fixes_errors: int = 0

    # pyqual gates
    pyqual_available: bool = False
    gates_passed: bool = False
    gates_total: int = 0
    gates_passing: int = 0
    gate_details: list[dict[str, Any]] = field(default_factory=list)

    # pyqual pipeline
    pipeline_ran: bool = False
    pipeline_passed: bool = False
    pipeline_iterations: int = 0
    pipeline_push_passed: bool = False
    pipeline_publish_passed: bool = False

    # git
    git_committed: bool = False
    git_pushed: bool = False
    push_preflight_passed: bool = False
    changes_to_commit: int = 0
    dirty_before: bool = False
    dirty_after: bool = False
    dirty_entries_before: int = 0
    dirty_entries_after: int = 0
    dry_run: bool = False
    verdict: str = "unknown"
    verdict_reasons: list[str] = field(default_factory=list)

    errors: list[str] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""
