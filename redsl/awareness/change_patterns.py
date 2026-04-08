"""Change pattern learning for awareness."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .git_timeline import MetricPoint, TrendAnalysis


@dataclass(slots=True)
class ChangePattern:
    """A learned pattern describing a recurring change shape."""

    name: str
    description: str
    trigger_signals: list[str] = field(default_factory=list)
    outcome: str = "unknown"
    effectiveness: float = 0.0
    sample_count: int = 0
    evidence: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "trigger_signals": list(self.trigger_signals),
            "outcome": self.outcome,
            "effectiveness": self.effectiveness,
            "sample_count": self.sample_count,
            "evidence": list(self.evidence),
        }


class ChangePatternLearner:
    """Infer patterns from timeline deltas and trend transitions."""

    def __init__(self) -> None:
        self.patterns: list[ChangePattern] = []

    def learn_from_timeline(
        self,
        timeline: list[MetricPoint],
        trends: dict[str, TrendAnalysis] | None = None,
    ) -> list[ChangePattern]:
        if len(timeline) < 2:
            return []

        trends = trends or {}
        learned: list[ChangePattern] = []

        for previous, current in zip(timeline, timeline[1:]):
            delta_cc = current.avg_cc - previous.avg_cc
            delta_critical = current.critical_count - previous.critical_count
            delta_lines = current.total_lines - previous.total_lines
            delta_dup = current.duplicate_count - previous.duplicate_count
            delta_validation = current.validation_issues - previous.validation_issues

            signals: list[str] = []
            if delta_cc > 0:
                signals.append("cc_up")
            if delta_critical > 0:
                signals.append("critical_up")
            if delta_lines > 0:
                signals.append("size_up")
            if delta_dup > 0:
                signals.append("duplication_up")
            if delta_validation > 0:
                signals.append("validation_up")

            if not signals:
                continue

            outcome = "degradation" if delta_cc > 0 or delta_critical > 0 else "improvement"
            effectiveness = self._estimate_effectiveness(previous, current, trends)
            pattern = ChangePattern(
                name=f"{outcome}_{current.commit_hash[:7]}",
                description=(
                    f"Transition from {previous.commit_hash[:7]} to {current.commit_hash[:7]} "
                    f"changed signals: {', '.join(signals)}"
                ),
                trigger_signals=signals,
                outcome=outcome,
                effectiveness=effectiveness,
                sample_count=1,
                evidence=[
                    {
                        "from": previous.commit_hash,
                        "to": current.commit_hash,
                        "delta_cc": round(delta_cc, 3),
                        "delta_critical": delta_critical,
                        "delta_lines": delta_lines,
                        "delta_duplication": delta_dup,
                        "delta_validation": delta_validation,
                    }
                ],
            )
            learned.append(pattern)

        self.patterns.extend(learned)
        return learned

    def summarize_patterns(self) -> list[dict[str, Any]]:
        return [pattern.to_dict() for pattern in self.patterns]

    def recall_by_signal(self, signal: str) -> list[ChangePattern]:
        return [pattern for pattern in self.patterns if signal in pattern.trigger_signals]

    @staticmethod
    def _estimate_effectiveness(
        previous: MetricPoint,
        current: MetricPoint,
        trends: dict[str, TrendAnalysis],
    ) -> float:
        cc_delta = previous.avg_cc - current.avg_cc
        critical_delta = previous.critical_count - current.critical_count
        validation_delta = previous.validation_issues - current.validation_issues
        trend_bonus = 0.0
        cc_trend = trends.get("cc_mean")
        if cc_trend and cc_trend.trend == "improving":
            trend_bonus += 0.15
        return round(max(0.0, min(1.0, 0.4 + cc_delta * 0.05 + critical_delta * 0.1 + validation_delta * 0.02 + trend_bonus)), 3)


__all__ = ["ChangePattern", "ChangePatternLearner"]
