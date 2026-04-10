"""Package discovery and filtering utilities."""

from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path
from typing import Tuple, List

# Directories to skip during package discovery
_SKIP_DIRS = frozenset({
    "venv", ".venv", ".git", "__pycache__", "node_modules", ".tox",
    "dist", "build", "logs", "2026", "project", "docs", "refactor_output",
    "shared", "pyqual-demo",
})

_PACKAGE_MARKERS = {"pyproject.toml", "setup.py", "setup.cfg"}


def _is_package(path: Path) -> bool:
    """Check if a directory is a Python package."""
    return any((path / m).exists() for m in _PACKAGE_MARKERS)


def _find_packages(workspace_root: Path) -> list[Path]:
    """Find all packages in workspace, sorted by name."""
    packages = []
    for item in sorted(workspace_root.iterdir()):
        if not item.is_dir() or item.name.startswith(".") or item.name in _SKIP_DIRS:
            continue
        if _is_package(item):
            packages.append(item)
    return packages


def _normalize_patterns(values: tuple[str, ...] | list[str] | None) -> list[str]:
    """Normalize include/exclude patterns from CLI args."""
    patterns: list[str] = []
    for value in values or ():
        for item in str(value).split(","):
            token = item.strip()
            if token:
                patterns.append(token)
    return patterns


def _matches_any(name: str, patterns: list[str]) -> bool:
    """Check if name matches any of the glob patterns."""
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def _filter_packages(
    packages: list[Path],
    include: tuple[str, ...] | list[str] | None = None,
    exclude: tuple[str, ...] | list[str] | None = None,
) -> list[Path]:
    """Filter packages by include/exclude patterns."""
    include_patterns = _normalize_patterns(include)
    exclude_patterns = _normalize_patterns(exclude)
    filtered = packages
    if include_patterns:
        filtered = [pkg for pkg in filtered if _matches_any(pkg.name, include_patterns)]
    if exclude_patterns:
        filtered = [pkg for pkg in filtered if not _matches_any(pkg.name, exclude_patterns)]
    return filtered


def _run_cmd(cmd: list[str], cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout, cwd=str(cwd),
    )


def _git_status_lines(project: Path) -> list[str]:
    """Get list of dirty files in git repo."""
    try:
        proc = _run_cmd(["git", "status", "--porcelain"], project, timeout=15)
    except Exception:
        return []
    return [line for line in proc.stdout.splitlines() if line.strip()]
