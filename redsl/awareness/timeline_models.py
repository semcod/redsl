"""Data models for git timeline analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

TrendState = Literal["improving", "stable", "degrading", "unknown"]


@dataclass(slots=True)
class MetricPoint:
    """Single timeline point captured from a git commit."""

    commit_hash: str
    timestamp: str
    commit_message: str = ""
    project_name: str = ""
    total_files: int = 0
    total_lines: int = 0
    avg_cc: float = 0.0
    critical_count: int = 0
    module_count: int = 0
    duplicate_count: int = 0
    validation_issues: int = 0
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def cc_mean(self) -> float:
        """Backward-compatible alias used by some tests and prompts."""
        return self.avg_cc

    def to_dict(self) -> dict[str, Any]:
        return {
            "commit_hash": self.commit_hash,
            "timestamp": self.timestamp,
            "commit_message": self.commit_message,
            "project_name": self.project_name,
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "avg_cc": self.avg_cc,
            "cc_mean": self.cc_mean,
            "critical_count": self.critical_count,
            "module_count": self.module_count,
            "duplicate_count": self.duplicate_count,
            "validation_issues": self.validation_issues,
            "raw": self.raw,
        }


@dataclass(slots=True)
class TrendAnalysis:
    """Trend summary for a single metric series."""

    metric_name: str
    trend: TrendState
    slope: float
    current_value: float
    predicted_value: float
    confidence: float
    samples: int
    history: list[float] = field(default_factory=list)

    @property
    def current(self) -> float:
        return self.current_value

    @property
    def predicted(self) -> float:
        return self.predicted_value

    @property
    def is_degrading(self) -> bool:
        return self.trend == "degrading"

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "trend": self.trend,
            "slope": self.slope,
            "current_value": self.current_value,
            "current": self.current,
            "predicted_value": self.predicted_value,
            "predicted": self.predicted,
            "confidence": self.confidence,
            "samples": self.samples,
            "history": list(self.history),
        }


@dataclass(slots=True)
class TimelineSummary:
    """High-level summary of a git timeline."""

    points: list[MetricPoint] = field(default_factory=list)
    trends: dict[str, TrendAnalysis] = field(default_factory=dict)
    degradation_sources: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "points": [point.to_dict() for point in self.points],
            "trends": {key: trend.to_dict() for key, trend in self.trends.items()},
            "degradation_sources": list(self.degradation_sources),
        }


__all__ = ["MetricPoint", "TrendAnalysis", "TimelineSummary", "TrendState"]
