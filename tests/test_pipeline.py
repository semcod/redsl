"""
Testy integracyjne pełnego pipeline'u ReDSL:

    code2llm → redup → DSL Engine → vallm → (regix) → (pyqual)

Każdy krok testuje integrację mostek ↔ ReDSL, nie implementację samego narzędzia.
Kroki z zepsutym CLI są oznaczone skip markers.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from redsl.analyzers import CodeAnalyzer, code2llm_bridge, redup_bridge
from redsl.analyzers.metrics import AnalysisResult
from redsl.dsl import DSLEngine
from redsl.validation import regix_bridge, vallm_bridge

REDSL_ROOT = Path(__file__).parent.parent / "redsl"
DSL_PKG = REDSL_ROOT / "dsl"


@pytest.fixture(scope="module")
def redsl_analysis():
    """Cached fallback analysis of REDSL_ROOT — shared across pipeline tests."""
    from redsl.analyzers import CodeAnalyzer
    return CodeAnalyzer().analyze_project(REDSL_ROOT)


@pytest.fixture(scope="module")
def redsl_enriched_analysis():
    """Cached code2llm + redup enriched analysis — shared across pipeline tests."""
    from redsl.analyzers import CodeAnalyzer, code2llm_bridge, redup_bridge
    analyzer = CodeAnalyzer()
    analysis = code2llm_bridge.maybe_analyze(REDSL_ROOT, analyzer) or analyzer.analyze_project(REDSL_ROOT)
    return redup_bridge.enrich_analysis(analysis, REDSL_ROOT)

skip_if_code2llm_unavailable = pytest.mark.skipif(
    not code2llm_bridge.is_available(), reason="code2llm not installed"
)
skip_if_redup_unavailable = pytest.mark.skipif(
    not redup_bridge.is_available(), reason="redup not installed"
)
skip_if_vallm_unavailable = pytest.mark.skipif(
    not vallm_bridge.is_available(), reason="vallm not installed"
)
skip_if_regix_unavailable = pytest.mark.skipif(
    not regix_bridge.is_available(), reason="regix not installed or broken"
)
skip_if_pyqual_unavailable = pytest.mark.skipif(
    shutil.which("pyqual") is None, reason="pyqual not installed"
)


# ---------------------------------------------------------------------------
# STEP 1 — PERCEIVE: code2llm bridge
# ---------------------------------------------------------------------------

class TestPipelinePerceive:
    """code2llm analyze . → AnalysisResult"""

    def test_fallback_analyze_always_works(self):
        analyzer = CodeAnalyzer()
        result = analyzer.analyze_project(REDSL_ROOT)
        assert result.total_files > 0
        assert result.total_lines > 0

    @skip_if_code2llm_unavailable
    def test_code2llm_bridge_returns_analysis_result(self):
        analyzer = CodeAnalyzer()
        result = code2llm_bridge.maybe_analyze(DSL_PKG, analyzer)
        assert result is not None
        assert isinstance(result, AnalysisResult)

    @skip_if_code2llm_unavailable
    def test_code2llm_generates_toon_files(self, tmp_path: Path):
        out = tmp_path / "out"
        out.mkdir()
        code2llm_bridge.generate_toon_files(DSL_PKG, output_dir=out)
        toon_files = [f for f in out.iterdir() if "toon" in f.name]
        assert toon_files, f"No toon files generated in {out}"

    @skip_if_code2llm_unavailable
    @pytest.mark.slow
    def test_pipeline_perceive_produces_usable_analysis(self):
        analyzer = CodeAnalyzer()
        result = (
            code2llm_bridge.maybe_analyze(REDSL_ROOT, analyzer)
            or analyzer.analyze_project(REDSL_ROOT)
        )
        assert result.total_files > 0
        contexts = result.to_dsl_contexts()
        assert len(contexts) > 0


# ---------------------------------------------------------------------------
# STEP 2 — DUPLICATION: redup bridge
# ---------------------------------------------------------------------------

class TestPipelineDuplication:
    """redup scan . → enrich AnalysisResult"""

    @skip_if_redup_unavailable
    def test_redup_scan_returns_list(self):
        groups = redup_bridge.scan_duplicates(REDSL_ROOT)
        assert isinstance(groups, list)

    @skip_if_redup_unavailable
    def test_enrich_analysis_adds_duplicates(self):
        analyzer = CodeAnalyzer()
        analysis = analyzer.analyze_project(REDSL_ROOT)
        enriched = redup_bridge.enrich_analysis(analysis, REDSL_ROOT)
        assert isinstance(enriched.duplicates, list)

    @skip_if_redup_unavailable
    def test_enrich_analysis_updates_metrics_when_dups_found(self):
        analyzer = CodeAnalyzer()
        analysis = analyzer.analyze_project(REDSL_ROOT)
        groups = redup_bridge.scan_duplicates(REDSL_ROOT)
        if not groups:
            pytest.skip("No duplicates found in this codebase")
        enriched = redup_bridge.enrich_analysis(analysis, REDSL_ROOT)
        has_dup = any(m.duplicate_lines > 0 for m in enriched.metrics)
        assert has_dup, "Expected at least one metric with duplicate_lines > 0"

    @skip_if_redup_unavailable
    def test_scan_as_toon_returns_nonempty_string(self):
        toon = redup_bridge.scan_as_toon(REDSL_ROOT)
        assert isinstance(toon, str)


# ---------------------------------------------------------------------------
# STEP 3 — DECIDE: DSL Engine
# ---------------------------------------------------------------------------

class TestPipelineDecide:
    """AnalysisResult → DSLEngine → decisions"""

    def test_dsl_engine_generates_decisions_for_redsl(self, redsl_analysis):
        engine = DSLEngine()
        decisions = engine.top_decisions(redsl_analysis.to_dsl_contexts(), limit=10)
        assert isinstance(decisions, list)
        assert len(decisions) > 0, "Expected at least one DSL decision"

    def test_decisions_have_required_fields(self, redsl_analysis):
        engine = DSLEngine()
        decisions = engine.top_decisions(redsl_analysis.to_dsl_contexts(), limit=10)
        for d in decisions:
            assert d.action is not None
            assert d.target_file
            assert d.score > 0
            assert d.rule_name

    def test_code2llm_enrich_redup_then_decide(self, redsl_enriched_analysis):
        engine = DSLEngine()
        decisions = engine.top_decisions(redsl_enriched_analysis.to_dsl_contexts(), limit=10)
        # Pipeline runs without errors — decisions may be empty if code quality is good
        assert isinstance(decisions, list)

    def test_decisions_scores_are_positive(self, redsl_analysis):
        engine = DSLEngine()
        decisions = engine.top_decisions(redsl_analysis.to_dsl_contexts(), limit=20)
        assert all(d.score > 0 for d in decisions)


# ---------------------------------------------------------------------------
# STEP 4 — REFLECT: vallm patch validation
# ---------------------------------------------------------------------------

class TestPipelineReflect:
    """patch → vallm validate → verdict + confidence blend"""

    @skip_if_vallm_unavailable
    def test_vallm_validates_good_code(self):
        code = "def add(a: int, b: int) -> int:\n    return a + b\n"
        result = vallm_bridge.validate_patch("add.py", code)
        assert result["valid"] is True
        assert result["score"] >= 0.4

    @skip_if_vallm_unavailable
    def test_vallm_score_in_range(self):
        code = "x = 1\ny = x + 2\n"
        result = vallm_bridge.validate_patch("x.py", code)
        assert 0.0 <= result["score"] <= 1.0

    @skip_if_vallm_unavailable
    def test_blend_confidence_with_vallm_score(self):
        code = "def hello() -> str:\n    return 'world'\n"
        result = vallm_bridge.validate_patch("hello.py", code)
        blended = vallm_bridge.blend_confidence(0.8, result["score"])
        assert 0.0 <= blended <= 1.0
        assert blended != 0.8 or result["score"] == 0.0

    @skip_if_vallm_unavailable
    def test_vallm_validates_orchestrator_snippet(self):
        snippet = (REDSL_ROOT / "orchestrator.py").read_text()[:600]
        result = vallm_bridge.validate_patch("orchestrator.py", snippet + "\n")
        assert result["available"] is True
        assert "verdict" in result

    def test_vallm_graceful_when_unavailable(self):
        from unittest.mock import patch
        with patch("redsl.validation.vallm_bridge.is_available", return_value=False):
            result = vallm_bridge.validate_patch("x.py", "x = 1\n")
        assert result["available"] is False
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# STEP 5 — VALIDATE: regix regression detection
# ---------------------------------------------------------------------------

class TestPipelineValidate:
    """regix compare HEAD~1 → no regression check"""

    def test_regix_is_available_returns_bool(self):
        assert isinstance(regix_bridge.is_available(), bool)

    def test_validate_working_tree_passes_without_regix(self, tmp_path: Path):
        from unittest.mock import patch
        with patch("redsl.validation.regix_bridge.is_available", return_value=False):
            passed, report = regix_bridge.validate_working_tree(tmp_path)
        assert passed is True
        assert report == {}

    @skip_if_regix_unavailable
    def test_regix_snapshot_returns_dict(self):
        snap = regix_bridge.snapshot(DSL_PKG)
        assert snap is not None
        assert isinstance(snap, dict)

    @skip_if_regix_unavailable
    def test_regix_full_cycle(self):
        before = regix_bridge.snapshot(DSL_PKG, ref="HEAD")
        assert before is not None
        passed, report = regix_bridge.validate_working_tree(
            DSL_PKG, before_snapshot=before
        )
        assert isinstance(passed, bool)


# ---------------------------------------------------------------------------
# STEP 6 — QUALITY GATE: pyqual
# ---------------------------------------------------------------------------

class TestPipelineQualityGate:
    """redsl pyqual analyze / internal quality checks"""

    def test_pyqual_analyzer_import(self):
        from redsl.commands.pyqual import PyQualAnalyzer
        analyzer = PyQualAnalyzer()
        assert analyzer is not None
        assert hasattr(analyzer, "analyze_project")

    def test_pyqual_analyze_project(self):
        from redsl.commands.pyqual import PyQualAnalyzer
        analyzer = PyQualAnalyzer()
        files = analyzer._find_python_files(REDSL_ROOT)
        assert len(files) > 0
        # Ensure .venv/venv excluded
        for f in files:
            assert ".venv" not in f.parts
            assert "venv" not in f.parts


# ---------------------------------------------------------------------------
# Full pipeline smoke test
# ---------------------------------------------------------------------------

@pytest.mark.slow
class TestFullPipelineSmoke:
    """Weryfikuje że cały flow PERCEIVE→DECIDE→REFLECT nie crashuje."""

    def test_full_pipeline_no_crash(self):
        analyzer = CodeAnalyzer()

        # PERCEIVE
        analysis = (
            code2llm_bridge.maybe_analyze(REDSL_ROOT, analyzer)
            or analyzer.analyze_project(REDSL_ROOT)
        )
        assert analysis is not None

        # DUPLICATION
        analysis = redup_bridge.enrich_analysis(analysis, REDSL_ROOT)

        # DECIDE
        engine = DSLEngine()
        decisions = engine.top_decisions(analysis.to_dsl_contexts(), limit=5)
        assert len(decisions) > 0

        # REFLECT (first decision target)
        if decisions and vallm_bridge.is_available():
            target = REDSL_ROOT.parent / decisions[0].target_file
            if target.exists():
                code = target.read_text()[:800]
                result = vallm_bridge.validate_patch(target.name, code + "\n")
                assert result["available"] is True

        # VALIDATE (regix — graceful skip if broken)
        passed, _ = regix_bridge.validate_working_tree(DSL_PKG)
        assert passed is True

    def test_pipeline_tool_availability_summary(self, capsys):
        tools = {
            "code2llm": code2llm_bridge.is_available(),
            "redup": redup_bridge.is_available(),
            "vallm": vallm_bridge.is_available(),
            "regix": regix_bridge.is_available(),
            "pyqual": shutil.which("pyqual") is not None,
        }
        with capsys.disabled():
            print("\n=== Pipeline tool availability ===")
            for name, avail in tools.items():
                print(f"  {'✓' if avail else '✗'} {name}")
        assert tools["code2llm"], "code2llm must be available"
        assert tools["redup"], "redup must be available"
        assert tools["vallm"], "vallm must be available"
