"""Awareness package for temporal, ecosystem and self-model signals."""

from __future__ import annotations

from dataclasses import dataclass, field
import subprocess
from pathlib import Path
from typing import Any

from redsl.analyzers import CodeAnalyzer
from redsl.memory import AgentMemory

from .change_patterns import ChangePattern, ChangePatternLearner
from .ecosystem import EcosystemGraph, ProjectNode
from .git_timeline import GitTimelineAnalyzer
from .health_model import HealthDimension, HealthModel, UnifiedHealth
from .proactive import ProactiveAlert, ProactiveAnalyzer
from .self_model import AgentCapabilityProfile, CapabilityStat, SelfModel
from .timeline_analysis import TimelineAnalyzer
from .timeline_git import GitTimelineProvider
from .timeline_models import MetricPoint, TimelineSummary, TrendAnalysis, TrendState
from .timeline_toon import ToonCollector


@dataclass(slots=True)
class AwarenessSnapshot:
    """Compact overview of the current awareness state for a project."""

    project_path: Path
    depth: int
    timeline: list[MetricPoint] = field(default_factory=list)
    trends: dict[str, TrendAnalysis] = field(default_factory=dict)
    patterns: list[ChangePattern] = field(default_factory=list)
    ecosystem: EcosystemGraph | None = None
    health: UnifiedHealth | None = None
    alerts: list[ProactiveAlert] = field(default_factory=list)
    self_profile: AgentCapabilityProfile | None = None
    summary: str = ""

    @property
    def latest_point(self) -> MetricPoint | None:
        return self.timeline[-1] if self.timeline else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_path": str(self.project_path),
            "depth": self.depth,
            "summary": self.summary,
            "timeline": [point.to_dict() for point in self.timeline],
            "trends": {name: trend.to_dict() for name, trend in self.trends.items()},
            "patterns": [pattern.to_dict() for pattern in self.patterns],
            "ecosystem": self.ecosystem.summarize() if self.ecosystem else None,
            "health": self.health.to_dict() if self.health else None,
            "alerts": [alert.to_dict() for alert in self.alerts],
            "self_profile": self.self_profile.to_dict() if self.self_profile else None,
        }

    def to_context(self) -> dict[str, Any]:
        """Return a concise context payload for DSL/prompt enrichment."""
        latest = self.latest_point
        latest_dict = latest.to_dict() if latest else {}
        trend_summary = {
            name: trend.to_dict()
            for name, trend in self.trends.items()
            if name in {"cc_mean", "critical_count", "validation_issues", "total_lines", "total_files"}
        }
        return {
            "project_path": str(self.project_path),
            "project_name": latest.project_name if latest else self.project_path.name,
            "timeline_depth": len(self.timeline),
            "summary": self.summary,
            "latest_point": latest_dict,
            "trend_summary": trend_summary,
            "health": self.health.to_dict() if self.health else {},
            "proactive_alerts": [alert.to_dict() for alert in self.alerts[:5]],
            "pattern_summary": [pattern.to_dict() for pattern in self.patterns[:5]],
            "ecosystem_context": self.ecosystem.summarize() if self.ecosystem else {},
            "self_model": self.self_profile.to_dict() if self.self_profile else {},
        }

    def to_prompt_context(self) -> dict[str, Any]:
        """Return prompt-friendly context with short human-readable summaries."""
        latest = self.latest_point
        latest_summary = (
            f"{latest.commit_hash[:7]} cc={latest.avg_cc:.2f} critical={latest.critical_count} lines={latest.total_lines}"
            if latest
            else "no timeline data"
        )
        return {
            "summary": self.summary,
            "project_name": latest.project_name if latest else self.project_path.name,
            "latest_summary": latest_summary,
            "health": self.health.to_dict() if self.health else {},
            "alerts": [alert.to_dict() for alert in self.alerts[:3]],
            "ecosystem": self.ecosystem.summarize() if self.ecosystem else {},
            "trends": {
                name: trend.to_dict()
                for name, trend in self.trends.items()
                if name in {"cc_mean", "critical_count", "validation_issues"}
            },
        }


