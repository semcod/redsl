"""
Walidacja refaktoryzacji — testy przed/po zmianie i wykrywanie regresji.

Moduły:
- test_runner    — uruchamianie testów i walidacja zmian
- regix_bridge   — wykrywanie regresji metryk (regix)
- vallm_bridge   — walidacja patchy przez multi-validator pipeline (vallm)
- testql_bridge  — walidacja API po refaktoryzacji (testql)
- test_generator — generowanie testów BDD/snapshot z code2logic (Tier 3C)
- sandbox        — Docker sandbox do bezpiecznego testowania zmian (Tier 3D)
"""

from __future__ import annotations

from .test_runner import TestResult, TestRunner, discover_test_command, run_tests, validate_refactor
from . import regix_bridge, vallm_bridge, test_generator, sandbox, pyqual_bridge, testql_bridge

__all__ = [
    "TestResult",
    "TestRunner",
    "discover_test_command",
    "run_tests",
    "validate_refactor",
    "regix_bridge",
    "vallm_bridge",
    "testql_bridge",
    "test_generator",
    "sandbox",
    "pyqual_bridge",
]
