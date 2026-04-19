"""Shared utilities for fixer modules (doctor_* and _*_fixers)."""

from __future__ import annotations

from pathlib import Path


def _read_source(path: Path) -> str | None:
    """Read file source text, returning None on OS error."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None
