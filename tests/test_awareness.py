from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from redsl import AwarenessManager as RootAwarenessManager, SelfModel as RootSelfModel
import redsl.cli as cli_module
from redsl.awareness import AwarenessManager, SelfModel
from redsl.awareness.git_timeline import GitTimelineAnalyzer, MetricPoint, TrendAnalysis
from redsl.awareness.health_model import HealthModel
from redsl.awareness.proactive import ProactiveAnalyzer
from redsl.memory import AgentMemory


class _DummySummary:
    def to_dict(self) -> dict[str, object]:
        return {"points": [], "trends": {}, "degradation_sources": []}


class _DummyGraph:
    def summarize(self) -> dict[str, object]:
        return {"project_count": 1, "edge_count": 0, "nodes": [], "edges": []}


class _DummyManager:
    def history(self, project_path: Path, depth: int = 20) -> _DummySummary:
        return _DummySummary()

    def ecosystem(self, root_path: Path) -> _DummyGraph:
        return _DummyGraph()

    def health(self, project_path: Path, depth: int = 20):
        return type("Health", (), {"to_dict": lambda self: {"score": 0.91, "status": "healthy"}})()

    def predict(self, project_path: Path, depth: int = 20) -> dict[str, object]:
        return {"alerts": [], "health": {"score": 0.91}, "trends": {}, "timeline": []}

    def self_assess(self, top_k: int = 5) -> dict[str, object]:
        return {
            "profile": {"overall_confidence": 0.9, "capabilities": [], "recommended_focus": []},
            "memory_stats": {"episodic": 2, "semantic": 1, "procedural": 0},
        }


def test_awareness_manager_build_snapshot_and_context(tmp_path: Path, monkeypatch) -> None:
    project_dir = tmp_path / "project-a"
    project_dir.mkdir()
    (project_dir / "TODO.md").write_text("- [ ] task\n", encoding="utf-8")

    timeline = [
        MetricPoint(
            commit_hash="a1",
            timestamp="2026-04-08T00:00:00+00:00",
            project_name="project-a",
            avg_cc=1.0,
            critical_count=0,
            total_lines=10,
            total_files=1,
        ),
        MetricPoint(
            commit_hash="b2",
            timestamp="2026-04-08T01:00:00+00:00",
            project_name="project-a",
            avg_cc=3.0,
            critical_count=1,
            total_lines=20,
            total_files=2,
        ),
    ]

    monkeypatch.setattr(GitTimelineAnalyzer, "build_timeline", lambda self, depth=None: timeline)

    manager = AwarenessManager(memory=AgentMemory(tmp_path / "memory"), default_depth=2)
    snapshot = manager.build_snapshot(project_dir, depth=2, ecosystem_root=tmp_path)

    context = snapshot.to_context()
    prompt_context = snapshot.to_prompt_context()

    assert context["project_name"] == "project-a"
    assert context["timeline_depth"] == 2
    assert snapshot.health is not None
    assert snapshot.health.score > 0
    assert any(alert.metric_name == "cc_mean" for alert in snapshot.alerts)
    assert snapshot.ecosystem is not None
    assert snapshot.ecosystem.summarize()["project_count"] == 1
    assert prompt_context["latest_summary"].startswith("b2")


def test_awareness_manager_snapshot_cache_invalidates_on_memory_change(tmp_path: Path, monkeypatch) -> None:
    project_dir = tmp_path / "project-a"
    project_dir.mkdir()

    timeline = [
        MetricPoint(
            commit_hash="a1",
            timestamp="2026-04-08T00:00:00+00:00",
            project_name="project-a",
            avg_cc=1.0,
            critical_count=0,
            total_lines=10,
            total_files=1,
        ),
        MetricPoint(
            commit_hash="b2",
            timestamp="2026-04-08T01:00:00+00:00",
            project_name="project-a",
            avg_cc=2.0,
            critical_count=1,
            total_lines=20,
            total_files=2,
        ),
    ]
    trends = {
        "cc_mean": TrendAnalysis(
            metric_name="cc_mean",
            trend="degrading",
            slope=1.0,
            current_value=2.0,
            predicted_value=3.0,
            confidence=0.8,
            samples=2,
            history=[1.0, 2.0],
        ),
    }

    monkeypatch.setattr(GitTimelineAnalyzer, "build_timeline", lambda self, depth=None: timeline)
    monkeypatch.setattr(GitTimelineAnalyzer, "analyze_trends", lambda self, points, horizon=1: trends)
    monkeypatch.setattr(AwarenessManager, "_git_head", lambda self, project_path: "head-1")

    manager = AwarenessManager(memory=AgentMemory(tmp_path / "memory"), default_depth=2)

    first_snapshot = manager.build_snapshot(project_dir, depth=2, ecosystem_root=tmp_path / "missing")
    second_snapshot = manager.build_snapshot(project_dir, depth=2, ecosystem_root=tmp_path / "missing")

    assert second_snapshot is first_snapshot

    manager.memory.remember_action("cache_invalidation", "x.py", "applied", True)

    third_snapshot = manager.build_snapshot(project_dir, depth=2, ecosystem_root=tmp_path / "missing")

    assert third_snapshot is not first_snapshot
    assert third_snapshot is not second_snapshot


