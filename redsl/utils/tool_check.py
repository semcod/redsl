"""Utilities for checking whether external CLI tools are available."""

from __future__ import annotations

import subprocess


def is_tool_available(cmd: list[str], timeout: int = 5) -> bool:
    """Return True if running *cmd* exits with code 0 within *timeout* seconds.

    Usage examples::

        is_tool_available(["metrun", "--version"])
        is_tool_available(["docker", "info"], timeout=5)
        is_tool_available(["llx", "--version"], timeout=3)
    """
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
