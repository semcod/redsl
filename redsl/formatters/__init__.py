"""Output formatters for reDSL.

This package provides formatting utilities for:
- Refactoring plans (text, yaml, json)
- Cycle reports (yaml, markdown)
- Batch reports (text, markdown)
- Debug information
"""

from __future__ import annotations

# Core
from .core import _get_timestamp, console

# Refactor plan formatters
from .refactor import (
    format_refactor_plan,
    _format_yaml,
    _format_json,
    _format_text,
    _serialize_analysis,
    _serialize_decision,
    _count_decision_types,
)

# Cycle report formatters
from .cycle import (
    format_cycle_report_yaml,
    format_cycle_report_markdown,
    format_plan_yaml,
    _serialize_result,
)

# Batch report formatters
from .batch import (
    format_batch_results,
    format_batch_report_markdown,
)

# Debug formatters
from .debug import format_debug_info

__all__ = [
    # Core
    "_get_timestamp",
    "console",
    # Refactor
    "format_refactor_plan",
    "_format_yaml",
    "_format_json",
    "_format_text",
    "_serialize_analysis",
    "_serialize_decision",
    "_count_decision_types",
    # Cycle
    "format_cycle_report_yaml",
    "format_cycle_report_markdown",
    "format_plan_yaml",
    "_serialize_result",
    # Batch
    "format_batch_results",
    "format_batch_report_markdown",
    # Debug
    "format_debug_info",
]
