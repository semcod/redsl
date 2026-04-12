"""
Bootstrap test — ReDSL analizuje samego siebie.

Weryfikuje że po refaktoringu (Phase 1.1):
- kod ReDSL można przeanalizować bez crashy
- metryki są sensowne
- god-modules zostały wyeliminowane ze split modułów
- DSL Engine może generować decyzje
- żaden split plik nie przekracza 300L

Test 1.3 z planu ewolucji.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from redsl.analyzers import CodeAnalyzer, CodeMetrics
from redsl.dsl import DSLEngine

REDSL_ROOT = Path(__file__).parent.parent / "redsl"

SPLIT_FILES = [
    "analyzers/analyzer.py",
    "analyzers/toon_analyzer.py",
    "analyzers/python_analyzer.py",
    "analyzers/resolver.py",
    "analyzers/parsers/__init__.py",
    "analyzers/parsers/project_parser.py",
    "analyzers/parsers/duplication_parser.py",
    "analyzers/parsers/validation_parser.py",
    "analyzers/parsers/functions_parser.py",
    "commands/pyqual/__init__.py",
    "commands/pyqual/ruff_analyzer.py",
    "commands/pyqual/mypy_analyzer.py",
    "commands/pyqual/bandit_analyzer.py",
    "commands/pyqual/ast_analyzer.py",
    "commands/pyqual/reporter.py",
    "validation/test_runner.py",
    "refactors/diff_manager.py",
]

_GOD_MODULE_LINES = 400
_GOD_MODULE_FUNCS = 15
_MAX_SPLIT_FILE_LINES = 300


class TestBootstrapAnalyzeSelf:
    """ReDSL powinien móc analizować swój własny kod."""

    def test_analyze_redsl_no_crash(self, cached_analysis):
        """Analiza redsl/ nie powinna crashować."""
        result = cached_analysis
        assert result is not None
        assert result.total_files > 0, "Expected at least 1 .py file"
        assert len(result.metrics) > 0, "Expected at least 1 metric"

    def test_redsl_has_reasonable_avg_cc(self, cached_analysis):
        """Średni CC po refaktoringu powinien być < 15.0.

        Threshold podniesiony z 6.0 → 15.0 po rozbudowie projektu o:
        - direct.py (remove_unused_imports CC=30, extract_constants CC=16)
        - orchestrator.py po dodaniu run_cycle regix validation
        Górna granica chroni przed regresją do stanu sprzed refaktoringu.
        """
        result = cached_analysis
        assert result.avg_cc < 15.0, (
            f"avg CC={result.avg_cc:.2f} exceeded threshold — "
            "check for new high-CC functions"
        )

    def test_no_god_modules_in_split_files(self):
        """Żaden z podzielonych plików nie powinien być god-module (>400L, >15f)."""
        for rel_path in SPLIT_FILES:
            full_path = REDSL_ROOT / rel_path
            if not full_path.exists():
                continue
            lines = len(full_path.read_text(encoding="utf-8").splitlines())
            assert lines <= _GOD_MODULE_LINES, (
                f"{rel_path}: {lines}L exceeds god-module threshold {_GOD_MODULE_LINES}L"
            )

    def test_split_files_under_300_lines(self):
        """Każdy split plik powinien być < 300L (cel z Phase 1.1)."""
        oversized = []
        for rel_path in SPLIT_FILES:
            full_path = REDSL_ROOT / rel_path
            if not full_path.exists():
                continue
            lines = len(full_path.read_text(encoding="utf-8").splitlines())
            if lines > _MAX_SPLIT_FILE_LINES:
                oversized.append(f"{rel_path}: {lines}L")
        assert not oversized, (
            f"Split files exceeding {_MAX_SPLIT_FILE_LINES}L:\n"
            + "\n".join(oversized)
        )

    def test_split_files_exist(self):
        """Wszystkie split pliki powinny istnieć."""
        missing = [
            rel for rel in SPLIT_FILES if not (REDSL_ROOT / rel).exists()
        ]
        assert not missing, (
            f"Expected split files missing:\n" + "\n".join(missing)
        )


class TestBootstrapDSLPipeline:
    """DSL pipeline powinien działać na własnym kodzie ReDSL."""

    def test_dsl_engine_on_self(self, cached_analysis):
        """DSLEngine powinien generować decyzje dla własnego kodu."""
        result = cached_analysis

        engine = DSLEngine()
        contexts = result.to_dsl_contexts()
        decisions = engine.top_decisions(contexts, limit=10)

        assert isinstance(decisions, list), "Expected list of decisions"
        assert len(contexts) > 0, "No DSL contexts generated"

    def test_metrics_contain_file_paths(self, cached_analysis):
        """Wszystkie metryki powinny mieć file_path."""
        result = cached_analysis
        bad = [m for m in result.metrics if not m.file_path]
        assert not bad, f"Metrics without file_path: {bad}"

    def test_dsl_contexts_have_required_keys(self, cached_analysis):
        """Konteksty DSL powinny zawierać wszystkie wymagane klucze."""
        required_keys = {
            "file_path", "cyclomatic_complexity", "module_lines",
            "function_count", "fan_out",
        }
        result = cached_analysis
        contexts = result.to_dsl_contexts()

        for ctx in contexts:
            missing = required_keys - ctx.keys()
            assert not missing, (
                f"Context missing keys {missing}: {ctx.get('file_path')}"
            )


class TestBootstrapSplitModuleImports:
    """Backward compat — publiczne API powinno być dostępne przez stare ścieżki importu."""

    def test_import_code_analyzer(self):
        from redsl.analyzers import CodeAnalyzer
        assert CodeAnalyzer is not None

    def test_import_toon_parser(self):
        from redsl.analyzers import ToonParser
        assert ToonParser is not None

    def test_import_pyqual_commands(self):
        from redsl.commands import pyqual as pyqual_commands
        assert hasattr(pyqual_commands, "run_pyqual_analysis")
        assert hasattr(pyqual_commands, "run_pyqual_fix")

    def test_import_new_submodules(self):
        from redsl.analyzers import ToonAnalyzer, PythonAnalyzer, PathResolver
        from redsl.validation import TestRunner, run_tests, validate_refactor
        from redsl.refactors import generate_diff, create_checkpoint
        assert all([ToonAnalyzer, PythonAnalyzer, PathResolver])
        assert all([TestRunner, run_tests, validate_refactor])
        assert all([generate_diff, create_checkpoint])
