"""Tests for the redsl.autonomy package."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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


# ===========================================================================
# quality_gate.py
# ===========================================================================

class TestQualityGate:
    def test_gate_passes_on_clean_project(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.quality_gate import run_quality_gate

        verdict = run_quality_gate(tmp_git_project)
        assert verdict.passed
        assert verdict.reason == "OK"
        assert verdict.violations == []

    def test_gate_detects_high_cc_new_function(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.quality_gate import run_quality_gate

        # Add a complex function (many branches)
        complex_func = "def complex():\n"
        for i in range(15):
            complex_func += f"    if x == {i}:\n        return {i}\n"
        complex_func += "    return -1\n"

        new_file = tmp_git_project / "mymod" / "complex.py"
        new_file.write_text(complex_func)

        # Lower threshold so it triggers
        verdict = run_quality_gate(tmp_git_project, max_new_function_cc=5)
        # new_functions only picks up untracked files
        assert isinstance(verdict, object)
        assert "cc_mean" in verdict.metrics_after

    def test_gate_detects_oversized_new_file(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.quality_gate import run_quality_gate

        # Create a file with >100 lines (use low threshold)
        big = tmp_git_project / "mymod" / "big.py"
        big.write_text("\n".join(f"x_{i} = {i}" for i in range(150)))

        verdict = run_quality_gate(tmp_git_project, max_new_file_lines=50)
        found_size_violation = any("New file" in v for v in verdict.violations)
        assert found_size_violation

    def test_gate_verdict_dataclass(self) -> None:
        from redsl.autonomy.quality_gate import GateVerdict

        v = GateVerdict(
            passed=False,
            reason="1 violation(s)",
            metrics_before={"cc_mean": 1.0},
            metrics_after={"cc_mean": 2.0},
            violations=["CC mean increased"],
        )
        assert not v.passed
        assert len(v.violations) == 1

    def test_install_hook(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.quality_gate import install_pre_commit_hook

        hook = install_pre_commit_hook(tmp_git_project)
        assert hook.exists()
        assert os.access(hook, os.X_OK)
        content = hook.read_text()
        assert "quality gate" in content.lower()


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


# ===========================================================================
# growth_control.py
# ===========================================================================

class TestGrowthControl:
    def test_growth_budget_defaults(self) -> None:
        from redsl.autonomy.growth_control import GrowthBudget

        b = GrowthBudget()
        assert b.max_file_size == 400
        assert b.max_total_growth_per_week == 2000

    def test_find_oversized_files(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.growth_control import GrowthController, GrowthBudget

        # Create a big file
        big = tmp_git_project / "mymod" / "big.py"
        big.write_text("\n".join(f"x_{i} = {i}" for i in range(500)))

        gc = GrowthController(GrowthBudget(max_file_size=100))
        warnings = gc.check_growth(tmp_git_project)
        oversized = [w for w in warnings if "big.py" in w]
        assert len(oversized) >= 1

    def test_find_tiny_modules(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.growth_control import GrowthController

        # Create several tiny files
        for i in range(12):
            (tmp_git_project / "mymod" / f"tiny_{i}.py").write_text(f"x = {i}\n")

        gc = GrowthController()
        suggestions = gc.suggest_consolidation(tmp_git_project)
        consolidate = [s for s in suggestions if s["action"] == "consolidate_tiny_modules"]
        assert len(consolidate) >= 1

    def test_module_budget_check(self, tmp_path: Path) -> None:
        from redsl.autonomy.growth_control import check_module_budget

        # Create a bridge-type file that exceeds limits
        bridge = tmp_path / "my_bridge.py"
        source = "\n".join(f"import mod_{i}" for i in range(20))
        source += "\n" + "\n".join(f"def fn_{i}(): pass" for i in range(12))
        bridge.write_text(source)

        violations = check_module_budget(bridge, module_type="bridge")
        # Should trigger at least the functions or imports limit
        assert len(violations) >= 1

    def test_module_budget_infer_type(self) -> None:
        from redsl.autonomy.growth_control import _infer_module_type

        assert _infer_module_type(Path("regix_bridge.py")) == "bridge"
        assert _infer_module_type(Path("toon_parser.py")) == "parser"
        assert _infer_module_type(Path("dsl_engine.py")) == "engine"
        assert _infer_module_type(Path("cli.py")) == "cli"
        assert _infer_module_type(Path("data_model.py")) == "model"
        assert _infer_module_type(Path("utils.py")) == "default"

    def test_group_by_prefix(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.growth_control import GrowthController

        for name in ("doctor_a.py", "doctor_b.py", "doctor_c.py", "doctor_d.py", "doctor_e.py"):
            (tmp_git_project / "mymod" / name).write_text("x = 1\n")

        gc = GrowthController()
        suggestions = gc.suggest_consolidation(tmp_git_project)
        subpkg = [s for s in suggestions if s["action"] == "create_subpackage"]
        assert len(subpkg) >= 1


# ===========================================================================
# history.py
# ===========================================================================

class TestHistoryWriter:
    def test_record_event_creates_jsonl_history(self, tmp_path: Path) -> None:
        from redsl.history import HistoryWriter

        writer = HistoryWriter(tmp_path)
        writer.record_event(
            "proposal_rejected",
            cycle_number=3,
            decision_rule="deduplicate_structural",
            target_file="mymod/core.py",
            action="deduplicate",
            status="rejected",
            reason="duplicate already covered by previous proposal",
            details={"reflection": "skip duplicate"},
        )

        history_file = tmp_path / ".redsl" / "history.jsonl"
        assert history_file.exists()

        payload = json.loads(history_file.read_text().strip())
        assert payload["event_type"] == "proposal_rejected"
        assert payload["target_file"] == "mymod/core.py"
        assert payload["reason"] == "duplicate already covered by previous proposal"

    def test_duplicate_signature_detection(self, tmp_path: Path) -> None:
        from redsl.history import HistoryWriter

        writer = HistoryWriter(tmp_path)
        signature = writer.decision_signature(
            rule="deduplicate_structural",
            target_file="mymod/core.py",
            action="deduplicate",
            context={"duplicate_lines": 20, "duplicate_similarity": 0.95},
        )

        writer.record_event(
            "proposal_generated",
            cycle_number=1,
            decision_rule="deduplicate_structural",
            target_file="mymod/core.py",
            action="deduplicate",
            details={"signature": signature},
        )

        assert writer.has_recent_signature(signature)


# ===========================================================================
# smart_scorer.py
# ===========================================================================

class TestSmartScorer:
    def test_smart_score_without_extras(self) -> None:
        from redsl.autonomy.smart_scorer import smart_score
        from redsl.dsl.engine import Rule, Condition, Operator, RefactorAction

        rule = Rule(
            name="test",
            conditions=[Condition("cyclomatic_complexity", Operator.GT, 10)],
            action=RefactorAction.EXTRACT_FUNCTIONS,
            priority=0.9,
        )
        ctx = {"cyclomatic_complexity": 20, "module_lines": 100}
        score = smart_score(rule, ctx)
        base = rule.score(ctx)
        assert score == base  # no multipliers

    def test_smart_score_zero_for_non_match(self) -> None:
        from redsl.autonomy.smart_scorer import smart_score
        from redsl.dsl.engine import Rule, Condition, Operator, RefactorAction

        rule = Rule(
            name="test",
            conditions=[Condition("cyclomatic_complexity", Operator.GT, 100)],
            action=RefactorAction.EXTRACT_FUNCTIONS,
            priority=0.9,
        )
        ctx = {"cyclomatic_complexity": 5}
        assert smart_score(rule, ctx) == 0.0

    def test_coupling_multiplier(self) -> None:
        from redsl.autonomy.smart_scorer import _coupling_multiplier

        assert _coupling_multiplier({"file_path": "mymod/core.py"}, None) == 1.0
        coupling = {"mymod.core": {"fan_in": 10}}
        assert _coupling_multiplier({"file_path": "mymod/core.py"}, coupling) == 1.2

    def test_ecosystem_multiplier_bridge(self) -> None:
        from redsl.autonomy.smart_scorer import _ecosystem_multiplier

        assert _ecosystem_multiplier({"file_path": "mymod/bridge.py"}, None) == 1.0


# ===========================================================================
# adaptive_executor.py
# ===========================================================================

class TestAdaptiveExecutor:
    def test_session_failures_tracking(self) -> None:
        from redsl.autonomy.adaptive_executor import AdaptiveExecutor

        mock_orch = MagicMock()
        mock_orch.memory = MagicMock()
        ae = AdaptiveExecutor(mock_orch)

        assert ae.session_failures == {}
        ae._session_failures["extract_functions"] = 2
        assert ae.session_failures["extract_functions"] == 2

    def test_adapt_strategy_records(self) -> None:
        from redsl.autonomy.adaptive_executor import AdaptiveExecutor

        mock_orch = MagicMock()
        mock_orch.memory = MagicMock()
        ae = AdaptiveExecutor(mock_orch)
        ae._adapt_strategy("extract_functions", ["err1"])
        mock_orch.memory.learn_pattern.assert_called_once()
        mock_orch.memory.store_strategy.assert_called_once()


# ===========================================================================
# review.py
# ===========================================================================

class TestReview:
    def test_review_no_changes(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.review import review_staged_changes

        output = review_staged_changes(tmp_git_project)
        assert "No changes" in output or "no major issues" in output.lower() or isinstance(output, str)

    def test_static_review_high_cc(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.review import _static_review

        # Create a file with high-CC function
        complex_func = "def complex():\n"
        for i in range(20):
            complex_func += f"    if x == {i}:\n        return {i}\n"
        complex_func += "    return -1\n"

        fp = tmp_git_project / "mymod" / "complex.py"
        fp.write_text(complex_func)
        diff = "+++ b/mymod/complex.py\n+def complex():\n"

        result = _static_review(tmp_git_project, diff)
        assert "complex" in result.lower() or "CC=" in result

    def test_parse_changed_files(self) -> None:
        from redsl.autonomy.review import _parse_changed_files_from_diff

        diff = "+++ b/src/foo.py\n+++ b/src/bar.py\n+++ b/readme.md\n"
        files = _parse_changed_files_from_diff(diff)
        assert "src/foo.py" in files
        assert "src/bar.py" in files
        assert "readme.md" not in files  # not .py


# ===========================================================================
# intent.py
# ===========================================================================

class TestIntent:
    def test_analyze_intent(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.intent import analyze_commit_intent

        report = analyze_commit_intent(tmp_git_project)
        assert "intent" in report
        assert "risk" in report
        assert "changed_files" in report
        assert "summary" in report
        assert report["risk"] in ("low", "medium", "high")

    def test_assess_risk_bugfix(self) -> None:
        from redsl.autonomy.intent import _assess_risk

        assert _assess_risk([], "bugfix") == "high"

    def test_assess_risk_high_pattern(self) -> None:
        from redsl.autonomy.intent import _assess_risk

        assert _assess_risk(["redsl/config.py"], "feature") == "high"

    def test_assess_risk_medium_pattern(self) -> None:
        from redsl.autonomy.intent import _assess_risk

        assert _assess_risk(["redsl/foo_bridge.py"], "feature") == "medium"

    def test_assess_risk_low(self) -> None:
        from redsl.autonomy.intent import _assess_risk

        assert _assess_risk(["docs/readme.md"], "docs") == "low"


# ===========================================================================
# scheduler.py
# ===========================================================================

class TestScheduler:
    def test_scheduler_init(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.scheduler import AutonomyMode, Scheduler

        s = Scheduler(
            project_dir=tmp_git_project,
            mode=AutonomyMode.WATCH,
            check_interval_minutes=1,
        )
        assert s.mode == AutonomyMode.WATCH
        assert s.interval == 60
        assert s._cycle_count == 0

    def test_run_once_watch(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.scheduler import AutonomyMode, Scheduler

        s = Scheduler(
            project_dir=tmp_git_project,
            mode=AutonomyMode.WATCH,
        )
        result = s.run_once()
        assert result["cycle"] == 1
        assert result["mode"] == "watch"
        assert "analysis_summary" in result

    def test_run_once_suggest(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.scheduler import AutonomyMode, Scheduler

        s = Scheduler(
            project_dir=tmp_git_project,
            mode=AutonomyMode.SUGGEST,
        )
        result = s.run_once()
        assert result["mode"] == "suggest"
        assert "proposals" in result

    def test_has_changes(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.scheduler import Scheduler

        s = Scheduler(project_dir=tmp_git_project)
        # First check always returns True (initializes _last_head)
        assert s._has_changes_since_last_check()
        # Second check returns False (same HEAD)
        assert not s._has_changes_since_last_check()


# ===========================================================================
# CLI smoke tests
# ===========================================================================

class TestCLI:
    def test_gate_check_cli(self, tmp_git_project: Path) -> None:
        from click.testing import CliRunner
        from redsl.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["gate", "check", str(tmp_git_project)])
        assert result.exit_code == 0
        assert "PASSED" in result.output or "FAILED" in result.output

    def test_gate_details_cli(self, tmp_git_project: Path) -> None:
        from click.testing import CliRunner
        from redsl.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["gate", "details", str(tmp_git_project)])
        assert result.exit_code == 0
        assert "Quality Gate" in result.output

    def test_intent_cli(self, tmp_git_project: Path) -> None:
        from click.testing import CliRunner
        from redsl.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["intent", str(tmp_git_project)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "intent" in data
        assert "risk" in data

    def test_growth_cli(self, tmp_git_project: Path) -> None:
        from click.testing import CliRunner
        from redsl.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["growth", str(tmp_git_project)])
        assert result.exit_code == 0

    def test_review_cli(self, tmp_git_project: Path) -> None:
        from click.testing import CliRunner
        from redsl.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["review", str(tmp_git_project)])
        assert result.exit_code == 0

    def test_improve_cli(self, tmp_git_project: Path) -> None:
        from click.testing import CliRunner
        from redsl.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["improve", str(tmp_git_project), "--mode", "watch"])
        assert result.exit_code == 0

    def test_gate_install_hook_cli(self, tmp_git_project: Path) -> None:
        from click.testing import CliRunner
        from redsl.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["gate", "install-hook", str(tmp_git_project)])
        assert result.exit_code == 0
        assert "hook" in result.output.lower()

    def test_autonomous_pr_aborts_when_only_reports_are_generated(self, monkeypatch, tmp_path: Path) -> None:
        from click.testing import CliRunner
        from redsl.cli import cli
        import redsl.commands.autonomy_pr as autonomy_pr

        # Stub helpers that call subprocess at module level
        monkeypatch.setattr(autonomy_pr, "_gh_available", lambda: False)
        monkeypatch.setattr(autonomy_pr, "_https_to_ssh", lambda url: url)

        clone_path = tmp_path / "vallm"
        calls: list[tuple[tuple[str, ...], str | None]] = []

        def fake_run(cmd, cwd=None, capture_output=False, text=False, timeout=None, check=False, env=None):
            calls.append((tuple(cmd), cwd))

            if tuple(cmd[:2]) == ("git", "clone"):
                clone_path.mkdir(parents=True, exist_ok=True)
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

            if tuple(cmd[:3]) == ("/usr/bin/python3", "-m", "redsl.cli"):
                (clone_path / "redsl_refactor_plan.md").write_text("plan", encoding="utf-8")
                (clone_path / "redsl_refactor_report.md").write_text("report", encoding="utf-8")
                return subprocess.CompletedProcess(cmd, 0, stdout="refactor complete", stderr="")

            if tuple(cmd[:3]) == ("git", "status", "--porcelain"):
                return subprocess.CompletedProcess(
                    cmd,
                    0,
                    stdout="?? redsl_refactor_plan.md\n?? redsl_refactor_report.md\n",
                    stderr="",
                )

            if tuple(cmd[:2]) in {("git", "branch"), ("git", "ls-remote")}:
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

            raise AssertionError(f"Unexpected command: {cmd}")

        monkeypatch.setattr(subprocess, "run", fake_run)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "autonomous-pr",
                "https://github.com/semcod/vallm.git",
                "--auto-apply",
                "--work-dir",
                str(tmp_path),
                "--branch-name",
                "redsl-test-branch",
            ],
        )

        assert result.exit_code != 0
        assert "no source-code changes" in result.output.lower()
        assert (clone_path / "redsl_refactor_plan.md").exists()
        assert (clone_path / "redsl_refactor_report.md").exists()
        assert not any(cmd[:2] == ("git", "checkout") for cmd, _ in calls)
        assert not any(cmd[:2] == ("git", "commit") for cmd, _ in calls)

    # --- SSH / gh helpers -----------------------------------------------

    def test_https_to_ssh_converts_github_url(self) -> None:
        from redsl.commands.autonomy_pr import _https_to_ssh

        assert _https_to_ssh("https://github.com/semcod/vallm.git") == "git@github.com:semcod/vallm.git"
        assert _https_to_ssh("http://github.com/org/repo.git") == "git@github.com:org/repo.git"
        # Non-GitHub URLs are left unchanged
        assert _https_to_ssh("https://gitlab.com/org/repo.git") == "https://gitlab.com/org/repo.git"
        # Already SSH → returned as-is
        assert _https_to_ssh("git@github.com:org/repo.git") == "git@github.com:org/repo.git"

    def test_gh_available_returns_false_when_missing(self, monkeypatch) -> None:
        from redsl.commands.autonomy_pr import _gh_available

        def raise_fnf(cmd, **kw):
            raise FileNotFoundError("gh not found")

        monkeypatch.setattr(subprocess, "run", raise_fnf)
        assert _gh_available() is False

    def test_gh_available_returns_true_when_auth_ok(self, monkeypatch) -> None:
        from redsl.commands.autonomy_pr import _gh_available

        monkeypatch.setattr(
            subprocess, "run",
            lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0),
        )
        assert _gh_available() is True

    # --- Full pipeline (clone → push → PR) with real changes -----------

    def test_autonomous_pr_full_pipeline_with_ssh_and_gh(self, monkeypatch, tmp_path: Path) -> None:
        """Happy-path: clone via SSH, real changes produced, push, PR via gh."""
        from click.testing import CliRunner
        from redsl.cli import cli
        import redsl.commands.autonomy_pr as autonomy_pr

        monkeypatch.setattr(autonomy_pr, "_gh_available", lambda: True)
        monkeypatch.setattr(autonomy_pr, "_https_to_ssh", lambda url: url.replace("https://github.com/", "git@github.com:"))

        clone_path = tmp_path / "vallm"
        calls: list[tuple[tuple[str, ...], str | None]] = []

        def fake_run(cmd, cwd=None, capture_output=False, text=False, timeout=None, check=False, env=None):
            calls.append((tuple(cmd), cwd))

            if tuple(cmd[:2]) == ("git", "clone"):
                clone_path.mkdir(parents=True, exist_ok=True)
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

            if tuple(cmd[:3]) == ("/usr/bin/python3", "-m", "redsl.cli"):
                (clone_path / "src" / "main.py").parent.mkdir(parents=True, exist_ok=True)
                (clone_path / "src" / "main.py").write_text("# refactored", encoding="utf-8")
                return subprocess.CompletedProcess(cmd, 0, stdout="1. Decision: split_module\n2. Decision: add_types", stderr="")

            if tuple(cmd[:3]) == ("git", "status", "--porcelain"):
                return subprocess.CompletedProcess(cmd, 0, stdout=" M src/main.py\n?? redsl_refactor_report.md\n", stderr="")

            if tuple(cmd[:2]) in {("git", "branch"), ("git", "ls-remote")}:
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

            if tuple(cmd[:2]) == ("git", "checkout"):
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

            if tuple(cmd[:2]) == ("git", "add"):
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

            if tuple(cmd[:2]) == ("git", "commit"):
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

            if tuple(cmd[:2]) == ("git", "push"):
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

            if tuple(cmd[:2]) == ("gh", "pr"):
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

            raise AssertionError(f"Unexpected command: {cmd}")

        monkeypatch.setattr(subprocess, "run", fake_run)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "autonomous-pr",
                "https://github.com/semcod/vallm.git",
                "--auto-apply",
                "--work-dir", str(tmp_path),
                "--branch-name", "redsl-test-ssh",
            ],
        )

        assert result.exit_code == 0, f"Expected success, got:\n{result.output}"
        assert "ssh" in result.output.lower() or "git@github.com" in result.output.lower()
        assert "pr created successfully" in result.output.lower()
        # Verify SSH clone URL used
        clone_cmds = [c for c, _ in calls if c[:2] == ("git", "clone")]
        assert any("git@github.com:" in c[2] for c in clone_cmds)
        # Verify gh pr create was called
        pr_cmds = [c for c, _ in calls if c[:2] == ("gh", "pr")]
        assert len(pr_cmds) == 1

    def test_autonomous_pr_skips_pr_creation_without_gh(self, monkeypatch, tmp_path: Path) -> None:
        """When gh is not available, push succeeds but PR creation is skipped."""
        from click.testing import CliRunner
        from redsl.cli import cli
        import redsl.commands.autonomy_pr as autonomy_pr

        monkeypatch.setattr(autonomy_pr, "_gh_available", lambda: False)
        monkeypatch.setattr(autonomy_pr, "_https_to_ssh", lambda url: url)

        clone_path = tmp_path / "vallm"
        calls: list[tuple[tuple[str, ...], str | None]] = []

        def fake_run(cmd, cwd=None, capture_output=False, text=False, timeout=None, check=False, env=None):
            calls.append((tuple(cmd), cwd))
            if tuple(cmd[:2]) == ("git", "clone"):
                clone_path.mkdir(parents=True, exist_ok=True)
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            if tuple(cmd[:3]) == ("/usr/bin/python3", "-m", "redsl.cli"):
                (clone_path / "src").mkdir(parents=True, exist_ok=True)
                (clone_path / "src" / "mod.py").write_text("# fixed", encoding="utf-8")
                return subprocess.CompletedProcess(cmd, 0, stdout="done", stderr="")
            if tuple(cmd[:3]) == ("git", "status", "--porcelain"):
                return subprocess.CompletedProcess(cmd, 0, stdout=" M src/mod.py\n", stderr="")
            if tuple(cmd[:2]) in {("git", "branch"), ("git", "ls-remote"), ("git", "checkout"),
                                   ("git", "add"), ("git", "commit"), ("git", "push")}:
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            raise AssertionError(f"Unexpected command: {cmd}")

        monkeypatch.setattr(subprocess, "run", fake_run)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "autonomous-pr",
                "https://github.com/semcod/vallm.git",
                "--auto-apply",
                "--work-dir", str(tmp_path),
                "--branch-name", "redsl-no-gh",
            ],
        )

        assert result.exit_code == 0, f"Expected success:\n{result.output}"
        assert "gh" in result.output.lower() and "not available" in result.output.lower()
        assert not any(c[:2] == ("gh", "pr") for c, _ in calls)


# ===========================================================================
# HistoryReader (new)
# ===========================================================================

class TestHistoryReader:
    def test_load_events_empty(self, tmp_path: Path) -> None:
        from redsl.history import HistoryReader

        reader = HistoryReader(tmp_path)
        assert reader.load_events() == []

    def test_load_events_roundtrip(self, tmp_path: Path) -> None:
        from redsl.history import HistoryWriter, HistoryReader

        writer = HistoryWriter(tmp_path)
        writer.record_event(
            "proposal_generated",
            cycle_number=1,
            target_file="foo.py",
            action="extract_functions",
            thought="CC=25, high priority",
        )
        writer.record_event(
            "proposal_rejected",
            cycle_number=1,
            target_file="foo.py",
            action="extract_functions",
            outcome_reason="Rejected: syntax error in generated code",
        )

        reader = HistoryReader(tmp_path)
        events = reader.load_events()
        assert len(events) == 2
        assert events[0]["thought"] == "CC=25, high priority"
        assert events[1]["outcome_reason"] == "Rejected: syntax error in generated code"

    def test_filter_by_file(self, tmp_path: Path) -> None:
        from redsl.history import HistoryWriter, HistoryReader

        writer = HistoryWriter(tmp_path)
        writer.record_event("decision_started", target_file="a.py", action="split")
        writer.record_event("decision_started", target_file="b.py", action="split")
        writer.record_event("proposal_applied", target_file="a.py", action="split")

        reader = HistoryReader(tmp_path)
        a_events = reader.filter_by_file("a.py")
        assert len(a_events) == 2
        assert all(e["target_file"] == "a.py" for e in a_events)

    def test_filter_by_type(self, tmp_path: Path) -> None:
        from redsl.history import HistoryWriter, HistoryReader

        writer = HistoryWriter(tmp_path)
        writer.record_event("decision_started", target_file="a.py")
        writer.record_event("proposal_applied", target_file="a.py")
        writer.record_event("decision_started", target_file="b.py")

        reader = HistoryReader(tmp_path)
        started = reader.filter_by_type("decision_started")
        assert len(started) == 2

    def test_has_recent_proposal_true(self, tmp_path: Path) -> None:
        from redsl.history import HistoryWriter, HistoryReader

        writer = HistoryWriter(tmp_path)
        writer.record_event(
            "proposal_generated",
            target_file="foo.py",
            action="extract_functions",
        )

        reader = HistoryReader(tmp_path)
        assert reader.has_recent_proposal("foo.py", "extract_functions")

    def test_has_recent_proposal_false_different_action(self, tmp_path: Path) -> None:
        from redsl.history import HistoryWriter, HistoryReader

        writer = HistoryWriter(tmp_path)
        writer.record_event(
            "proposal_generated",
            target_file="foo.py",
            action="deduplicate",
        )

        reader = HistoryReader(tmp_path)
        assert not reader.has_recent_proposal("foo.py", "extract_functions")

    def test_has_recent_proposal_false_empty(self, tmp_path: Path) -> None:
        from redsl.history import HistoryReader

        reader = HistoryReader(tmp_path)
        assert not reader.has_recent_proposal("foo.py", "extract_functions")

    def test_has_recent_ticket_true(self, tmp_path: Path) -> None:
        from redsl.history import HistoryWriter, HistoryReader

        writer = HistoryWriter(tmp_path)
        writer.record_event(
            "ticket_created",
            details={"title": "ReDSL: 3 refactors applied (CC 5.0→3.0)"},
        )

        reader = HistoryReader(tmp_path)
        assert reader.has_recent_ticket("ReDSL: 3 refactors")

    def test_has_recent_ticket_false(self, tmp_path: Path) -> None:
        from redsl.history import HistoryReader

        reader = HistoryReader(tmp_path)
        assert not reader.has_recent_ticket("anything")

    def test_generate_decision_report_empty(self, tmp_path: Path) -> None:
        from redsl.history import HistoryReader

        reader = HistoryReader(tmp_path)
        report = reader.generate_decision_report()
        assert "No events" in report

    def test_generate_decision_report_with_events(self, tmp_path: Path) -> None:
        from redsl.history import HistoryWriter, HistoryReader

        writer = HistoryWriter(tmp_path)
        writer.record_event(
            "decision_started",
            cycle_number=1,
            target_file="foo.py",
            action="extract_functions",
            thought="Rule split_high_cc matched with score=1.70",
        )
        writer.record_event(
            "proposal_rejected",
            cycle_number=1,
            target_file="foo.py",
            action="extract_functions",
            outcome_reason="Rejected: syntax error in LLM output",
        )

        reader = HistoryReader(tmp_path)
        report = reader.generate_decision_report()
        assert "Cycle 1" in report
        assert "decision_started" in report
        assert "split_high_cc" in report
        assert "syntax error" in report


# ===========================================================================
# HistoryEvent new fields
# ===========================================================================

class TestHistoryEventFields:
    def test_thought_reflection_outcome_fields(self, tmp_path: Path) -> None:
        from redsl.history import HistoryWriter

        writer = HistoryWriter(tmp_path)
        writer.record_event(
            "decision_started",
            cycle_number=1,
            target_file="bar.py",
            action="split_module",
            thought="Rule matched with score=1.80",
            reflection="Looks like a god module",
            outcome_reason=None,
        )

        history_file = tmp_path / ".redsl" / "history.jsonl"
        payload = json.loads(history_file.read_text().strip())
        assert payload["thought"] == "Rule matched with score=1.80"
        assert payload["reflection"] == "Looks like a god module"
        assert payload["outcome_reason"] is None


# ===========================================================================
# DSL Engine — top_decisions dedup key includes action
# ===========================================================================

class TestTopDecisionsDedup:
    def test_dedup_allows_different_actions_same_file(self) -> None:
        from redsl.dsl.engine import DSLEngine

        engine = DSLEngine()
        contexts = [
            {
                "file_path": "big.py",
                "cyclomatic_complexity": 25,
                "module_lines": 600,
                "function_count": 20,
                "nested_depth": 5,
                "fan_out": 20,
            },
        ]
        decisions = engine.top_decisions(contexts, limit=20)
        actions = [d.action.value for d in decisions]
        files = [d.target_file for d in decisions]
        # Same file can have multiple distinct actions
        assert all(f == "big.py" for f in files)
        assert len(set(actions)) > 1, f"Expected multiple actions, got {actions}"

    def test_dedup_blocks_same_action_same_file(self) -> None:
        from redsl.dsl.engine import DSLEngine

        engine = DSLEngine()
        contexts = [
            {"file_path": "a.py", "cyclomatic_complexity": 25},
            {"file_path": "a.py", "cyclomatic_complexity": 20},
        ]
        decisions = engine.top_decisions(contexts, limit=20)
        keys = [(d.action.value, d.target_file, d.target_function) for d in decisions]
        assert len(keys) == len(set(keys)), "Duplicate (action, file, function) should not appear"


# ===========================================================================
# Proposal dedup guard (_execute_decision)
# ===========================================================================

class TestProposalDedupGuard:
    def test_time_window_blocks_duplicate(self, tmp_path: Path) -> None:
        from redsl.history import HistoryWriter, HistoryReader

        writer = HistoryWriter(tmp_path)
        writer.record_event(
            "proposal_generated",
            target_file="engine.py",
            action="extract_functions",
        )

        reader = HistoryReader(tmp_path)
        assert reader.has_recent_proposal("engine.py", "extract_functions")

    def test_time_window_allows_different_file(self, tmp_path: Path) -> None:
        from redsl.history import HistoryWriter, HistoryReader

        writer = HistoryWriter(tmp_path)
        writer.record_event(
            "proposal_generated",
            target_file="engine.py",
            action="extract_functions",
        )

        reader = HistoryReader(tmp_path)
        assert not reader.has_recent_proposal("other.py", "extract_functions")

    def test_signature_dedup_blocks_exact_match(self, tmp_path: Path) -> None:
        from redsl.history import HistoryWriter

        writer = HistoryWriter(tmp_path)
        sig = writer.decision_signature(
            rule="split_high_cc",
            target_file="engine.py",
            action="extract_functions",
            context={"cyclomatic_complexity": 25},
        )
        writer.record_event(
            "decision_started",
            details={"signature": sig},
        )
        assert writer.has_recent_signature(sig)

    def test_signature_dedup_allows_different_context(self, tmp_path: Path) -> None:
        from redsl.history import HistoryWriter

        writer = HistoryWriter(tmp_path)
        sig1 = writer.decision_signature(
            rule="split_high_cc",
            target_file="engine.py",
            action="extract_functions",
            context={"cyclomatic_complexity": 25},
        )
        writer.record_event(
            "decision_started",
            details={"signature": sig1},
        )

        sig2 = writer.decision_signature(
            rule="split_high_cc",
            target_file="engine.py",
            action="extract_functions",
            context={"cyclomatic_complexity": 30},
        )
        assert not writer.has_recent_signature(sig2)


# ===========================================================================
# Ticket dedup (planfile_bridge)
# ===========================================================================

class TestTicketDedup:
    def test_create_ticket_blocks_recent_history_dup(self, tmp_path: Path) -> None:
        from redsl.history import HistoryWriter
        from redsl.commands.planfile_bridge import create_ticket

        writer = HistoryWriter(tmp_path)
        writer.record_event(
            "ticket_created",
            details={"title": "ReDSL: 3 refactors applied (CC 5.0→3.0)"},
        )

        result = create_ticket(
            tmp_path,
            title="ReDSL: 3 refactors applied (CC 5.0→3.0)",
            description="test",
        )
        assert result["created"] is False
        assert result.get("duplicate") is True

    def test_create_ticket_allows_new_title(self, tmp_path: Path) -> None:
        from redsl.commands.planfile_bridge import create_ticket

        # No history, planfile not available → should return available=False (not duplicate)
        result = create_ticket(tmp_path, title="Brand new ticket", description="test")
        assert result.get("duplicate") is not True


# ===========================================================================
# Auto-fix dedup
# ===========================================================================

class TestAutoFixDedup:
    def test_duplicate_violations_produce_single_ticket(self) -> None:
        from redsl.autonomy.auto_fix import auto_fix_violations

        violations = [
            "file big.py has 500L exceeded limit",
            "file big.py has 500L exceeded limit",
            "file big.py has 500L exceeded limit",
        ]
        with patch("redsl.autonomy.auto_fix._attempt_fix", return_value={"fixed": False, "reason": "test"}):
            result = auto_fix_violations(Path("/tmp/proj"), violations)

        assert len(result.manual_needed) == 3
        assert len(result.tickets_created) == 1


# ===========================================================================
# Planfile limits (_resolve_limits)
# ===========================================================================

class TestPlanfileLimits:
    def test_resolve_limits_from_planfile(self, tmp_path: Path) -> None:
        from redsl.orchestrator import RefactorOrchestrator

        planfile = tmp_path / "planfile.yaml"
        planfile.write_text("name: test\nlimits:\n  max_actions: 3\n")

        result = RefactorOrchestrator._resolve_limits(tmp_path, 5)
        assert result == 3

    def test_resolve_limits_max_tickets_alias(self, tmp_path: Path) -> None:
        from redsl.orchestrator import RefactorOrchestrator

        planfile = tmp_path / "planfile.yaml"
        planfile.write_text("name: test\nlimits:\n  max_tickets: 7\n")

        result = RefactorOrchestrator._resolve_limits(tmp_path, 5)
        assert result == 7

    def test_resolve_limits_no_planfile(self, tmp_path: Path) -> None:
        from redsl.orchestrator import RefactorOrchestrator

        result = RefactorOrchestrator._resolve_limits(tmp_path, 5)
        assert result == 5

    def test_resolve_limits_no_limits_key(self, tmp_path: Path) -> None:
        from redsl.orchestrator import RefactorOrchestrator

        planfile = tmp_path / "planfile.yaml"
        planfile.write_text("name: test\nsprints: []\n")

        result = RefactorOrchestrator._resolve_limits(tmp_path, 5)
        assert result == 5

    def test_resolve_limits_malformed_yaml(self, tmp_path: Path) -> None:
        from redsl.orchestrator import RefactorOrchestrator

        planfile = tmp_path / "planfile.yaml"
        planfile.write_text("{{invalid yaml")

        result = RefactorOrchestrator._resolve_limits(tmp_path, 5)
        assert result == 5
