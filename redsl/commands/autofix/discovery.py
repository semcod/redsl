"""Discovery utilities for autofix package."""

from __future__ import annotations

from pathlib import Path

_SKIP_DIRS = frozenset({
    "venv", ".venv", ".git", "__pycache__", "node_modules", ".tox",
    "dist", "build", "logs", "2026", "project", "docs", "refactor_output",
    "shared", "pyqual-demo",
})


def _is_package(path: Path) -> bool:
    """Check if directory is a Python package (has pyproject.toml or setup.py)."""
    return (path / "pyproject.toml").exists() or (path / "setup.py").exists()


def _find_packages(semcod_root: Path) -> list[Path]:
    """Find all Python packages under semcod root."""
    packages: list[Path] = []
    for item in semcod_root.iterdir():
        if item.is_dir() and item.name not in _SKIP_DIRS:
            if _is_package(item):
                packages.append(item)
    return sorted(packages)
