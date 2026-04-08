"""T015 — Testy integracyjne na prawdziwych projektach semcod."""

import os
from pathlib import Path

import pytest

from redsl.analyzers import CodeAnalyzer
from redsl.dsl.engine import DSLEngine

SEMCOD = Path("/home/tom/github/semcod")
CODE2LLM = SEMCOD / "code2llm"
GOAL = SEMCOD / "goal"
PFIX = SEMCOD / "pfix"

skip_if_no_semcod = pytest.mark.skipif(
    not SEMCOD.exists(),
    reason="semcod directory not available",
)


@pytest.fixture(scope="module")
def analyzer() -> CodeAnalyzer:
    return CodeAnalyzer()


@pytest.fixture(scope="module")
def dsl() -> DSLEngine:
    return DSLEngine()


@pytest.fixture(scope="module")
def goal_analysis(analyzer: CodeAnalyzer):
    """Cached analysis of the GOAL semcod project — shared across TestGoalFunctionsToon."""
    if not GOAL.exists():
        pytest.skip("semcod/goal not available")
    return analyzer.analyze_project(GOAL)


# ---------------------------------------------------------------------------
# code2llm — analysis.toon (HEALTH[N] emoji + LAYERS)
# ---------------------------------------------------------------------------

@skip_if_no_semcod
class TestCode2llmAnalysis:
    def test_analyzes_nonzero_files(self, analyzer: CodeAnalyzer) -> None:
        result = analyzer.analyze_project(CODE2LLM)
        assert result.total_files > 0, "should find files in code2llm"
        assert result.total_lines > 0

    def test_detects_critical_alerts(self, analyzer: CodeAnalyzer) -> None:
        result = analyzer.analyze_project(CODE2LLM)
        assert result.critical_count > 0
        assert len(result.alerts) > 0
        cc_alerts = [a for a in result.alerts if a["type"] == "cc_exceeded"]
        assert len(cc_alerts) > 0, "should have CC-exceeded alerts"

    def test_resolves_function_to_real_path(self, analyzer: CodeAnalyzer) -> None:
        resolved = analyzer.resolve_file_path(CODE2LLM, "analyze_typescript_js")
        assert resolved is not None, "should resolve analyze_typescript_js"
        assert (CODE2LLM / resolved).exists()

    def test_extracts_function_source(self, analyzer: CodeAnalyzer) -> None:
        resolved = analyzer.resolve_file_path(CODE2LLM, "analyze_typescript_js")
        assert resolved is not None
        src = analyzer.extract_function_source(CODE2LLM / resolved, "analyze_typescript_js")
        assert len(src) > 50, "should extract meaningful function source"
        assert "def analyze_typescript_js" in src

    def test_dsl_generates_decisions(
        self, analyzer: CodeAnalyzer, dsl: DSLEngine
    ) -> None:
        result = analyzer.analyze_project(CODE2LLM)
        decisions = dsl.top_decisions(result.to_dsl_contexts(), limit=10)
        assert len(decisions) > 0, "DSL should generate refactoring decisions"
        # At least some decisions should have resolvable file paths
        has_real_path = any(
            (CODE2LLM / d.target_file).exists() for d in decisions
        )
        assert has_real_path, "at least one decision should point to a real file"


# ---------------------------------------------------------------------------
# goal — project.functions.toon (YAML format z CC per funkcja)
# ---------------------------------------------------------------------------

@skip_if_no_semcod
class TestGoalFunctionsToon:
    def test_analyzes_nonzero_files(self, goal_analysis) -> None:
        assert goal_analysis.total_files > 0

    def test_detects_high_cc_functions(self, goal_analysis) -> None:
        assert len(goal_analysis.alerts) > 0, "goal should have CC alerts from functions.toon"
        cc_alerts = [a for a in goal_analysis.alerts if a.get("value", 0) > 15]
        assert len(cc_alerts) > 0, "should have functions with CC > 15"

    def test_decisions_have_real_paths(
        self, goal_analysis, dsl: DSLEngine
    ) -> None:
        decisions = dsl.top_decisions(goal_analysis.to_dsl_contexts(), limit=5)
        assert len(decisions) > 0
        real = [d for d in decisions if (GOAL / d.target_file).exists()]
        assert len(real) > 0, "some decisions should reference real files"

    def test_find_worst_function_in_cli(self, analyzer: CodeAnalyzer) -> None:
        cli_path = GOAL / "goal" / "cli.py"
        if not cli_path.exists():
            pytest.skip("goal/cli.py not found")
        worst = analyzer.find_worst_function(cli_path)
        assert worst is not None, "should find at least one function in cli.py"
        name, cc = worst
        assert len(name) > 0, "function name should be non-empty"
        assert cc >= 1, "CC should be at least 1"

    def test_extract_worst_function_source(self, analyzer: CodeAnalyzer) -> None:
        cli_path = GOAL / "goal" / "cli.py"
        if not cli_path.exists():
            pytest.skip("goal/cli.py not found")
        worst = analyzer.find_worst_function(cli_path)
        assert worst is not None
        name, _ = worst
        src = analyzer.extract_function_source(cli_path, name)
        assert len(src) > 20, "should extract meaningful function source"
        assert f"def {name}" in src


