"""Predictive refactoring and proactive alerts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .git_timeline import GitTimelineAnalyzer, MetricPoint, TrendAnalysis
from .health_model import HealthModel, UnifiedHealth


@dataclass(slots=True)
class ProactiveAlert:
    """A proactive issue detected from trends."""

    title: str
    severity: str
    reason: str
    metric_name: str
    current_value: float
    predicted_value: float
    commit_hash: str = ""
    recommended_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "severity": self.severity,
            "reason": self.reason,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "predicted_value": self.predicted_value,
            "commit_hash": self.commit_hash,
            "recommended_actions": list(self.recommended_actions),
        }


class ProactiveAnalyzer:
    """Turn trend forecasts into alerts and suggested interventions."""

    _SEVERITY_RANK = {"critical": 3, "high": 2, "medium": 1, "low": 0}

    def __init__(self, health_model: HealthModel | None = None) -> None:
        self.health_model = health_model or HealthModel()

    def analyze(
        self,
        timeline: list[MetricPoint],
        trends: dict[str, TrendAnalysis] | None = None,
        health: UnifiedHealth | None = None,
    ) -> list[ProactiveAlert]:
        if not timeline:
            return []

        trends = trends or {}
        health = health or self.health_model.assess(timeline, trends)
        latest = timeline[-1]
        alerts: list[ProactiveAlert] = []

        for metric_name in ("cc_mean", "critical_count", "validation_issues", "total_lines"):
            trend = trends.get(metric_name)
            if trend is None:
                continue
            alert = self._trend_alert(metric_name, trend, latest, health)
            if alert is not None:
                alerts.append(alert)

        alerts.sort(
            key=lambda item: (
                self._SEVERITY_RANK.get(item.severity, -1),
                item.predicted_value,
            ),
            reverse=True,
        )
        return alerts

    def predict_future_state(
        self,
        project_path: str | None = None,
        analyzer: GitTimelineAnalyzer | None = None,
        depth: int = 20,
    ) -> dict[str, Any]:
        if analyzer is None:
            if project_path is None:
                raise ValueError("project_path or analyzer must be provided")
            analyzer = GitTimelineAnalyzer(project_path=project_path, depth=depth)

        timeline = analyzer.build_timeline(depth=depth)
        trends = analyzer.predict_future_state(horizon=1, timeline=timeline)
        health = self.health_model.assess(timeline, trends)
        alerts = self.analyze(timeline, trends, health)
        return {
            "timeline": [point.to_dict() for point in timeline],
            "trends": {name: trend.to_dict() for name, trend in trends.items()},
            "health": health.to_dict(),
            "alerts": [alert.to_dict() for alert in alerts],
        }

    @staticmethod
    def _trend_alert(
        metric_name: str,
        trend: TrendAnalysis,
        latest: MetricPoint,
        health: UnifiedHealth,
    ) -> ProactiveAlert | None:
        if trend.trend not in {"degrading", "unknown"}:
            return None

        severity = "high" if trend.predicted_value > trend.current_value else "medium"
        if metric_name == "cc_mean" and latest.avg_cc >= 15:
            severity = "critical"

        reason = (
            f"{metric_name} is {trend.trend}; current={trend.current_value:.2f}, "
            f"predicted={trend.predicted_value:.2f}, health={health.status}"
        )
        recommendations = [
            "Review recent commits for complexity spikes",
            "Prioritize the hottest files first",
        ]
        if metric_name == "validation_issues":
            recommendations.insert(0, "Run validation bridges before applying new changes")
        if metric_name == "cc_mean":
            recommendations.insert(0, "Schedule predictive refactoring before the next cycle")

        return ProactiveAlert(
            title=f"{metric_name} degradation risk",
            severity=severity,
            reason=reason,
            metric_name=metric_name,
            current_value=trend.current_value,
            predicted_value=trend.predicted_value,
            commit_hash=latest.commit_hash,
            recommended_actions=recommendations,
        )


__all__ = ["ProactiveAlert", "ProactiveAnalyzer"]
