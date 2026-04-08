"""Unified health model for awareness."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .git_timeline import MetricPoint, TrendAnalysis


@dataclass(slots=True)
class HealthDimension:
    """Single health dimension with score and rationale."""

    name: str
    score: float
    trend: str = "stable"
    weight: float = 1.0
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": self.score,
            "trend": self.trend,
            "weight": self.weight,
            "evidence": list(self.evidence),
        }


@dataclass(slots=True)
class UnifiedHealth:
    """Aggregated health snapshot."""

    score: float
    dimensions: list[HealthDimension] = field(default_factory=list)
    status: str = "unknown"
    summary: str = ""
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "status": self.status,
            "summary": self.summary,
            "dimensions": [dimension.to_dict() for dimension in self.dimensions],
            "recommendations": list(self.recommendations),
        }


class HealthModel:
    """Combine timeline metrics into a single health snapshot."""

    def assess(
        self,
        timeline: list[MetricPoint],
        trends: dict[str, TrendAnalysis] | None = None,
    ) -> UnifiedHealth:
        trends = trends or {}
        if not timeline:
            return UnifiedHealth(score=0.0, status="unknown", summary="No timeline data available.")

        latest = timeline[-1]
        cc_trend = trends.get("cc_mean")
        critical_trend = trends.get("critical_count")
        lines_trend = trends.get("total_lines")

        cc_score = self._bounded_score(1.0 - latest.avg_cc / 25.0)
        critical_score = self._bounded_score(1.0 - latest.critical_count / 12.0)
        size_score = self._bounded_score(1.0 - latest.total_lines / 5000.0)
        validation_score = self._bounded_score(1.0 - latest.validation_issues / 20.0)

        dimensions = [
            HealthDimension(
                name="complexity",
                score=cc_score,
                trend=(cc_trend.trend if cc_trend else "unknown"),
                weight=0.35,
                evidence=[f"avg_cc={latest.avg_cc:.2f}"],
            ),
            HealthDimension(
                name="criticality",
                score=critical_score,
                trend=(critical_trend.trend if critical_trend else "unknown"),
                weight=0.30,
                evidence=[f"critical_count={latest.critical_count}"],
            ),
            HealthDimension(
                name="size",
                score=size_score,
                trend=(lines_trend.trend if lines_trend else "unknown"),
                weight=0.15,
                evidence=[f"total_lines={latest.total_lines}"],
            ),
            HealthDimension(
                name="validation",
                score=validation_score,
                trend=(trends.get("validation_issues").trend if trends.get("validation_issues") else "unknown"),
                weight=0.20,
                evidence=[f"validation_issues={latest.validation_issues}"],
            ),
        ]

        score = sum(d.score * d.weight for d in dimensions) / sum(d.weight for d in dimensions)
        status = self._status_for_score(score)
        recommendations = self._recommendations(latest, trends)
        summary = (
            f"health={score:.2f} status={status} "
            f"cc={latest.avg_cc:.2f} critical={latest.critical_count} lines={latest.total_lines}"
        )
        return UnifiedHealth(
            score=round(score, 3),
            dimensions=dimensions,
            status=status,
            summary=summary,
            recommendations=recommendations,
        )

    @staticmethod
    def _bounded_score(value: float) -> float:
        return round(max(0.0, min(1.0, value)), 3)

    @staticmethod
    def _status_for_score(score: float) -> str:
        if score >= 0.85:
            return "healthy"
        if score >= 0.65:
            return "watch"
        if score >= 0.40:
            return "degraded"
        return "critical"

    @staticmethod
    def _recommendations(
        latest: MetricPoint,
        trends: dict[str, TrendAnalysis],
    ) -> list[str]:
        recommendations: list[str] = []
        if latest.avg_cc >= 15:
            recommendations.append("Split high-complexity functions")
        if latest.critical_count >= 5:
            recommendations.append("Prioritize critical hotspots")
        if latest.validation_issues > 0:
            recommendations.append("Address validation issues")
        cc_trend = trends.get("cc_mean")
        if cc_trend and cc_trend.trend == "degrading":
            recommendations.append("Trend is degrading; intervene proactively")
        return recommendations


__all__ = ["HealthDimension", "UnifiedHealth", "HealthModel"]