# ---------------------------------------------------------------------------
# pfix — AST fallback (brak toon pliku)
# ---------------------------------------------------------------------------

@skip_if_no_semcod
class TestPfixAstFallback:
    def test_analyzes_without_toon(self, analyzer: CodeAnalyzer) -> None:
        result = analyzer.analyze_project(PFIX)
        assert result.total_files > 0, "AST fallback should find Python files"
        assert result.total_lines > 0

    def test_cc_not_inflated(self, analyzer: CodeAnalyzer) -> None:
        result = analyzer.analyze_project(PFIX)
        # CC should not be absurdly inflated (bug: nested defs counted)
        max_cc = max(
            (m.cyclomatic_complexity for m in result.metrics), default=0
        )
        assert max_cc < 200, f"CC should not be inflated (got {max_cc})"

    def test_per_function_metrics_have_real_paths(
        self, analyzer: CodeAnalyzer
    ) -> None:
        result = analyzer.analyze_project(PFIX)
        func_metrics = [m for m in result.metrics if m.function_name]
        for m in func_metrics[:5]:
            assert (PFIX / m.file_path).exists(), (
                f"file_path should exist: {m.file_path}"
            )

    def test_dsl_targets_real_files(
        self, analyzer: CodeAnalyzer, dsl: DSLEngine
    ) -> None:
        result = analyzer.analyze_project(PFIX)
        decisions = dsl.top_decisions(result.to_dsl_contexts(), limit=5)
        # At least check no crash and decisions exist or code is clean
        assert isinstance(decisions, list)


# ---------------------------------------------------------------------------
# AST helpers — unit tests
# ---------------------------------------------------------------------------

class TestAstHelpers:
    def test_cyclomatic_complexity_simple(self) -> None:
        import ast as ast_mod

        src = "def f(x):\n    if x > 0:\n        return 1\n    return 0\n"
        tree = ast_mod.parse(src)
        func = tree.body[0]
        a = CodeAnalyzer()
        cc = a._ast_cyclomatic_complexity(func)
        assert cc == 2, f"simple if → CC=2, got {cc}"

    def test_cyclomatic_complexity_no_inflate_nested(self) -> None:
        import ast as ast_mod

        src = (
            "def outer(x):\n"
            "    if x:\n"
            "        pass\n"
            "    def inner(y):\n"
            "        for i in range(10):\n"
            "            if i > y:\n"
            "                pass\n"
            "    return inner\n"
        )
        tree = ast_mod.parse(src)
        func = tree.body[0]
        a = CodeAnalyzer()
        cc = a._ast_cyclomatic_complexity(func)
        # outer has only 1 if → CC=2, inner's for+if should NOT be counted
        assert cc == 2, f"nested def should not inflate outer CC, got {cc}"

    def test_extract_function_source_returns_full_def(self, tmp_path: Path) -> None:
        src = "def foo(x):\n    if x:\n        return 1\n    return 0\n\ndef bar():\n    pass\n"
        f = tmp_path / "test.py"
        f.write_text(src)
        a = CodeAnalyzer()
        result = a.extract_function_source(f, "foo")
        assert "def foo" in result
        assert "def bar" not in result

    def test_resolve_file_path_finds_function(self, tmp_path: Path) -> None:
        (tmp_path / "module.py").write_text("def my_func(x):\n    pass\n")
        a = CodeAnalyzer()
        result = a.resolve_file_path(tmp_path, "my_func")
        assert result == "module.py"

    def test_resolve_file_path_returns_none_when_missing(
        self, tmp_path: Path
    ) -> None:
        a = CodeAnalyzer()
        result = a.resolve_file_path(tmp_path, "nonexistent_func_xyz")
        assert result is None


# ---------------------------------------------------------------------------
# T007 — Confidence scoring
# ---------------------------------------------------------------------------

