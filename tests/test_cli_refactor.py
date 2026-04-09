from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from click.testing import CliRunner

import redsl.cli as cli_module


@dataclass
class DummyDecision:
    score: float


class DummyAnalysis:
    def to_dsl_contexts(self) -> list[dict[str, int]]:
        return [{"metric": 1}]


class DummyAnalyzer:
    def __init__(self) -> None:
        self.last_project_path: Path | None = None

    def analyze_project(self, project_path: Path) -> DummyAnalysis:
        self.last_project_path = project_path
        return DummyAnalysis()


class DummyDslEngine:
    def __init__(self) -> None:
        self.last_contexts: list[dict[str, int]] | None = None

    def evaluate(self, contexts: list[dict[str, int]]) -> list[DummyDecision]:
        self.last_contexts = contexts
        return [DummyDecision(score=2.0), DummyDecision(score=7.0), DummyDecision(score=5.0)]


@dataclass
class DummyReport:
    cycle_number: int = 4
    analysis_summary: str = "done"
    decisions_count: int = 3
    proposals_generated: int = 3
    proposals_applied: int = 2
    proposals_rejected: int = 1
    errors: list[str] = field(default_factory=lambda: ["first error"])


class DummyOrchestrator:
    last_instance: DummyOrchestrator | None = None

    def __init__(self, config) -> None:
        self.config = config
        self.analyzer = DummyAnalyzer()
        self.dsl_engine = DummyDslEngine()
        self.run_cycle_called = False
        self.run_cycle_kwargs: dict[str, object] | None = None
        DummyOrchestrator.last_instance = self

    def run_cycle(self, project_path: Path, **kwargs):
        self.run_cycle_called = True
        self.run_cycle_kwargs = {"project_path": project_path, **kwargs}
        return DummyReport()


def _prepare_cli(monkeypatch, tmp_path: Path) -> Path:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    monkeypatch.setattr(cli_module, "_setup_logging", lambda *args, **kwargs: tmp_path / "redsl.log")
    monkeypatch.setattr(cli_module, "RefactorOrchestrator", DummyOrchestrator)
    return project_dir


def test_refactor_dry_run_yaml_renders_plan_and_skips_cycle(tmp_path: Path, monkeypatch) -> None:
    project_dir = _prepare_cli(monkeypatch, tmp_path)
    runner = CliRunner()

    monkeypatch.setattr(cli_module, "format_plan_yaml", lambda decisions, analysis: "PLAN-YAML")
    monkeypatch.setattr(cli_module, "format_refactor_plan", lambda decisions, output_format, analysis: "PLAN-TEXT")

    result = runner.invoke(
        cli_module.cli,
        ["refactor", str(project_dir), "--dry-run", "--format", "yaml"],
    )

    assert result.exit_code == 0
    assert "PLAN-YAML" in result.output
    assert DummyOrchestrator.last_instance is not None
    assert DummyOrchestrator.last_instance.config.refactor.dry_run is True
    assert DummyOrchestrator.last_instance.config.refactor.reflection_rounds == 0
    assert DummyOrchestrator.last_instance.run_cycle_called is False


def test_refactor_live_json_emits_payload_and_passes_flags(tmp_path: Path, monkeypatch) -> None:
    project_dir = _prepare_cli(monkeypatch, tmp_path)
    runner = CliRunner()

    monkeypatch.setattr(cli_module, "_serialize_analysis", lambda analysis: {"kind": "analysis"})
    monkeypatch.setattr(cli_module, "_serialize_decision", lambda decision: {"score": decision.score})
    monkeypatch.setattr(cli_module, "_get_timestamp", lambda: "2026-04-08T00:00:00Z")
    monkeypatch.setattr(cli_module, "format_cycle_report_yaml", lambda report, decisions, analysis: "CYCLE-YAML")

    result = runner.invoke(
        cli_module.cli,
        [
            "refactor",
            str(project_dir),
            "--format",
            "json",
            "--use-code2llm",
            "--validate-regix",
            "--rollback",
            "--sandbox",
        ],
    )

    assert result.exit_code == 0
    assert "Sandbox mode: each refactoring will be tested in Docker before applying." in result.output
    json_start = result.output.index("{")
    json_end = result.output.rindex("}") + 1
    payload = json.loads(result.output[json_start:json_end])
    report = payload["redsl_report"]
    assert report["timestamp"] == "2026-04-08T00:00:00Z"
    assert report["cycle"] == 4
    assert report["analysis"] == {"kind": "analysis"}
    assert report["decisions"] == [{"score": 7.0}, {"score": 5.0}, {"score": 2.0}]
    assert report["execution"] == {
        "proposals_generated": 3,
        "proposals_applied": 2,
        "proposals_rejected": 1,
    }
    assert report["errors"] == ["first error"]
    assert DummyOrchestrator.last_instance is not None
    assert DummyOrchestrator.last_instance.run_cycle_called is True
    assert DummyOrchestrator.last_instance.run_cycle_kwargs == {
        "project_path": project_dir,
        "max_actions": 10,
        "use_code2llm": True,
        "validate_regix": True,
        "rollback_on_failure": True,
        "use_sandbox": True,
    }


