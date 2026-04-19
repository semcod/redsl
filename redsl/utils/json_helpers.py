"""redsl/utils/json_helpers.py — shared JSON extraction utilities."""

from __future__ import annotations


def extract_json_block(text: str) -> str:
    """Extract first JSON block from *text*, skipping preamble lines.

    Returns the substring starting from the first line that begins with
    ``{`` or ``[``, or an empty string if none found.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            return "\n".join(lines[i:])
    return ""
