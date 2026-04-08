"""
Narzędzia pomocnicze dla analizatora kodu.
"""

from __future__ import annotations

import fnmatch
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# Default patterns to always ignore (common virtualenv/cache dirs)
DEFAULT_IGNORE_PATTERNS = {
    ".venv",
    "venv",
    ".testvenv",
    "testvenv",
    ".tox",
    "tox",
    "dist",
    "build",
    "__pycache__",
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    "*.egg-info",
    ".eggs",
    "htmlcov",
    ".coverage",
}


def _load_gitignore_patterns(project_dir: Path) -> set[str]:
    """Read .gitignore file and return set of patterns."""
    patterns = set()
    gitignore = project_dir / ".gitignore"
    if gitignore.exists():
        try:
            content = gitignore.read_text(encoding="utf-8", errors="ignore")
            for line in content.splitlines():
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                # Remove leading / if present (anchored patterns)
                if line.startswith("/"):
                    line = line[1:]
                patterns.add(line)
        except OSError:
            pass
    return patterns


def _should_ignore_file(
    file_path: Path, project_dir: Path, gitignore_patterns: set[str]
) -> bool:
    """Check if file should be ignored based on default patterns and .gitignore."""
    if _matches_default_patterns(file_path):
        return True
    if gitignore_patterns and _matches_gitignore_patterns(file_path, project_dir, gitignore_patterns):
        return True
    return False


def _matches_default_patterns(file_path: Path) -> bool:
    """Return True if any path part matches DEFAULT_IGNORE_PATTERNS."""
    for part in file_path.parts:
        if part in DEFAULT_IGNORE_PATTERNS:
            return True
        for pattern in DEFAULT_IGNORE_PATTERNS:
            if pattern.startswith("*") and fnmatch.fnmatch(part, pattern):
                return True
    return False


def _is_gitignore_glob_pattern(pattern: str) -> bool:
    return "*" in pattern or "?" in pattern or "[" in pattern


def _matches_gitignore_directory_pattern(pattern: str, rel_path: Path) -> bool:
    if not pattern.endswith("/"):
        return False
    dir_pattern = pattern.rstrip("/")
    return any(part == dir_pattern for part in rel_path.parts)


def _matches_gitignore_glob_pattern(
    pattern: str,
    rel_path: Path,
    rel_str: str,
) -> bool:
    if not _is_gitignore_glob_pattern(pattern):
        return False
    return fnmatch.fnmatch(rel_str, pattern) or fnmatch.fnmatch(rel_path.name, pattern)


def _matches_gitignore_literal_pattern(
    pattern: str,
    rel_str: str,
) -> bool:
    return pattern in rel_str.split("/") or rel_str.startswith(pattern + "/")


def _matches_gitignore_patterns(
    file_path: Path, project_dir: Path, gitignore_patterns: set[str]
) -> bool:
    """Return True if the file matches any .gitignore pattern."""
    try:
        rel_path = file_path.relative_to(project_dir)
        rel_str = str(rel_path).replace("\\", "/")
        for pattern in gitignore_patterns:
            if _matches_gitignore_directory_pattern(pattern, rel_path):
                return True
            if _matches_gitignore_glob_pattern(pattern, rel_path, rel_str):
                return True
            if _matches_gitignore_literal_pattern(pattern, rel_str):
                return True
    except ValueError:
        pass
    return False


def _try_number(val: str) -> int | float | str:
    """Spróbuj skonwertować na liczbę."""
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return val