# ---------------------------------------------------------------------------
# CLI example subcommand tests
# ---------------------------------------------------------------------------


def test_example_list_shows_all_scenarios() -> None:
    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["example", "list"])
    assert result.exit_code == 0
    for name in ["basic-analysis", "custom-rules", "full-pipeline", "memory-learning", "api-integration", "awareness", "pyqual", "audit", "pr-bot", "badge"]:
        assert name in result.output


def test_example_memory_learning_default() -> None:
    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["example", "memory-learning"])
    assert result.exit_code == 0
    assert "EPISODIC" in result.output
    assert "SEMANTIC" in result.output
    assert "PROCEDURAL" in result.output


def test_example_basic_analysis_advanced() -> None:
    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["example", "basic-analysis", "--scenario", "advanced"])
    assert result.exit_code == 0
    assert "advanced" in result.output.lower() or "Analiza" in result.output


# ---------------------------------------------------------------------------
# batch pyqual-run CLI registration test
# ---------------------------------------------------------------------------


def test_batch_pyqual_run_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["batch", "pyqual-run", "--help"])
    assert result.exit_code == 0
    assert "pyqual" in result.output.lower()
    assert "--pipeline" in result.output
    assert "--push" in result.output
    assert "--publish" in result.output
    assert "--profile" in result.output
    assert "--fix-config" in result.output
    assert "--include" in result.output
    assert "--exclude" in result.output
    assert "--dry-run" in result.output
    assert "--skip-dirty" in result.output
    assert "--fail-fast" in result.output


def test_batch_pyqual_run_forwards_options(monkeypatch, tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setattr(cli_module, "_setup_logging", lambda *args, **kwargs: tmp_path / "redsl.log")

    captured: dict[str, object] = {}

    def fake_run_pyqual_batch(
        workspace_root: Path,
        max_fixes: int = 30,
        run_pipeline: bool = False,
        git_push: bool = False,
        limit: int = 0,
        profile: str = "auto",
        publish: bool = False,
        fix_config: bool = False,
        include: tuple[str, ...] | list[str] | None = None,
        exclude: tuple[str, ...] | list[str] | None = None,
        dry_run: bool = False,
        skip_dirty: bool = False,
        fail_fast: bool = False,
    ) -> dict[str, object]:
        captured.update(
            {
                "workspace_root": workspace_root,
                "max_fixes": max_fixes,
                "run_pipeline": run_pipeline,
                "git_push": git_push,
                "limit": limit,
                "include": include,
                "exclude": exclude,
                "profile": profile,
                "publish": publish,
                "fix_config": fix_config,
                "dry_run": dry_run,
                "skip_dirty": skip_dirty,
                "fail_fast": fail_fast,
            }
        )
        return {}

    monkeypatch.setattr(cli_module.batch_pyqual_commands, "run_pyqual_batch", fake_run_pyqual_batch)

    runner = CliRunner()
    result = runner.invoke(
        cli_module.cli,
        [
            "batch", "pyqual-run", str(workspace),
            "--max-fixes", "7",
            "--limit", "3",
            "--include", "alpha*",
            "--include", "beta",
            "--exclude", "beta-old",
            "--profile", "python-full",
            "--pipeline",
            "--push",
            "--publish",
            "--fix-config",
            "--dry-run",
            "--skip-dirty",
            "--fail-fast",
        ],
    )

    assert result.exit_code == 0
    assert captured["workspace_root"] == workspace
    assert captured["max_fixes"] == 7
    assert captured["limit"] == 3
    assert captured["include"] == ("alpha*", "beta")
    assert captured["exclude"] == ("beta-old",)
    assert captured["profile"] == "python-full"
    assert captured["run_pipeline"] is True
    assert captured["git_push"] is True
    assert captured["publish"] is True
    assert captured["fix_config"] is True
    assert captured["dry_run"] is True
    assert captured["skip_dirty"] is True
    assert captured["fail_fast"] is True


def test_batch_autofix_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["batch", "autofix", "--help"])
    assert result.exit_code == 0
    assert "Auto-fix" in result.output
