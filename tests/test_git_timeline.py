from __future__ import annotations

from pathlib import Path

from redsl.awareness.git_timeline import GitTimelineAnalyzer, MetricPoint


def test_toon_candidate_priority_classifies_known_categories(tmp_path):
    analyzer = GitTimelineAnalyzer(tmp_path)

    assert analyzer._toon_candidate_priority("project_toon.yaml")[0] == 0
    assert analyzer._toon_candidate_priority("analysis.toon.yaml")[0] == 0
    assert analyzer._toon_candidate_priority("duplication.toon.yaml")[0] == 3
    assert analyzer._toon_candidate_priority("validation.toon.yaml")[0] == 4
    assert analyzer._toon_candidate_priority("notes.txt")[0] == 6


def test_analyze_trends_preserves_cc_alias(tmp_path):
    analyzer = GitTimelineAnalyzer(tmp_path)
    timeline = [
        MetricPoint(
            commit_hash="a1",
            timestamp="2026-04-08T00:00:00+00:00",
            avg_cc=1.0,
            critical_count=0,
            total_lines=10,
            total_files=1,
        ),
        MetricPoint(
            commit_hash="b2",
            timestamp="2026-04-08T01:00:00+00:00",
            avg_cc=3.0,
            critical_count=1,
            total_lines=20,
            total_files=2,
        ),
    ]

    trends = analyzer.analyze_trends(timeline)

    assert "cc_mean" in trends
    assert "avg_cc" in trends
    assert trends["avg_cc"] is trends["cc_mean"]
    assert trends["cc_mean"].trend == "degrading"
    assert trends["cc_mean"].predicted_value >= trends["cc_mean"].current_value


def test_build_timeline_graceful_fallback_without_git(tmp_path):
    analyzer = GitTimelineAnalyzer(tmp_path)

    assert analyzer.build_timeline(depth=5) == []


def test_find_degradation_sources_returns_largest_jump_first(tmp_path):
    analyzer = GitTimelineAnalyzer(tmp_path)
    timeline = [
        MetricPoint(
            commit_hash="a1",
            timestamp="2026-04-08T00:00:00+00:00",
            avg_cc=1.0,
            critical_count=0,
            total_lines=10,
            total_files=1,
        ),
        MetricPoint(
            commit_hash="b2",
            timestamp="2026-04-08T01:00:00+00:00",
            avg_cc=4.0,
            critical_count=1,
            total_lines=20,
            total_files=2,
        ),
        MetricPoint(
            commit_hash="c3",
            timestamp="2026-04-08T02:00:00+00:00",
            avg_cc=10.0,
            critical_count=2,
            total_lines=40,
            total_files=3,
        ),
    ]

    sources = analyzer.find_degradation_sources(timeline)

    assert sources[0]["commit_hash"] == "c3"
    assert sources[0]["metric_deltas"]["cc_mean"] == 6.0
    assert sources[0]["degradation_score"] >= sources[-1]["degradation_score"]


def test_predict_future_state_returns_degrading_prediction(tmp_path):
    analyzer = GitTimelineAnalyzer(tmp_path)
    timeline = [
        MetricPoint(
            commit_hash="a1",
            timestamp="2026-04-08T00:00:00+00:00",
            avg_cc=1.0,
            critical_count=0,
            total_lines=10,
            total_files=1,
        ),
        MetricPoint(
            commit_hash="b2",
            timestamp="2026-04-08T01:00:00+00:00",
            avg_cc=3.0,
            critical_count=1,
            total_lines=20,
            total_files=2,
        ),
    ]

    predictions = analyzer.predict_future_state(horizon=2, timeline=timeline)

    assert predictions["cc_mean"].trend == "degrading"
    assert predictions["cc_mean"].predicted > predictions["cc_mean"].current
