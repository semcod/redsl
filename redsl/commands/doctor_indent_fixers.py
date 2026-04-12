"""Indentation fixers for project doctor — re-exports from split modules.

This module re-exports all public fixers from ``_guard_fixers`` and ``_indent_fixers``
for backward compatibility. The implementation was split to improve maintainability index.

Main fixers:
  - ``_fix_guard_in_try_block``: Fixes guards placed inside try/except blocks
  - ``_fix_guard_with_excess_indent``: Removes bare guards and fixes over-indented bodies
  - ``_fix_stolen_indent``: Re-indents body lines that lost their proper indentation level
"""

from redsl.commands._guard_fixers import (
    _collect_guard_body,
    _fix_guard_in_try_block,
    _fix_guard_with_excess_indent,
    _handle_guard,
    _is_guard_followed_by_except,
    _next_non_blank_index,
    _process_guard_and_indent,
    _read_source,
)
from redsl.commands._indent_fixers import (
    _DEF_RE,
    _check_excess_indent,
    _fix_body_indent,
    _fix_stolen_indent,
    _handle_function_indent,
    _iterative_fix,
    _read_source as _read_source_indent,
)