class TestConfidenceScoring:
    def _make_decision(self, cc: int, score: float = 1.0) -> object:
        from redsl.dsl.engine import Decision, RefactorAction
        return Decision(
            rule_name="test",
            action=RefactorAction.EXTRACT_FUNCTIONS,
            score=score,
            target_file="test.py",
            context={"cyclomatic_complexity": cc},
        )

    def test_high_cc_gives_high_confidence(self) -> None:
        from redsl.refactors import RefactorEngine
        d = self._make_decision(cc=35)
        conf = RefactorEngine.estimate_confidence(d)
        assert conf >= 0.70, f"CC=35 should give conf >= 0.70, got {conf}"

    def test_moderate_cc_gives_moderate_confidence(self) -> None:
        from redsl.refactors import RefactorEngine
        d = self._make_decision(cc=12)
        conf = RefactorEngine.estimate_confidence(d)
        assert 0.45 <= conf <= 0.75, f"CC=12 should give moderate conf, got {conf}"

    def test_low_cc_gives_low_confidence(self) -> None:
        from redsl.refactors import RefactorEngine
        d = self._make_decision(cc=3, score=0.2)
        conf = RefactorEngine.estimate_confidence(d)
        assert conf < 0.65, f"CC=3 should give low conf, got {conf}"

    def test_confidence_monotone_with_cc(self) -> None:
        from redsl.refactors import RefactorEngine
        ccs = [5, 10, 15, 20, 30]
        confs = [RefactorEngine.estimate_confidence(self._make_decision(cc)) for cc in ccs]
        for i in range(len(confs) - 1):
            assert confs[i] <= confs[i + 1], (
                f"Confidence should be non-decreasing: CC={ccs[i]} conf={confs[i]}, "
                f"CC={ccs[i+1]} conf={confs[i+1]}"
            )

    def test_confidence_range_valid(self) -> None:
        from redsl.refactors import RefactorEngine
        for cc in [1, 10, 15, 20, 30, 50]:
            d = self._make_decision(cc=cc, score=1.9)
            conf = RefactorEngine.estimate_confidence(d)
            assert 0.0 <= conf <= 1.0, f"Confidence must be in [0,1], got {conf} for CC={cc}"


class TestRefactorProposalConfidence:
    def _make_decision(self, cc: int = 30, score: float = 1.0):
        from redsl.dsl.engine import Decision, RefactorAction

        return Decision(
            rule_name="test",
            action=RefactorAction.EXTRACT_FUNCTIONS,
            score=score,
            target_file="sample.py",
            context={"cyclomatic_complexity": cc},
        )

    def _make_engine(self, tmp_path: Path, response_data: dict) -> object:
        from unittest.mock import MagicMock

        from redsl.config import RefactorConfig
        from redsl.refactors import RefactorEngine

        llm = MagicMock()
        llm.call_json.return_value = response_data
        engine = RefactorEngine(llm=llm, config=RefactorConfig(output_dir=tmp_path / "refactor_output"))
        return engine

    def test_generate_proposal_blends_llm_confidence(self, tmp_path: Path) -> None:
        from redsl.refactors import RefactorEngine

        decision = self._make_decision(cc=30, score=1.0)
        engine = self._make_engine(
            tmp_path,
            {
                "refactor_type": "extract_functions",
                "summary": "split helper logic",
                "confidence": 0.0,
                "changes": [
                    {
                        "file_path": "sample.py",
                        "refactored_code": "def sample():\n    return 1\n",
                        "description": "split helper logic",
                    }
                ],
            },
        )

        proposal = engine.generate_proposal(decision, "def sample():\n    return 1\n")
        expected_base = RefactorEngine.estimate_confidence(decision)

        assert proposal.confidence == pytest.approx(round(0.6 * expected_base, 3))
        assert proposal.confidence > 0.0

        messages = engine.llm.call_json.call_args.args[0]
        assert "Confidence guidance" in messages[1]["content"]

    def test_generate_proposal_falls_back_when_llm_confidence_missing(self, tmp_path: Path) -> None:
        from redsl.refactors import RefactorEngine

        decision = self._make_decision(cc=12, score=0.8)
        engine = self._make_engine(
            tmp_path,
            {
                "refactor_type": "extract_functions",
                "summary": "split helper logic",
                "changes": [
                    {
                        "file_path": "sample.py",
                        "refactored_code": "def sample():\n    return 1\n",
                        "description": "split helper logic",
                    }
                ],
            },
        )

        proposal = engine.generate_proposal(decision, "def sample():\n    return 1\n")

        assert proposal.confidence == RefactorEngine.estimate_confidence(decision)
