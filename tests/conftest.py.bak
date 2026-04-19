"""Shared fixtures and configuration for the test suite."""

from __future__ import annotations

import pytest
from pathlib import Path

REDSL_ROOT = Path(__file__).parent.parent / "redsl"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "slow: marks tests as slow (>5s)")
    config.addinivalue_line("markers", "integration: integration tests requiring external tools")


@pytest.fixture(scope="session")
def redsl_root() -> Path:
    return REDSL_ROOT


@pytest.fixture(scope="session")
def cached_analysis():
    """Session-scoped analysis of the redsl package — avoids re-analyzing in every test module."""
    from redsl.analyzers import CodeAnalyzer
    return CodeAnalyzer().analyze_project(REDSL_ROOT)