class AwarenessManager:
    """Facade that combines all awareness layers into one snapshot."""

    def __init__(
        self,
        memory: AgentMemory | None = None,
        analyzer: CodeAnalyzer | None = None,
        default_depth: int = 20,
        ecosystem_root: Path | None = None,
    ) -> None:
        self.memory = memory or AgentMemory()
        self.analyzer = analyzer or CodeAnalyzer()
        self.default_depth = default_depth
        self.ecosystem_root = Path(ecosystem_root).resolve() if ecosystem_root else None
        self.health_model = HealthModel()
        self.proactive_analyzer = ProactiveAnalyzer(self.health_model)
        self.self_model = SelfModel(self.memory)
        self._last_snapshot: AwarenessSnapshot | None = None
        self._last_snapshot_key: tuple[str, int, str | None, str | None, tuple[int, int, int]] | None = None

    def _memory_fingerprint(self) -> tuple[int, int, int]:
        stats = self.memory.stats()
        return (
            int(stats.get("episodic", 0)),
            int(stats.get("semantic", 0)),
            int(stats.get("procedural", 0)),
        )

    def _git_head(self, project_path: Path) -> str | None:
        try:
            result = subprocess.run(
                ["git", "-C", str(project_path), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            return None

        head = result.stdout.strip()
        return head or None

    def _build_cache_key(
        self,
        project_path: Path,
        depth: int,
        ecosystem_root: Path | None,
    ) -> tuple[str, int, str | None, str | None, tuple[int, int, int]] | None:
        git_head = self._git_head(project_path)
        if git_head is None:
            return None

        return (
            str(project_path),
            depth,
            str(ecosystem_root) if ecosystem_root else None,
            git_head,
            self._memory_fingerprint(),
        )

    def build_snapshot(
        self,
        project_path: Path,
        depth: int | None = None,
        ecosystem_root: Path | None = None,
    ) -> AwarenessSnapshot:
        project_path = Path(project_path).resolve()
        depth = depth or self.default_depth
        resolved_ecosystem_root = Path(ecosystem_root).resolve() if ecosystem_root else self.ecosystem_root
        cache_key = self._build_cache_key(project_path, depth, resolved_ecosystem_root)
        if cache_key is not None and self._last_snapshot is not None and self._last_snapshot_key == cache_key:
            return self._last_snapshot

        timeline_analyzer = GitTimelineAnalyzer(
            project_path=project_path,
            depth=depth,
            analyzer=self.analyzer,
        )
        timeline = timeline_analyzer.build_timeline(depth=depth)
        trends = timeline_analyzer.analyze_trends(timeline)
        pattern_learner = ChangePatternLearner()
        patterns = pattern_learner.learn_from_timeline(timeline, trends)
        health = self.health_model.assess(timeline, trends)
        alerts = self.proactive_analyzer.analyze(timeline, trends, health)

        ecosystem_graph = None
        resolved_ecosystem_root = resolved_ecosystem_root or project_path.parent
        if resolved_ecosystem_root and Path(resolved_ecosystem_root).exists():
            ecosystem_graph = EcosystemGraph(Path(resolved_ecosystem_root)).build()

        self_profile = self.self_model.assess()
        summary = self._summarize_snapshot(project_path, timeline, health, alerts, ecosystem_graph)
        snapshot = AwarenessSnapshot(
            project_path=project_path,
            depth=depth,
            timeline=timeline,
            trends=trends,
            patterns=patterns,
            ecosystem=ecosystem_graph,
            health=health,
            alerts=alerts,
            self_profile=self_profile,
            summary=summary,
        )
        if cache_key is not None:
            self._last_snapshot = snapshot
            self._last_snapshot_key = cache_key
        return snapshot

    def build_context(
        self,
        project_path: Path,
        depth: int | None = None,
        ecosystem_root: Path | None = None,
    ) -> dict[str, Any]:
        return self.build_snapshot(project_path, depth=depth, ecosystem_root=ecosystem_root).to_context()

    def build_prompt_context(
        self,
        project_path: Path,
        depth: int | None = None,
        ecosystem_root: Path | None = None,
    ) -> dict[str, Any]:
        return self.build_snapshot(project_path, depth=depth, ecosystem_root=ecosystem_root).to_prompt_context()

    def history(
        self,
        project_path: Path,
        depth: int | None = None,
    ) -> TimelineSummary:
        timeline_analyzer = GitTimelineAnalyzer(
            project_path=Path(project_path).resolve(),
            depth=depth or self.default_depth,
            analyzer=self.analyzer,
        )
        return timeline_analyzer.summarize(depth=depth)

    def ecosystem(
        self,
        root: Path,
    ) -> EcosystemGraph:
        return EcosystemGraph(Path(root).resolve()).build()

    def health(
        self,
        project_path: Path,
        depth: int | None = None,
    ) -> UnifiedHealth:
        snapshot = self.build_snapshot(project_path, depth=depth)
        return snapshot.health or UnifiedHealth(score=0.0, status="unknown")

    def predict(
        self,
        project_path: Path,
        depth: int | None = None,
        ecosystem_root: Path | None = None,
    ) -> dict[str, Any]:
        snapshot = self.build_snapshot(project_path, depth=depth, ecosystem_root=ecosystem_root)
        return {
            "project_path": str(snapshot.project_path),
            "depth": snapshot.depth,
            "summary": snapshot.summary,
            "alerts": [alert.to_dict() for alert in snapshot.alerts],
            "health": snapshot.health.to_dict() if snapshot.health else None,
            "trends": {name: trend.to_dict() for name, trend in snapshot.trends.items()},
            "timeline": [point.to_dict() for point in snapshot.timeline],
        }

    def self_assess(self, top_k: int = 5) -> dict[str, Any]:
        profile = self.self_model.assess(top_k=top_k)
        return {
            "profile": profile.to_dict(),
            "memory_stats": self.memory.stats(),
            "last_snapshot": self._last_snapshot.to_context() if self._last_snapshot else {},
        }

    @staticmethod
    def _summarize_snapshot(
        project_path: Path,
        timeline: list[MetricPoint],
        health: UnifiedHealth,
        alerts: list[ProactiveAlert],
        ecosystem: EcosystemGraph | None,
    ) -> str:
        latest = timeline[-1] if timeline else None
        ecosystem_projects = len(ecosystem.nodes) if ecosystem else 0
        latest_cc = latest.avg_cc if latest else 0.0
        latest_critical = latest.critical_count if latest else 0
        return (
            f"{project_path.name}: health={health.score:.2f} ({health.status}), "
            f"latest_cc={latest_cc:.2f}, critical={latest_critical}, "
            f"alerts={len(alerts)}, ecosystem_projects={ecosystem_projects}"
        )


__all__ = [
    # Timeline facade and data models
    "MetricPoint",
    "TrendAnalysis",
    "TimelineSummary",
    "GitTimelineAnalyzer",
    # Timeline specialized modules
    "TimelineAnalyzer",
    "GitTimelineProvider",
    "ToonCollector",
    "TrendState",
    # Other awareness modules
    "ChangePattern",
    "ChangePatternLearner",
    "ProjectNode",
    "EcosystemGraph",
    "HealthDimension",
    "UnifiedHealth",
    "HealthModel",
    "ProactiveAlert",
    "ProactiveAnalyzer",
    "CapabilityStat",
    "AgentCapabilityProfile",
    "SelfModel",
    "AwarenessSnapshot",
    "AwarenessManager",
]
