"""
Testy mostów ekosystemowych (Tier 1 + Tier 2):
- code2llm_bridge  — percepcja przez code2llm (generowanie toon.yaml)
- regix_bridge     — wykrywanie regresji metryk
- vallm_bridge     — walidacja wygenerowanych patchy
- redup_bridge     — wykrywanie duplikatów kodu

Struktura testów:
1. Jednostkowe (mock subprocess) — bez zewnętrznych narzędzi
2. Integracyjne (skip jeśli narzędzie niedostępne/zepsute)
3. Graceful degradation — bridge nie crashuje gdy narzędzie zawodzi
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from redsl.analyzers import CodeAnalyzer, redup_bridge
from redsl.analyzers import code2llm_bridge
from redsl.analyzers.metrics import AnalysisResult, CodeMetrics
from redsl.validation import regix_bridge, vallm_bridge

REDSL_ROOT = Path(__file__).parent.parent / "redsl"

skip_if_code2llm_unavailable = pytest.mark.skipif(
    not code2llm_bridge.is_available(),
    reason="code2llm not installed",
)
skip_if_regix_unavailable = pytest.mark.skipif(
    not regix_bridge.is_available(),
    reason="regix not installed or broken",
)
skip_if_vallm_unavailable = pytest.mark.skipif(
    not vallm_bridge.is_available(),
    reason="vallm not installed",
)
skip_if_redup_unavailable = pytest.mark.skipif(
    not redup_bridge.is_available(),
    reason="redup not installed",
)


# ---------------------------------------------------------------------------
# code2llm_bridge
# ---------------------------------------------------------------------------

class TestCode2llmBridgeUnit:
    def test_is_available_returns_bool(self):
        assert isinstance(code2llm_bridge.is_available(), bool)

    def test_read_toon_contents_empty_dir(self, tmp_path: Path):
        assert code2llm_bridge.read_toon_contents(tmp_path) == {}

    def test_read_toon_contents_finds_analysis_toon(self, tmp_path: Path):
        (tmp_path / "analysis.toon.yaml").write_text("HEALTH[0]: ok\n")
        contents = code2llm_bridge.read_toon_contents(tmp_path)
        assert "project_toon" in contents
        assert "HEALTH" in contents["project_toon"]

    def test_read_toon_contents_prefers_analysis_over_project(self, tmp_path: Path):
        (tmp_path / "analysis.toon.yaml").write_text("# analysis\n")
        (tmp_path / "project_toon.yaml").write_text("# project\n")
        contents = code2llm_bridge.read_toon_contents(tmp_path)
        assert contents["project_toon"] == "# analysis\n"

    def test_read_toon_contents_finds_duplication(self, tmp_path: Path):
        (tmp_path / "duplication.toon.yaml").write_text("duplicates: []\n")
        contents = code2llm_bridge.read_toon_contents(tmp_path)
        assert "duplication_toon" in contents

    def test_read_toon_contents_finds_validation(self, tmp_path: Path):
        (tmp_path / "validation.toon.yaml").write_text("errors: 0\n")
        contents = code2llm_bridge.read_toon_contents(tmp_path)
        assert "validation_toon" in contents

    def test_maybe_analyze_returns_none_when_unavailable(self):
        analyzer = CodeAnalyzer()
        with patch("redsl.analyzers.code2llm_bridge.is_available", return_value=False):
            result = code2llm_bridge.maybe_analyze(REDSL_ROOT, analyzer)
        assert result is None

    def test_maybe_analyze_falls_back_on_subprocess_error(self, tmp_path: Path):
        (tmp_path / "x.py").write_text("def foo(): pass\n")
        analyzer = CodeAnalyzer()
        with patch("redsl.analyzers.code2llm_bridge.is_available", return_value=True), \
             patch("subprocess.run", side_effect=FileNotFoundError("not found")):
            result = code2llm_bridge.maybe_analyze(tmp_path, analyzer)
        assert result is None

    def test_generate_toon_raises_when_unavailable(self, tmp_path: Path):
        with patch("redsl.analyzers.code2llm_bridge.is_available", return_value=False):
            with pytest.raises(RuntimeError, match="code2llm"):
                code2llm_bridge.generate_toon_files(tmp_path)

    def test_generate_toon_raises_on_nonzero_exit(self, tmp_path: Path):
        mock_proc = MagicMock(returncode=1, stderr="some error")
        with patch("redsl.analyzers.code2llm_bridge.is_available", return_value=True), \
             patch("subprocess.run", return_value=mock_proc):
            with pytest.raises(RuntimeError, match="failed"):
                code2llm_bridge.generate_toon_files(tmp_path)

    def test_analyze_falls_back_when_no_toon_files_generated(self, tmp_path: Path):
        (tmp_path / "sample.py").write_text("def foo(): pass\n")
        mock_proc = MagicMock(returncode=0, stdout="", stderr="")
        analyzer = CodeAnalyzer()
        with patch("redsl.analyzers.code2llm_bridge.is_available", return_value=True), \
             patch("subprocess.run", return_value=mock_proc):
            result = code2llm_bridge.analyze_with_code2llm(tmp_path, analyzer)
        assert result is not None
        assert isinstance(result, AnalysisResult)


@skip_if_code2llm_unavailable
class TestCode2llmBridgeIntegration:
    def test_generate_toon_files_on_redsl(self, tmp_path: Path):
        out = tmp_path / "toon_out"
        out.mkdir()
        code2llm_bridge.generate_toon_files(REDSL_ROOT / "dsl", output_dir=out)
        files = list(out.iterdir())
        assert any("toon" in f.name for f in files), f"No toon files in: {files}"

    def test_read_toon_after_generate(self, tmp_path: Path):
        out = tmp_path / "out"
        out.mkdir()
        code2llm_bridge.generate_toon_files(REDSL_ROOT / "dsl", output_dir=out)
        contents = code2llm_bridge.read_toon_contents(out)
        assert "project_toon" in contents, f"Contents: {list(contents)}"

    def test_maybe_analyze_returns_result(self):
        analyzer = CodeAnalyzer()
        result = code2llm_bridge.maybe_analyze(REDSL_ROOT / "dsl", analyzer)
        assert result is not None
        assert result.total_files > 0
        assert result.avg_cc >= 0


# ---------------------------------------------------------------------------
# regix_bridge
# ---------------------------------------------------------------------------

class TestRegixBridgeUnit:
    def test_is_available_returns_bool(self):
        assert isinstance(regix_bridge.is_available(), bool)

    def test_snapshot_returns_none_when_unavailable(self, tmp_path: Path):
        with patch("redsl.validation.regix_bridge.is_available", return_value=False):
            result = regix_bridge.snapshot(tmp_path)
        assert result is None

    def test_snapshot_returns_none_on_subprocess_error(self, tmp_path: Path):
        with patch("redsl.validation.regix_bridge.is_available", return_value=True), \
             patch("subprocess.run", side_effect=OSError("crash")):
            result = regix_bridge.snapshot(tmp_path)
        assert result is None

    def test_compare_returns_none_when_unavailable(self, tmp_path: Path):
        with patch("redsl.validation.regix_bridge.is_available", return_value=False):
            result = regix_bridge.compare(tmp_path)
        assert result is None

    def test_check_gates_returns_none_when_unavailable(self, tmp_path: Path):
        with patch("redsl.validation.regix_bridge.is_available", return_value=False):
            result = regix_bridge.check_gates(tmp_path)
        assert result is None

    def test_validate_working_tree_passes_when_unavailable(self, tmp_path: Path):
        with patch("redsl.validation.regix_bridge.is_available", return_value=False):
            passed, report = regix_bridge.validate_working_tree(tmp_path)
        assert passed is True
        assert report == {}

    def test_validate_working_tree_skips_when_no_before_snapshot(self, tmp_path: Path):
        with patch("redsl.validation.regix_bridge.is_available", return_value=True):
            passed, report = regix_bridge.validate_working_tree(tmp_path, before_snapshot=None)
        assert passed is True

    def test_snapshot_parses_json_output(self, tmp_path: Path):
        fake_json = json.dumps({"metrics": {"avg_cc": 5.0}})
        mock_proc = MagicMock(returncode=0, stdout=fake_json, stderr="")
        with patch("redsl.validation.regix_bridge.is_available", return_value=True), \
             patch("subprocess.run", return_value=mock_proc):
            result = regix_bridge.snapshot(tmp_path)
        assert result is not None
        assert result["metrics"]["avg_cc"] == 5.0


DSL_PKG = REDSL_ROOT / "dsl"


@skip_if_regix_unavailable
class TestRegixBridgeIntegration:
    def test_snapshot_on_small_pkg(self):
        snap = regix_bridge.snapshot(DSL_PKG)
        assert snap is not None
        assert isinstance(snap, dict)

    def test_check_gates_on_small_pkg(self):
        result = regix_bridge.check_gates(DSL_PKG)
        if result is not None:
            assert "passed" in result


# ---------------------------------------------------------------------------
# vallm_bridge
# ---------------------------------------------------------------------------

class TestVallmBridgeUnit:
    def test_is_available_returns_bool(self):
        assert isinstance(vallm_bridge.is_available(), bool)

    def test_extract_json_strips_preamble(self):
        text = "Detected language: python\n{\"verdict\": \"pass\", \"score\": 1.0}"
        raw = vallm_bridge._extract_json(text)
        assert raw.startswith("{")
        data = json.loads(raw)
        assert data["verdict"] == "pass"

    def test_extract_json_returns_empty_on_no_json(self):
        assert vallm_bridge._extract_json("no json here") == ""

    def test_blend_confidence_returns_base_when_score_zero(self):
        assert vallm_bridge.blend_confidence(0.8, 0.0) == 0.8

    def test_blend_confidence_weighted_blend(self):
        result = vallm_bridge.blend_confidence(1.0, 0.0)
        assert result == 1.0
        result = vallm_bridge.blend_confidence(0.0, 1.0)
        assert abs(result - 0.4) < 0.001

    def test_blend_confidence_clamps_vallm_above_1(self):
        result = vallm_bridge.blend_confidence(0.5, 2.0)
        expected = 0.6 * 0.5 + 0.4 * 1.0
        assert abs(result - expected) < 0.001

    def test_blend_confidence_clamps_vallm_below_0(self):
        result = vallm_bridge.blend_confidence(0.5, -1.0)
        assert result == 0.5

    def test_validate_patch_returns_unavailable_when_not_installed(self):
        with patch("redsl.validation.vallm_bridge.is_available", return_value=False):
            result = vallm_bridge.validate_patch("test.py", "def foo(): pass")
        assert result["available"] is False
        assert result["valid"] is True

    def test_validate_patch_handles_subprocess_error_gracefully(self):
        with patch("redsl.validation.vallm_bridge.is_available", return_value=True), \
             patch("subprocess.run", side_effect=OSError("crash")):
            result = vallm_bridge.validate_patch("test.py", "def foo(): pass")
        assert "valid" in result
        assert result["available"] is True

    def test_validate_proposal_returns_all_valid_when_unavailable(self):
        mock_proposal = MagicMock()
        mock_proposal.changes = []
        with patch("redsl.validation.vallm_bridge.is_available", return_value=False):
            result = vallm_bridge.validate_proposal(mock_proposal)
        assert result["all_valid"] is True
        assert result["available"] is False


@skip_if_vallm_unavailable
class TestVallmBridgeIntegration:
    def test_validate_simple_function(self):
        code = "def greet(name: str) -> str:\n    return f'Hello, {name}'\n"
        result = vallm_bridge.validate_patch("greet.py", code)
        assert result["available"] is True
        assert "valid" in result
        assert "score" in result
        assert 0.0 <= result["score"] <= 1.0

    def test_valid_code_passes(self):
        code = "def add(a: int, b: int) -> int:\n    return a + b\n"
        result = vallm_bridge.validate_patch("add.py", code)
        assert result["valid"] is True
        assert result["score"] >= 0.4

    def test_score_is_float_between_0_and_1(self):
        code = "x = 1\n"
        result = vallm_bridge.validate_patch("x.py", code)
        assert isinstance(result["score"], float)
        assert 0.0 <= result["score"] <= 1.0

    def test_validate_proposal_empty_changes(self):
        mock_proposal = MagicMock()
        mock_proposal.changes = []
        result = vallm_bridge.validate_proposal(mock_proposal)
        assert result["all_valid"] is True
        assert result["avg_score"] == 0.0


# ---------------------------------------------------------------------------
# redup_bridge
# ---------------------------------------------------------------------------

class TestRedupBridgeUnit:
    def test_is_available_returns_bool(self):
        assert isinstance(redup_bridge.is_available(), bool)

    def test_scan_duplicates_returns_empty_when_unavailable(self, tmp_path: Path):
        with patch("redsl.analyzers.redup_bridge.is_available", return_value=False):
            result = redup_bridge.scan_duplicates(tmp_path)
        assert result == []

    def test_scan_duplicates_returns_empty_on_nonzero_exit(self, tmp_path: Path):
        mock_proc = MagicMock(returncode=1, stdout="", stderr="error")
        with patch("redsl.analyzers.redup_bridge.is_available", return_value=True), \
             patch("subprocess.run", return_value=mock_proc):
            result = redup_bridge.scan_duplicates(tmp_path)
        assert result == []

    def test_scan_duplicates_returns_empty_on_timeout(self, tmp_path: Path):
        import subprocess
        with patch("redsl.analyzers.redup_bridge.is_available", return_value=True), \
             patch("subprocess.run", side_effect=subprocess.TimeoutExpired("redup", 60)):
            result = redup_bridge.scan_duplicates(tmp_path)
        assert result == []

    def test_scan_duplicates_parses_groups(self, tmp_path: Path):
        fake_json = json.dumps({
            "stats": {"files_scanned": 5},
            "summary": {"total_groups": 1, "total_saved_lines": 10},
            "groups": [{"similarity": 0.95, "fragments": [], "saved_lines": 10}],
            "refactor_suggestions": [],
        })
        mock_proc = MagicMock(returncode=0, stdout=fake_json, stderr="")
        with patch("redsl.analyzers.redup_bridge.is_available", return_value=True), \
             patch("subprocess.run", return_value=mock_proc):
            result = redup_bridge.scan_duplicates(tmp_path)
        assert len(result) == 1
        assert result[0]["similarity"] == 0.95

    def test_scan_as_toon_returns_empty_when_unavailable(self, tmp_path: Path):
        with patch("redsl.analyzers.redup_bridge.is_available", return_value=False):
            result = redup_bridge.scan_as_toon(tmp_path)
        assert result == ""

    def test_extract_json_helper(self):
        text = "🔍 Scanning: /tmp\n📁 Extensions: .py\n{\"groups\": []}"
        raw = redup_bridge._extract_json(text)
        assert raw.startswith("{")

    def test_strip_progress_output(self):
        text = "🔍 Scanning: /tmp\n📊 Scanned 5 files\n# redup/duplication\nDUPLICATES:\n"
        cleaned = redup_bridge._strip_progress_output(text)
        assert "🔍" not in cleaned
        assert "# redup/duplication" in cleaned

    def test_enrich_analysis_no_op_when_no_duplicates(self):
        analysis = AnalysisResult(total_files=3)
        with patch("redsl.analyzers.redup_bridge.scan_duplicates", return_value=[]):
            result = redup_bridge.enrich_analysis(analysis, Path("/tmp"))
        assert result.duplicates == []

    def test_enrich_analysis_populates_metrics(self, tmp_path: Path):
        analysis = AnalysisResult()
        analysis.metrics = [
            CodeMetrics(file_path="foo.py"),
            CodeMetrics(file_path="bar.py"),
        ]
        groups = [{
            "similarity": 0.92,
            "fragments": [
                {"file": "foo.py", "lines": 8},
                {"file": "bar.py", "lines": 8},
            ],
            "saved_lines": 8,
        }]
        with patch("redsl.analyzers.redup_bridge.scan_duplicates", return_value=groups):
            result = redup_bridge.enrich_analysis(analysis, tmp_path)
        foo = next(m for m in result.metrics if m.file_path == "foo.py")
        assert foo.duplicate_lines == 8
        assert foo.duplicate_similarity == pytest.approx(0.92)

    def test_get_refactor_suggestions_returns_empty_when_unavailable(self, tmp_path: Path):
        with patch("redsl.analyzers.redup_bridge.is_available", return_value=False):
            result = redup_bridge.get_refactor_suggestions(tmp_path)
        assert result == []


@skip_if_redup_unavailable
class TestRedupBridgeIntegration:
    def test_scan_duplicates_on_redsl(self):
        groups = redup_bridge.scan_duplicates(REDSL_ROOT)
        assert isinstance(groups, list)

    def test_scan_as_toon_on_redsl(self):
        toon = redup_bridge.scan_as_toon(REDSL_ROOT)
        assert isinstance(toon, str)

    def test_enrich_analysis_on_redsl(self):
        analyzer = CodeAnalyzer()
        analysis = analyzer.analyze_project(REDSL_ROOT)
        before_count = len(analysis.duplicates)
        enriched = redup_bridge.enrich_analysis(analysis, REDSL_ROOT)
        assert isinstance(enriched.duplicates, list)
        assert len(enriched.duplicates) >= before_count

    def test_suggestions_are_list(self):
        suggestions = redup_bridge.get_refactor_suggestions(REDSL_ROOT)
        assert isinstance(suggestions, list)

    def test_is_available_consistent(self):
        a1 = redup_bridge.is_available()
        a2 = redup_bridge.is_available()
        assert a1 == a2
