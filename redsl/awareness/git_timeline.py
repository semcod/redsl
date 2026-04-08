"""Git timeline analysis for temporal awareness — thin facade.

Backward compatibility: All class APIs remain unchanged.
Implementation now delegates to focused submodules:
- timeline_models: Data classes (MetricPoint, TrendAnalysis, TimelineSummary)
- timeline_analysis: Trend analysis and prediction logic
- timeline_git: Git operations provider
- timeline_toon: Toon file collection and processing
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

from redsl.analyzers import CodeAnalyzer
from redsl.awareness.timeline_analysis import TimelineAnalyzer
from redsl.awareness.timeline_git import GitTimelineProvider
from redsl.awareness.timeline_models import MetricPoint, TimelineSummary, TrendAnalysis, TrendState
from redsl.awareness.timeline_toon import ToonCollector

logger = logging.getLogger(__name__)

# Re-export data classes for backward compatibility
__all__ = [
    "MetricPoint",
    "TrendAnalysis",
    "TimelineSummary",
    "TrendState",
    "GitTimelineAnalyzer",
]


class GitTimelineAnalyzer:
    """Build a historical metric timeline from git commits — facade.

    This is a thin facade that delegates to specialized provider classes.
    Maintains full backward compatibility with the original API.
    """

    _TOON_PRIORITY = GitTimelineProvider._TOON_PRIORITY

    def __init__(
        self,
        project_path: Path,
        depth: int = 20,
        analyzer: CodeAnalyzer | None = None,
    ) -> None:
        self.project_path = Path(project_path).resolve()
        self.depth = depth
        self.analyzer = analyzer or CodeAnalyzer()
        self._git_provider = GitTimelineProvider(self.project_path, self.analyzer)
        self._toon_collector = ToonCollector(self.project_path, self._git_provider, self.analyzer)
        self.repo_root = self._git_provider.repo_root
        self.timeline: list[MetricPoint] = []

    def build_timeline(self, depth: int | None = None) -> list[MetricPoint]:
        """Build a chronological timeline from git history."""
        if self.repo_root is None:
            logger.info("No git repository found for %s", self.project_path)
            self.timeline = []
            return []

        depth = depth or self.depth
        commits = self._git_provider._git_log(depth)
        points: list[MetricPoint] = []

        for commit_hash, timestamp, message in commits:
            point = self._toon_collector.snapshot_for_commit(commit_hash, timestamp, message)
            if point is not None:
                points.append(point)

        self.timeline = points
        return list(points)

    def analyze_trends(
        self,
        timeline: Sequence[MetricPoint] | None = None,
        horizon: int = 1,
    ) -> dict[str, TrendAnalysis]:
        """Analyze metric trends from the current timeline."""
        points = list(timeline or self.timeline or self.build_timeline())
        return TimelineAnalyzer.analyze_trends(points, horizon=horizon)

    def predict_future_state(
        self,
        horizon: int = 1,
        timeline: Sequence[MetricPoint] | None = None,
    ) -> dict[str, TrendAnalysis]:
        """Predict the next state by extrapolating each metric trend."""
        return self.analyze_trends(timeline=timeline, horizon=horizon)

    def find_degradation_sources(
        self,
        timeline: Sequence[MetricPoint] | None = None,
    ) -> list[dict]:
        """Return commits with the largest negative quality jumps first."""
        points = list(timeline or self.timeline or self.build_timeline())
        return TimelineAnalyzer.find_degradation_sources(points)

    def summarize(self, depth: int | None = None) -> TimelineSummary:
        """Build a cached summary object."""
        points = self.build_timeline(depth=depth)
        trends = self.analyze_trends(points)
        sources = self.find_degradation_sources(points)
        return TimelineSummary(points=points, trends=trends, degradation_sources=sources)

    # Backward-compatible internal method aliases
    def _resolve_repo_root(self) -> Path | None:
        return self._git_provider._resolve_repo_root()

    def _project_rel_path(self) -> str:
        return self._git_provider._project_rel_path()

    def _git_log(self, depth: int) -> list[tuple[str, int, str]]:
        return self._git_provider._git_log(depth)

    def _snapshot_for_commit(self, commit_hash: str, timestamp: int, message: str) -> MetricPoint | None:
        return self._toon_collector.snapshot_for_commit(commit_hash, timestamp, message)

    def _collect_toon_contents(self, commit_hash: str) -> dict[str, str]:
        return self._toon_collector._collect_toon_contents(commit_hash)

    @staticmethod
    def _empty_toon_contents() -> dict[str, str]:
        return ToonCollector._empty_toon_contents()

    def _store_toon_content(self, contents: dict[str, str], rel_file: str, content: str) -> None:
        self._toon_collector._store_toon_content(contents, rel_file, content)

    def _toon_bucket(self, name: str) -> str | None:
        return self._toon_collector._toon_bucket(name)

    def _sorted_toon_candidates(self, candidates: Sequence[str]) -> list[str]:
        return self._toon_collector._sorted_toon_candidates(candidates)

    def _toon_candidate_priority(self, candidate: str) -> tuple[int, str]:
        return self._toon_collector._toon_candidate_priority(candidate)

    def _git_show(self, commit_hash: str, rel_file: str) -> str:
        return self._git_provider._git_show(commit_hash, rel_file)

    @staticmethod
    def _is_duplication_file(name: str) -> bool:
        return GitTimelineProvider._is_duplication_file(name)

    @staticmethod
    def _is_validation_file(name: str) -> bool:
        return GitTimelineProvider._is_validation_file(name)

    @staticmethod
    def _build_series_map(points: Sequence[MetricPoint]) -> dict[str, list[float]]:
        return TimelineAnalyzer._build_series_map(points)

    @staticmethod
    def _apply_trend_aliases(trends: dict[str, TrendAnalysis]) -> None:
        TimelineAnalyzer._apply_trend_aliases(trends)

    @staticmethod
    def _linear_regression(values: Sequence[float]) -> tuple[float, float]:
        return TimelineAnalyzer._linear_regression(values)

    def _analyze_series(self, metric_name: str, values: Sequence[float], horizon: int = 1) -> TrendAnalysis:
        return TimelineAnalyzer._analyze_series(metric_name, values, horizon)
