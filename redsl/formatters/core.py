"""Core utilities for formatters."""

from __future__ import annotations

from rich.console import Console

# Console for rich output (stderr)
console = Console(stderr=True)


def _get_timestamp() -> str:
    """Get current timestamp."""
    from datetime import datetime
    return datetime.now().isoformat()
