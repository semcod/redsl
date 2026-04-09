"""
Tier 3 integration tests — metrun, llx, code2logic, pactfix (sandbox).

All tests are offline-safe:
- metrun / code2logic / Docker unavailability → graceful fallback paths tested
- LLM never called (no API keys required)
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Tier 3A — perf_bridge
# ---------------------------------------------------------------------------


class TestPerfBridge:
    def test_import(self):
        from redsl.diagnostics import perf_bridge
        assert hasattr(perf_bridge, "PerformanceReport")
        assert hasattr(perf_bridge, "generate_optimization_report")
        assert hasattr(perf_bridge, "profile_refactor_cycle")

    def test_performance_report_dataclass(self):
        from redsl.diagnostics.perf_bridge import PerformanceReport, Bottleneck, CriticalStep
        report = PerformanceReport(
            total_time_ms=1234.5,
            bottlenecks=[Bottleneck("foo.bar", 500.0, 3, 9.2)],
            critical_path=[CriticalStep("analyze", 200.0)],
            suggestions=["cache LLM calls"],
        )
        assert report.total_time_ms == 1234.5
        assert report.bottlenecks[0].func == "foo.bar"
        assert report.critical_path[0].cumulative_ms == 200.0

    def test_parse_profile_bottlenecks_and_suggestions(self):
        from redsl.diagnostics.perf_bridge import (
            _build_fallback_suggestions,
            _parse_profile_bottlenecks,
        )

        stats_output = "3 0.003 0.001 0.500 0.000 somefunc\n"
        bottlenecks = _parse_profile_bottlenecks(stats_output)

        assert len(bottlenecks) == 1
        assert bottlenecks[0].func == "somefunc"
        assert bottlenecks[0].calls == 3

        suggestions = _build_fallback_suggestions(bottlenecks)
        assert suggestions == ["Hottest function: somefunc (500ms, 3 calls)"]

    def test_parse_metrun_output_valid_json(self):
        import json
        from redsl.diagnostics.perf_bridge import _parse_metrun_output
        data = {
            "total_time_ms": 4230.0,
            "bottlenecks": [{"func": "LLMLayer.call", "time_ms": 3100, "calls": 4, "score": 9.2}],
            "critical_path": [{"func": "analyze_project", "cumulative_ms": 200}],
            "suggestions": ["cache repeated prompts"],
        }
        report = _parse_metrun_output(json.dumps(data))
        assert report.total_time_ms == 4230.0
        assert report.bottlenecks[0].func == "LLMLayer.call"
        assert report.suggestions[0] == "cache repeated prompts"

    def test_parse_metrun_output_empty(self):
        from redsl.diagnostics.perf_bridge import _parse_metrun_output
        report = _parse_metrun_output("")
        assert report.total_time_ms == 0.0

    def test_parse_metrun_output_bad_json(self):
        from redsl.diagnostics.perf_bridge import _parse_metrun_output
        report = _parse_metrun_output("{not valid json")
        assert report.total_time_ms == 0.0

    def test_fallback_profile_runs(self, tmp_path):
        (tmp_path / "dummy.py").write_text("x = 1\n")
        from redsl.diagnostics.perf_bridge import _fallback_profile
        report = _fallback_profile(tmp_path)
        assert report.total_time_ms >= 0
        assert report.source == "cprofile-fallback"

    def test_generate_optimization_report_returns_string(self, tmp_path):
        (tmp_path / "dummy.py").write_text("x = 1\n")
        from redsl.diagnostics.perf_bridge import generate_optimization_report
        with patch("redsl.diagnostics.perf_bridge._metrun_available", return_value=False):
            result = generate_optimization_report(tmp_path)
        assert isinstance(result, str)
        assert "Total cycle time" in result

    def test_profile_refactor_cycle_fallback_when_no_metrun(self, tmp_path):
        (tmp_path / "dummy.py").write_text("x = 1\n")
        from redsl.diagnostics.perf_bridge import profile_refactor_cycle
        with patch("redsl.diagnostics.perf_bridge._metrun_available", return_value=False):
            report = profile_refactor_cycle(tmp_path)
        assert report.source == "cprofile-fallback"


# ---------------------------------------------------------------------------
# Tier 3B — llx_router
# ---------------------------------------------------------------------------


class TestLlxRouter:
    def test_import(self):
        from redsl.llm import llx_router
        assert hasattr(llx_router, "select_model")
        assert hasattr(llx_router, "select_reflection_model")
        assert hasattr(llx_router, "estimate_cycle_cost")
        assert hasattr(llx_router, "ModelSelection")

    def test_build_model_matrix_uses_sparse_and_full_specs(self):
        from redsl.llm.llx_router import _build_model_matrix

        matrix = _build_model_matrix()

        assert matrix[("extract_functions", "critical")] == "google/gemini-3.1-flash-lite-preview"
        assert matrix[("extract_functions", "high")] == "google/gemini-3.1-flash-lite-preview"
        assert matrix[("extract_functions", "any")] == "gpt-5-mini"
        assert matrix[("rename_for_clarity", "any")] == "gpt-5-mini"
        assert ("rename_for_clarity", "critical") not in matrix
        assert ("rename_for_clarity", "high") not in matrix

    def test_select_model_high_cc_returns_gemini(self):
        from redsl.llm.llx_router import select_model
        sel = select_model("extract_functions", {"cyclomatic_complexity": 35})
        assert sel.model == "google/gemini-3.1-flash-lite-preview"
        assert sel.estimated_cost >= 0

    def test_select_model_low_cc_returns_mini(self):
        from redsl.llm.llx_router import select_model
        sel = select_model("add_type_hints", {"cyclomatic_complexity": 5})
        assert sel.model == "gpt-5-mini"

    def test_select_model_critical_cc_extract(self):
        from redsl.llm.llx_router import select_model
        sel = select_model("extract_functions", {"cyclomatic_complexity": 31})
        assert sel.model == "google/gemini-3.1-flash-lite-preview"

    def test_select_model_budget_triggers_downgrade(self):
        from redsl.llm.llx_router import select_model
        sel = select_model("extract_functions", {"cyclomatic_complexity": 35}, budget_remaining=0.0001)
        assert sel.model == "ollama/llama3"

    def test_select_model_zero_budget_falls_back_to_local(self):
        from redsl.llm.llx_router import select_model
        with patch("redsl.llm.llx_router._ollama_available", return_value=True):
            sel = select_model("extract_functions", {"cyclomatic_complexity": 35}, budget_remaining=0.0)
        assert sel.model == "ollama/llama3"

    def test_apply_provider_prefix_preserves_google_model_on_openrouter(self):
        from redsl.llm.llx_router import apply_provider_prefix
        model = apply_provider_prefix(
            "google/gemini-3.1-flash-lite-preview",
            "openrouter/openai/gpt-5-mini",
        )
        assert model == "openrouter/google/gemini-3.1-flash-lite-preview"

    def test_apply_provider_prefix_prefers_configured_xai_model(self):
        from redsl.llm.llx_router import apply_provider_prefix

        model = apply_provider_prefix("gpt-5-mini", "x-ai/grok-code-fast-1")

        assert model == "xai/grok-code-fast-1"

    def test_select_reflection_model_no_ollama(self):
        from redsl.llm.llx_router import select_reflection_model
        with patch("redsl.llm.llx_router._ollama_available", return_value=False):
            model = select_reflection_model(use_local=True)
        assert model == "gpt-5-mini"

    def test_select_reflection_model_with_ollama(self):
        from redsl.llm.llx_router import select_reflection_model
        with patch("redsl.llm.llx_router._ollama_available", return_value=True):
            model = select_reflection_model(use_local=True)
        assert model == "ollama/llama3"

    def test_select_reflection_model_default(self):
        from redsl.llm.llx_router import select_reflection_model
        model = select_reflection_model(use_local=False)
        assert model == "gpt-5-mini"

    def test_estimate_cost_gpt4o(self):
        from redsl.llm.llx_router import _estimate_cost
        cost = _estimate_cost("gpt-4o", 1_000_000)
        assert cost == pytest.approx(15.0)

    def test_estimate_cost_mini(self):
        from redsl.llm.llx_router import _estimate_cost
        cost = _estimate_cost("gpt-5-mini", 1_000_000)
        assert cost == pytest.approx(0.6)

    def test_estimate_cost_gemini(self):
        from redsl.llm.llx_router import _estimate_cost
        cost = _estimate_cost("google/gemini-3.1-flash-lite-preview", 1_000_000)
        assert cost == pytest.approx(0.15)

    def test_estimate_cost_local_is_zero(self):
        from redsl.llm.llx_router import _estimate_cost
        cost = _estimate_cost("ollama/llama3", 1_000_000)
        assert cost == 0.0

    def test_model_selection_reason_contains_model(self):
        from redsl.llm.llx_router import select_model
        sel = select_model("split_module", {"module_lines": 600})
        assert sel.model in sel.reason

    def test_action_with_enum_value_attribute(self):
        from redsl.llm.llx_router import select_model
        action = MagicMock()
        action.value = "extract_functions"
        sel = select_model(action, {"cyclomatic_complexity": 35})
        assert sel.model == "google/gemini-3.1-flash-lite-preview"

    def test_llm_layer_uses_xai_key_for_xai_models(self, monkeypatch):
        from redsl.config import LLMConfig
        from redsl.llm import LLMLayer

        captured: dict[str, object] = {}

        def fake_completion(**kwargs):
            captured.update(kwargs)
            return {
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"total_tokens": 7},
            }

        monkeypatch.setenv("XAI_API_KEY", "xai-test-key")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setattr("litellm.completion", fake_completion)

        layer = LLMLayer(LLMConfig(model="x-ai/grok-code-fast-1", provider_key=""))
        response = layer.call([{"role": "user", "content": "hi"}])

        assert response.model == "xai/grok-code-fast-1"
        assert captured["model"] == "xai/grok-code-fast-1"
        assert captured["api_key"] == "xai-test-key"

    def test_call_via_llx_returns_none_when_unavailable(self):
        from redsl.llm.llx_router import call_via_llx
        with patch("redsl.llm.llx_router._llx_available", return_value=False):
            result = call_via_llx([{"role": "user", "content": "hi"}], "code-refactor")
        assert result is None


# ---------------------------------------------------------------------------
# Tier 3C — test_generator (code2logic)
# ---------------------------------------------------------------------------


class TestTestGenerator:
    def test_import(self):
        from redsl.validation import test_generator
        assert hasattr(test_generator, "generate_behavior_tests")
        assert hasattr(test_generator, "generate_snapshot_test")
        assert hasattr(test_generator, "verify_behavior_preserved")

    def _sample_file(self, tmp_path: Path) -> Path:
        p = tmp_path / "sample.py"
        p.write_text(
            "def add(a, b):\n"
            "    if a > 0:\n"
            "        return a + b\n"
            "    return b\n"
        )
        return p

    def test_ast_fallback_paths_finds_branch(self, tmp_path):
        from redsl.validation.test_generator import _ast_fallback_paths
        f = self._sample_file(tmp_path)
        paths = _ast_fallback_paths(f, "add")
        assert len(paths) >= 2

    def test_ast_fallback_paths_no_branches(self, tmp_path):
        p = tmp_path / "simple.py"
        p.write_text("def greet():\n    return 'hello'\n")
        from redsl.validation.test_generator import _ast_fallback_paths
        paths = _ast_fallback_paths(p, "greet")
        assert len(paths) >= 1

    def test_generate_behavior_tests_returns_gherkin(self, tmp_path):
        from redsl.validation.test_generator import generate_behavior_tests
        f = self._sample_file(tmp_path)
        with patch("redsl.validation.test_generator._code2logic_available", return_value=False):
            output = generate_behavior_tests(f, "add")
        assert "Feature:" in output
        assert "Scenario:" in output
        assert "add" in output

    def test_generate_snapshot_test_returns_pytest(self, tmp_path):
        from redsl.validation.test_generator import generate_snapshot_test
        f = self._sample_file(tmp_path)
        with patch("redsl.validation.test_generator._code2logic_available", return_value=False):
            output = generate_snapshot_test(f, "add")
        assert "import pytest" in output
        assert "class TestBehaviorPreserved_add" in output
        assert "def test_path_" in output

    def test_ast_fallback_dfg_extracts_params(self, tmp_path):
        from redsl.validation.test_generator import _ast_fallback_dfg
        f = self._sample_file(tmp_path)
        dfg = _ast_fallback_dfg(f, "add")
        assert "a" in dfg["inputs"]
        assert "b" in dfg["inputs"]

    def test_verify_behavior_preserved_same_file(self, tmp_path):
        from redsl.validation.test_generator import verify_behavior_preserved
        f = self._sample_file(tmp_path)
        with patch("redsl.validation.test_generator._code2logic_available", return_value=False):
            result = verify_behavior_preserved(f, f, "add")
        assert result["behavior_preserved"] is True
        assert result["inputs_match"] is True
        assert result["outputs_match"] is True

    def test_detect_behavioral_changes_reduced_paths(self):
        from redsl.validation.test_generator import _detect_behavioral_changes
        orig = {"paths": [1, 2, 3]}
        ref = {"paths": [1]}
        warnings = _detect_behavioral_changes(orig, ref)
        assert any("Reduced" in w for w in warnings)

    def test_detect_behavioral_changes_exploded_paths(self):
        from redsl.validation.test_generator import _detect_behavioral_changes
        orig = {"paths": [1, 2]}
        ref = {"paths": [1, 2, 3, 4, 5, 6, 7]}
        warnings = _detect_behavioral_changes(orig, ref)
        assert any("many" in w.lower() for w in warnings)

    def test_detect_behavioral_changes_no_change(self):
        from redsl.validation.test_generator import _detect_behavioral_changes
        orig = {"paths": [1, 2]}
        ref = {"paths": [1, 2]}
        warnings = _detect_behavioral_changes(orig, ref)
        assert warnings == []


# ---------------------------------------------------------------------------
# Tier 3D — sandbox
# ---------------------------------------------------------------------------


class TestSandbox:
    def test_import(self):
        from redsl.validation import sandbox
        assert hasattr(sandbox, "RefactorSandbox")
        assert hasattr(sandbox, "DockerNotFoundError")
        assert hasattr(sandbox, "sandbox_available")

    def test_docker_not_found_error_is_runtime_error(self):
        from redsl.validation.sandbox import DockerNotFoundError
        err = DockerNotFoundError("Docker not running")
        assert isinstance(err, RuntimeError)
        assert "Docker" in str(err)

    def test_sandbox_available_false_when_no_docker_no_pactfix(self):
        from redsl.validation.sandbox import sandbox_available
        with patch("redsl.validation.sandbox._docker_available", return_value=False), \
             patch("redsl.validation.sandbox._pactfix_available", return_value=False):
            assert sandbox_available() is False

    def test_sandbox_available_true_when_docker_present(self):
        from redsl.validation.sandbox import sandbox_available
        with patch("redsl.validation.sandbox._docker_available", return_value=True):
            assert sandbox_available() is True

    def test_sandbox_start_raises_when_no_docker(self, tmp_path):
        from redsl.validation.sandbox import RefactorSandbox, DockerNotFoundError
        sb = RefactorSandbox(tmp_path)
        with patch("redsl.validation.sandbox._docker_available", return_value=False):
            with pytest.raises(DockerNotFoundError):
                sb.start()

    def test_sandbox_apply_and_test_not_running_raises(self, tmp_path):
        from redsl.validation.sandbox import RefactorSandbox, SandboxError
        sb = RefactorSandbox(tmp_path)
        proposal = MagicMock()
        proposal.changes = []
        with pytest.raises(SandboxError):
            sb.apply_and_test(proposal)

    def test_sandbox_stop_when_not_running_noop(self, tmp_path):
        from redsl.validation.sandbox import RefactorSandbox
        sb = RefactorSandbox(tmp_path)
        sb.stop()

    def test_sandbox_context_manager_calls_stop_on_error(self, tmp_path):
        from redsl.validation.sandbox import RefactorSandbox, DockerNotFoundError
        sb = RefactorSandbox(tmp_path)
        with patch("redsl.validation.sandbox._docker_available", return_value=False):
            with pytest.raises(DockerNotFoundError):
                with sb:
                    pass

    def test_apply_and_test_no_changes_returns_error(self, tmp_path):
        from redsl.validation.sandbox import RefactorSandbox
        sb = RefactorSandbox(tmp_path)
        sb._running = True
        proposal = MagicMock()
        proposal.changes = []
        result = sb.apply_and_test(proposal)
        assert result["applied"] is False
        assert len(result["errors"]) > 0


# ---------------------------------------------------------------------------
# Orchestrator integration smoke tests
# ---------------------------------------------------------------------------


class TestOrchestratorTier3Integration:
    def test_llx_router_imported_in_orchestrator(self):
        """Verify llx_router functionality is available through orchestrator.

        The import may be in orchestrator.py or in redsl/execution/ submodule
        (executor.py, reflector.py, reporter.py) that orchestrator imports from.
        """
        from redsl.orchestrator import RefactorOrchestrator
        import inspect

        # Check orchestrator file
        src = inspect.getfile(RefactorOrchestrator)
        orchestrator_content = Path(src).read_text()

        # Check execution module files (they're in redsl/execution/)
        execution_dir = Path(src).parent / "execution"
        execution_content = ""
        if execution_dir.exists():
            for py_file in execution_dir.glob("*.py"):
                execution_content += py_file.read_text()

        # llx_router should be in orchestrator OR in execution module
        all_content = orchestrator_content + execution_content
        assert "llx_router" in all_content, \
            "llx_router import not found in orchestrator or execution module"

    def test_total_llm_cost_attribute_exists(self):
        from redsl.orchestrator import RefactorOrchestrator
        from redsl.config import AgentConfig
        orch = RefactorOrchestrator(AgentConfig())
        assert hasattr(orch, "_total_llm_cost")
        assert orch._total_llm_cost == 0.0

    def test_get_memory_stats_includes_cost(self):
        from redsl.orchestrator import RefactorOrchestrator
        from redsl.config import AgentConfig
        from redsl.execution import get_memory_stats
        orch = RefactorOrchestrator(AgentConfig())
        stats = get_memory_stats(orch)
        assert "total_llm_cost_usd" in stats

    def test_run_cycle_accepts_use_sandbox(self):
        import inspect
        from redsl.orchestrator import RefactorOrchestrator
        sig = inspect.signature(RefactorOrchestrator.run_cycle)
        assert "use_sandbox" in sig.parameters

    def test_estimate_cycle_cost_returns_list(self, tmp_path):
        (tmp_path / "dummy.py").write_text("x = 1\n")
        from redsl.orchestrator import RefactorOrchestrator
        from redsl.config import AgentConfig
        from redsl.execution import estimate_cycle_cost
        orch = RefactorOrchestrator(AgentConfig())
        items = estimate_cycle_cost(orch, tmp_path, max_actions=3)
        assert isinstance(items, list)

    def test_execute_sandboxed_method_exists(self):
        from redsl.orchestrator import RefactorOrchestrator
        assert hasattr(RefactorOrchestrator, "execute_sandboxed")


# ---------------------------------------------------------------------------
# CLI smoke tests
# ---------------------------------------------------------------------------


class TestCliTier3:
    def test_perf_command_registered(self):
        from redsl.cli import cli
        assert "perf" in [c.name for c in cli.commands.values()]

    def test_cost_command_registered(self):
        from redsl.cli import cli
        assert "cost" in [c.name for c in cli.commands.values()]

    def test_refactor_has_sandbox_option(self):
        from redsl.cli import cli
        refactor_cmd = cli.commands["refactor"]
        param_names = [p.name for p in refactor_cmd.params]
        assert "sandbox" in param_names


class TestTodoRegeneration:
    def test_hybrid_regenerate_todo_executes_backlog(self, monkeypatch, tmp_path):
        from redsl.commands.hybrid import _regenerate_todo

        captured: list[list[str]] = []

        def fake_run(args, cwd=None, capture_output=False, text=False):
            captured.append(list(args))
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")

        monkeypatch.setattr("redsl.commands.hybrid.subprocess.run", fake_run)

        _regenerate_todo(tmp_path)

        assert captured == [["prefact", "-a", "--execute-todos"]]

    def test_semcod_batch_regenerates_todo_after_refactor(self, monkeypatch, tmp_path):
        from redsl.commands import batch as batch_commands

        project = tmp_path / "demo-project"
        project.mkdir()
        todo_file = project / "TODO.md"
        todo_file.write_text("# TODO\n- [ ] fix me\n", encoding="utf-8")

        dummy_report = types.SimpleNamespace(
            decisions_count=1,
            proposals_generated=1,
            proposals_applied=1,
            proposals_rejected=0,
            errors=[],
        )

        monkeypatch.setattr(batch_commands, "apply_refactor", lambda _project, _max_actions: dummy_report)

        regenerated: list[Path] = []

        def fake_regenerate(project_path: Path) -> None:
            regenerated.append(project_path)
            (project_path / "TODO.md").write_text("# TODO\n", encoding="utf-8")

        monkeypatch.setattr(batch_commands, "_regenerate_todo", fake_regenerate)

        result = batch_commands.run_semcod_batch(tmp_path, max_actions=1)

        assert regenerated == [project]
        assert result["project_details"][0]["todo_reduction"] == 1