def test_self_model_records_outcome_and_assesses(tmp_path: Path) -> None:
    memory = AgentMemory(tmp_path / "memory")
    self_model = SelfModel(memory)

    self_model.record_outcome("extract_functions", True, "applied", target="x.py")
    self_model.record_outcome("extract_functions", False, "failed", target="y.py")

    profile = self_model.assess()

    assert profile.capabilities
    assert profile.capabilities[0].name == "extract_functions"
    assert profile.capabilities[0].attempts == 2
    assert profile.capabilities[0].success_rate == 0.5
    assert profile.overall_confidence == 0.5


def test_proactive_analyzer_orders_critical_alert_first() -> None:
    timeline = [
        MetricPoint(
            commit_hash="a1",
            timestamp="2026-04-08T00:00:00+00:00",
            project_name="project-a",
            avg_cc=10.0,
            critical_count=0,
            total_lines=100,
            total_files=1,
        ),
        MetricPoint(
            commit_hash="b2",
            timestamp="2026-04-08T01:00:00+00:00",
            project_name="project-a",
            avg_cc=20.0,
            critical_count=2,
            total_lines=200,
            total_files=2,
        ),
    ]
    trends = {
        "cc_mean": TrendAnalysis(
            metric_name="cc_mean",
            trend="degrading",
            slope=5.0,
            current_value=20.0,
            predicted_value=28.0,
            confidence=0.9,
            samples=2,
            history=[10.0, 20.0],
        ),
        "critical_count": TrendAnalysis(
            metric_name="critical_count",
            trend="degrading",
            slope=1.0,
            current_value=2.0,
            predicted_value=3.0,
            confidence=0.8,
            samples=2,
            history=[0.0, 2.0],
        ),
    }

    health = HealthModel().assess(timeline, trends)
    alerts = ProactiveAnalyzer().analyze(timeline, trends, health)

    assert alerts
    assert alerts[0].severity == "critical"
    assert alerts[0].metric_name == "cc_mean"
    assert alerts[0].recommended_actions[0].startswith("Schedule predictive refactoring")


def test_cli_registers_awareness_commands_and_renders_json(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()

    help_result = runner.invoke(cli_module.cli, ["--help"])
    assert help_result.exit_code == 0
    for command_name in ["history", "ecosystem", "health", "predict", "self-assess"]:
        assert command_name in help_result.output

    project_dir = tmp_path / "project-a"
    project_dir.mkdir()

    monkeypatch.setattr(cli_module, "_setup_logging", lambda *args, **kwargs: Path("/tmp/redsl.log"))
    monkeypatch.setattr(cli_module, "_build_awareness_manager", lambda: _DummyManager())

    history_result = runner.invoke(cli_module.cli, ["history", "--project", str(project_dir), "--depth", "3"])
    assert history_result.exit_code == 0
    history_payload = json.loads(history_result.output)
    assert history_payload["depth"] == 3
    assert history_payload["points"] == []

    ecosystem_result = runner.invoke(cli_module.cli, ["ecosystem", "--root", str(tmp_path)])
    assert ecosystem_result.exit_code == 0
    ecosystem_payload = json.loads(ecosystem_result.output)
    assert ecosystem_payload["project_count"] == 1

    predict_result = runner.invoke(cli_module.cli, ["predict", "--project", str(project_dir), "--depth", "4"])
    assert predict_result.exit_code == 0
    predict_payload = json.loads(predict_result.output)
    assert predict_payload["timeline"] == []
    assert predict_payload["health"]["score"] == 0.91

    health_result = runner.invoke(cli_module.cli, ["health", "--project", str(project_dir), "--depth", "4"])
    assert health_result.exit_code == 0
    health_payload = json.loads(health_result.output)
    assert health_payload["status"] == "healthy"

    assess_result = runner.invoke(cli_module.cli, ["self-assess", "--top-k", "2"])
    assert assess_result.exit_code == 0
    assess_payload = json.loads(assess_result.output)
    assert assess_payload["profile"]["overall_confidence"] == 0.9
    assert assess_payload["memory_stats"]["episodic"] == 2


def test_root_package_exports_awareness_facade() -> None:
    assert RootAwarenessManager is AwarenessManager
    assert RootSelfModel is SelfModel
