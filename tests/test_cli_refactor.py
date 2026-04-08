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
        "rollback_on_regression": True,
        "use_sandbox": True,
    }
