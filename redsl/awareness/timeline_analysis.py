"""Trend analysis and prediction for git timeline data."""

from __future__ import annotations

from statistics import mean
from typing import Any, Sequence

from redsl.awareness.timeline_models import MetricPoint, TrendAnalysis, TrendState


class TimelineAnalyzer:
    """Analyzes metric trends from timeline data."""

    @staticmethod
    def analyze_trends(
        points: Sequence[MetricPoint],
        horizon: int = 1,
    ) -> dict[str, TrendAnalysis]:
        """Analyze metric trends from timeline points."""
        if not points:
            return {}

        series_map = TimelineAnalyzer._build_series_map(points)
        trends: dict[str, TrendAnalysis] = {}
        for metric_name, values in series_map.items():
            trend = TimelineAnalyzer._analyze_series(metric_name, values, horizon=horizon)
            trends[metric_name] = trend

        TimelineAnalyzer._apply_trend_aliases(trends)
        return trends

    @staticmethod
    def predict_future_state(
        points: Sequence[MetricPoint],
        horizon: int = 1,
    ) -> dict[str, TrendAnalysis]:
        """Predict the next state by extrapolating each metric trend."""
        return TimelineAnalyzer.analyze_trends(points, horizon=horizon)

    @staticmethod
    def find_degradation_sources(
        points: Sequence[MetricPoint],
    ) -> list[dict[str, Any]]:
        """Return commits with the largest negative quality jumps first."""
        if len(points) < 2:
            return []

        sources: list[dict[str, Any]] = []
        for previous, current in zip(points, points[1:]):
            delta_cc = current.avg_cc - previous.avg_cc
            delta_critical = current.critical_count - previous.critical_count
            delta_lines = current.total_lines - previous.total_lines
            delta_files = current.total_files - previous.total_files
            delta_validation = current.validation_issues - previous.validation_issues

            score = (
                max(delta_cc, 0.0) * 2.5
                + max(delta_critical, 0) * 5.0
                + max(delta_lines, 0) / 100.0
                + max(delta_files, 0) * 1.0
                + max(delta_validation, 0) * 2.0
            )
            if score <= 0:
                continue

            sources.append(
                {
                    "commit_hash": current.commit_hash,
                    "timestamp": current.timestamp,
                    "commit_message": current.commit_message,
                    "degradation_score": round(score, 3),
                    "metric_deltas": {
                        "cc_mean": round(delta_cc, 3),
                        "critical_count": int(delta_critical),
                        "total_lines": int(delta_lines),
                        "total_files": int(delta_files),
                        "validation_issues": int(delta_validation),
                    },
                }
            )

        sources.sort(key=lambda item: item["degradation_score"], reverse=True)
        return sources

    @staticmethod
    def _build_series_map(points: Sequence[MetricPoint]) -> dict[str, list[float]]:
        return {
            "cc_mean": [point.avg_cc for point in points],
            "avg_cc": [point.avg_cc for point in points],
            "critical_count": [float(point.critical_count) for point in points],
            "total_lines": [float(point.total_lines) for point in points],
            "total_files": [float(point.total_files) for point in points],
            "validation_issues": [float(point.validation_issues) for point in points],
        }

    @staticmethod
    def _apply_trend_aliases(trends: dict[str, TrendAnalysis]) -> None:
        if "cc_mean" in trends:
            trends["avg_cc"] = trends["cc_mean"]

    @staticmethod
    def _linear_regression(values: Sequence[float]) -> tuple[float, float]:
        """Return (slope, intercept) for x=0..n-1."""
        count = len(values)
        if count < 2:
            return 0.0, values[-1] if values else 0.0

        xs = list(range(count))
        x_mean = mean(xs)
        y_mean = mean(values)
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, values))
        denominator = sum((x - x_mean) ** 2 for x in xs)
        if denominator == 0:
            return 0.0, y_mean
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        return slope, intercept

    @staticmethod
    def _analyze_series(
        metric_name: str,
        values: Sequence[float],
        horizon: int = 1,
    ) -> TrendAnalysis:
        if not values:
            return TrendAnalysis(
                metric_name=metric_name,
                trend="unknown",
                slope=0.0,
                current_value=0.0,
                predicted_value=0.0,
                confidence=0.0,
                samples=0,
                history=[],
            )

        current_value = float(values[-1])
        slope, intercept = TimelineAnalyzer._linear_regression(values)
        predicted_value = max(0.0, intercept + slope * (len(values) - 1 + horizon))
        history = [float(value) for value in values]
        baseline = max(1.0, mean(abs(value) for value in history))
        normalized_slope = slope / baseline
        is_worse_when_increasing = metric_name in {"cc_mean", "avg_cc", "critical_count", "total_lines", "total_files"}
        if metric_name == "validation_issues":
            is_worse_when_increasing = True

        if len(values) < 2:
            trend: TrendState = "unknown"
        elif abs(normalized_slope) < 0.02:
            trend = "stable"
        elif normalized_slope > 0:
            trend = "degrading" if is_worse_when_increasing else "improving"
        else:
            trend = "improving" if is_worse_when_increasing else "degrading"

        confidence = min(0.99, max(0.15, abs(normalized_slope) * len(values) + 0.2))
        return TrendAnalysis(
            metric_name=metric_name,
            trend=trend,
            slope=round(slope, 4),
            current_value=round(current_value, 4),
            predicted_value=round(predicted_value, 4),
            confidence=round(confidence, 4),
            samples=len(values),
            history=[round(value, 4) for value in history],
        )


__all__ = ["TimelineAnalyzer"]
