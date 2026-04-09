from __future__ import annotations

from typing import Any

from redsl.awareness.change_patterns import ChangePatternLearner
from redsl.awareness.timeline_models import MetricPoint

from ._common import load_example_yaml, parse_scenario, print_banner


def _build_timeline(raw_points: list[dict[str, Any]]) -> list[MetricPoint]:
    """Build MetricPoint list from YAML timeline data."""
    timeline: list[MetricPoint] = []
    for idx, pt in enumerate(raw_points):
        timeline.append(MetricPoint(
            commit_hash=pt["commit_hash"],
            timestamp=pt.get("timestamp", f"2026-01-{idx + 1:02d}T00:00:00"),
            avg_cc=float(pt.get("avg_cc", 0)),
            critical_count=int(pt.get("critical_count", 0)),
            total_lines=int(pt.get("total_lines", 0)),
            duplicate_count=int(pt.get("duplicate_count", 0)),
            validation_issues=int(pt.get("validation_issues", 0)),
        ))
    return timeline


def run_awareness_example(scenario: str = "default", source: str | None = None) -> dict[str, Any]:
    data = load_example_yaml("awareness", scenario=scenario, source=source)
    display = data.get("display", {})

    print_banner(data.get("title", "ReDSL — Awareness"))

    raw_timeline = data.get("timeline", [])
    timeline = _build_timeline(raw_timeline)
    print(f"\n  Timeline: {len(timeline)} punktów")

    learner = ChangePatternLearner()
    patterns = learner.learn_from_timeline(timeline)
    print(f"  Wykryte wzorce: {len(patterns)}")

    if display.get("show_patterns"):
        print("\n  Wzorce zmian:")
        print("-" * 60)
        for i, pattern in enumerate(patterns, 1):
            print(f"\n  [{i}] {pattern.name}")
            print(f"      {pattern.description}")
            print(f"      Outcome: {pattern.outcome}")
            if display.get("show_effectiveness"):
                print(f"      Effectiveness: {pattern.effectiveness:.3f}")

    if display.get("show_signals"):
        all_signals = set()
        for p in patterns:
            all_signals.update(p.trigger_signals)
        print(f"\n  Unikalne sygnały: {sorted(all_signals)}")

        for signal in sorted(all_signals):
            matching = learner.recall_by_signal(signal)
            print(f"    {signal}: {len(matching)} wzorców")

    if display.get("show_summary"):
        summary = learner.summarize_patterns()
        degradations = sum(1 for s in summary if s["outcome"] == "degradation")
        improvements = sum(1 for s in summary if s["outcome"] == "improvement")
        print(f"\n  Podsumowanie:")
        print(f"    Degradacje:  {degradations}")
        print(f"    Poprawy:     {improvements}")
        print(f"    Łącznie:     {len(summary)}")

    print("\n" + "=" * 60)

    return {
        "scenario": data,
        "patterns": patterns,
        "timeline": timeline,
        "summary": learner.summarize_patterns(),
    }


def main(argv: list[str] | None = None) -> dict[str, Any]:
    scenario = parse_scenario(argv)
    return run_awareness_example(scenario=scenario)


if __name__ == "__main__":
    main()
