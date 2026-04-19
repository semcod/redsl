"""Shared utilities for the batch_pyqual sub-package."""

from __future__ import annotations

import subprocess
from pathlib import Path

# Profile name constants used across the sub-package
AUTO_PROFILE = "auto"
DEFAULT_PROFILE = "python"
FULL_PROFILE = "python-full"
PUBLISH_PROFILE = "python-publish"


def run_cmd(cmd: list[str], cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout, cwd=str(cwd),
    )


def git_status_lines(project: Path) -> list[str]:
    """Return non-empty git status lines for *project*, or [] on error."""
    try:
        proc = run_cmd(["git", "status", "--porcelain"], project, timeout=15)
    except Exception:
        return []
    return [line for line in proc.stdout.splitlines() if line.strip()]


def resolve_profile(requested_profile: str, run_pipeline: bool, publish: bool) -> str:
    """Resolve the effective pyqual profile based on CLI options."""
    if requested_profile != AUTO_PROFILE:
        return requested_profile
    if publish:
        return PUBLISH_PROFILE
    return DEFAULT_PROFILE
