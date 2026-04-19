"""Tests for the redsl.autonomy.auto_fix module."""

from __future__ import annotations

from pathlib import Path

import pytest

# ===========================================================================
# auto_fix.py
# ===========================================================================

class TestAutoFix:
    def test_auto_fix_result_dataclass(self) -> None:
        from redsl.autonomy.auto_fix import AutoFixResult

        r = AutoFixResult()
        assert r.fixed == []
        assert r.manual_needed == []
        assert r.tickets_created == []

    def test_extract_file_path(self) -> None:
        from redsl.autonomy.auto_fix import _extract_file_path

        assert _extract_file_path("New file mymod/big.py has 500L") == "mymod/big.py"
        assert _extract_file_path("no match here") is None

    def test_extract_function_name(self) -> None:
        from redsl.autonomy.auto_fix import _extract_function_name

        assert _extract_function_name("function complex has CC=15") == "complex"
        assert _extract_function_name("no match") is None

    def test_suggest_manual_action(self) -> None:
        from redsl.autonomy.auto_fix import _suggest_manual_action

        assert "Split" in _suggest_manual_action("file exceeded 500L")
        assert "Extract" in _suggest_manual_action("has CC=20")
        assert "Review" in _suggest_manual_action("CC mean increased")
        assert "Refactor" in _suggest_manual_action("Critical count increased")
        assert "Review" in _suggest_manual_action("unknown issue")

    def test_create_fix_ticket(self) -> None:
        from redsl.autonomy.auto_fix import _create_fix_ticket

        ticket = _create_fix_ticket(Path("/tmp/proj"), "CC mean increased", "cannot auto")
        assert ticket["project"] == "proj"
        assert ticket["violation"] == "CC mean increased"
        assert ticket["auto_fix_reason"] == "cannot auto"
        assert "suggested_action" in ticket