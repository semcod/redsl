"""Execution helpers for the refactoring orchestrator — thin facade.

Backward compatibility: All function APIs remain unchanged.
Implementation now delegates to focused submodules:
- cycle: Main cycle orchestration
- decision: Decision execution logic
- resolution: Path/source resolution
- validation: regix validation
- sandbox_execution: Sandboxed execution
"""

from __future__ import annotations

# Re-export from cycle module
from redsl.execution.cycle import (
    _analyze_project,
    _new_cycle_report,
    _summarize_analysis,
    run_cycle,
    run_from_toon_content,
)

# Re-export from decision module
from redsl.execution.decision import (
    _execute_decision,
    _execute_decisions,
    _execute_direct_refactor,
    _select_decisions,
)

# Re-export from resolution module
from redsl.execution.resolution import (
    _consult_memory,
    _consult_memory_for_decisions,
    _load_source_code,
    _remember_decision_result,
    _resolve_source_path,
    _resolve_target_function,
)

# Re-export from sandbox_execution module
from redsl.execution.sandbox_execution import execute_sandboxed

# Re-export from validation module
from redsl.execution.validation import (
    _snapshot_regix_before,
    _validate_with_regix,
)

__all__ = [
    # Cycle
    "_new_cycle_report",
    "_analyze_project",
    "_summarize_analysis",
    "run_cycle",
    "run_from_toon_content",
    # Decision
    "_select_decisions",
    "_execute_decision",
    "_execute_decisions",
    "_execute_direct_refactor",
    # Resolution
    "_resolve_source_path",
    "_resolve_target_function",
    "_load_source_code",
    "_consult_memory",
    "_consult_memory_for_decisions",
    "_remember_decision_result",
    # Validation
    "_snapshot_regix_before",
    "_validate_with_regix",
    # Sandbox
    "execute_sandboxed",
]
