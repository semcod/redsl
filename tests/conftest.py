"""Shared fixtures for autonomy tests."""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import pytest

REDSL_ROOT = Path(__file__).parent.parent / "redsl"


@pytest.fixture(scope="session")
def cached_analysis():
    """Session-scoped analysis of the redsl package — avoids re-analyzing in every test module."""
    from redsl.analyzers import CodeAnalyzer
    return CodeAnalyzer().analyze_project(REDSL_ROOT)


@pytest.fixture
def tmp_git_project(tmp_path: Path) -> Path:
    """Create a minimal git-initialized Python project."""
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), capture_output=True)

    # Create a simple Python file
    pkg = tmp_path / "mymod"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "core.py").write_text(textwrap.dedent("""\
        def hello():
            return "world"

        def add(a, b):
            return a + b
    """))

    # Initial commit
    subprocess.run(["git", "add", "-A"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=str(tmp_path), capture_output=True, check=True)
    return tmp_path
