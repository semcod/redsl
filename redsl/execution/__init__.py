"""Execution helpers for the refactoring orchestrator."""

from __future__ import annotations

# Cycle orchestration
from .cycle import (
    _analyze_project,
    _new_cycle_report,
    _summarize_analysis,
    run_cycle,
    run_from_toon_content,
)

# Decision execution
from .decision import (
    _execute_decision,
    _execute_decisions,
    _execute_direct_refactor,
    _select_decisions,
)

# Resolution utilities
from .resolution import (
    _consult_memory,
    _consult_memory_for_decisions,
    _load_source_code,
    _remember_decision_result,
    _resolve_source_path,
    _resolve_target_function,
)

# Validation
from .validation import (
    _snapshot_regix_before,
    _validate_with_regix,
)

# Sandbox
from .sandbox_execution import execute_sandboxed

# Legacy executor facade (backward compatibility)
from .executor import (
    _execute_decision,
    _execute_decisions,
    _execute_direct_refactor,
    _new_cycle_report,
    _validate_with_regix,
    execute_sandboxed,
    run_cycle,
    run_from_toon_content,
)

# Reflection and reporting
from .reflector import _reflect_on_cycle
from .reporter import estimate_cycle_cost, explain_decisions, get_memory_stats

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
    # Reflection
    "_reflect_on_cycle",
    # Reporter
    "estimate_cycle_cost",
    "explain_decisions",
    "get_memory_stats",
]
