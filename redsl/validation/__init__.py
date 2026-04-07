"""
Walidacja refaktoryzacji — testy przed/po zmianie i wykrywanie regresji.

Moduły:
- test_runner   — uruchamianie testów i walidacja zmian
- regix_bridge  — wykrywanie regresji metryk (regix)
- vallm_bridge  — walidacja patchy przez multi-validator pipeline (vallm)
"""

from __future__ import annotations

from .test_runner import TestResult, TestRunner, discover_test_command, run_tests, validate_refactor
from . import regix_bridge, vallm_bridge

__all__ = [
    "TestResult",
    "TestRunner",
    "discover_test_command",
    "run_tests",
    "validate_refactor",
    "regix_bridge",
    "vallm_bridge",
]
