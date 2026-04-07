"""Tests for Phase 3.4 — MultiProjectRunner."""

from __future__ import annotations

from pathlib import Path

import pytest

from redsl.commands.multi_project import (
    MultiProjectReport,
    MultiProjectRunner,
    ProjectAnalysis,
    run_multi_analysis,
)


@pytest.fixture
def two_projects(tmp_path: Path):
    p1 = tmp_path / "proj_a"
    p1.mkdir()
    (p1 / "main.py").write_text("def hello():\n    return 42\n")

    p2 = tmp_path / "proj_b"
    p2.mkdir()
    (p2 / "utils.py").write_text("x = 1\n")

    return p1, p2


class TestProjectAnalysis:
    def test_ok_when_result_present(self, tmp_path: Path):
        from redsl.analyzers import AnalysisResult
        pa = ProjectAnalysis(name="x", path=tmp_path, result=AnalysisResult())
        assert pa.ok is True

    def test_not_ok_when_error(self, tmp_path: Path):
        pa = ProjectAnalysis(name="x", path=tmp_path, error="boom")
        assert pa.ok is False

    def test_avg_cc_zero_without_result(self, tmp_path: Path):
        pa = ProjectAnalysis(name="x", path=tmp_path)
        assert pa.avg_cc == 0.0

    def test_total_files_zero_without_result(self, tmp_path: Path):
        pa = ProjectAnalysis(name="x", path=tmp_path)
        assert pa.total_files == 0


class TestMultiProjectReport:
    def _make_report(self, tmp_path: Path) -> MultiProjectReport:
        from redsl.analyzers import AnalysisResult
        r1 = AnalysisResult(avg_cc=8.0, total_files=5)
        r2 = AnalysisResult(avg_cc=4.0, total_files=3)
        pa1 = ProjectAnalysis(name="a", path=tmp_path / "a", result=r1)
        pa2 = ProjectAnalysis(name="b", path=tmp_path / "b", result=r2)
        report = MultiProjectReport()
        report.results = {"a": pa1, "b": pa2}
        return report

    def test_total_projects(self, tmp_path: Path):
        report = self._make_report(tmp_path)
        assert report.total_projects == 2

    def test_successful_count(self, tmp_path: Path):
        report = self._make_report(tmp_path)
        assert report.successful == 2

    def test_failed_count(self, tmp_path: Path):
        report = self._make_report(tmp_path)
        assert report.failed == 0

    def test_aggregate_avg_cc(self, tmp_path: Path):
        report = self._make_report(tmp_path)
        assert report.aggregate_avg_cc == pytest.approx(6.0, abs=0.1)

    def test_aggregate_files(self, tmp_path: Path):
        report = self._make_report(tmp_path)
        assert report.aggregate_files == 8

    def test_worst_projects_sorted(self, tmp_path: Path):
        report = self._make_report(tmp_path)
        worst = report.worst_projects(2)
        assert worst[0].avg_cc >= worst[1].avg_cc

    def test_to_dict_structure(self, tmp_path: Path):
        report = self._make_report(tmp_path)
        d = report.to_dict()
        assert "total_projects" in d
        assert "aggregate_avg_cc" in d
        assert "projects" in d
        assert "a" in d["projects"]

    def test_summary_contains_stats(self, tmp_path: Path):
        report = self._make_report(tmp_path)
        summary = report.summary()
        assert "2/2" in summary or "ok" in summary.lower()


class TestMultiProjectRunnerAnalyze:
    def test_analyze_existing_projects(self, two_projects):
        p1, p2 = two_projects
        runner = MultiProjectRunner()
        report = runner.analyze([p1, p2])
        assert report.total_projects == 2
        assert report.successful == 2

    def test_analyze_missing_dir_records_error(self, tmp_path: Path):
        runner = MultiProjectRunner()
        missing = tmp_path / "does_not_exist"
        report = runner.analyze([missing])
        assert report.failed == 1
        assert report.results["does_not_exist"].error is not None

    def test_analyze_empty_list(self):
        runner = MultiProjectRunner()
        report = runner.analyze([])
        assert report.total_projects == 0
        assert report.aggregate_avg_cc == 0.0

    def test_analyze_from_paths_strings(self, two_projects):
        p1, p2 = two_projects
        runner = MultiProjectRunner()
        report = runner.analyze_from_paths([str(p1), str(p2)])
        assert report.successful == 2

    def test_fail_fast_stops_after_first_error(self, tmp_path: Path):
        bad = tmp_path / "no_such_dir"
        good = tmp_path / "good"
        good.mkdir()
        (good / "a.py").write_text("x = 1")

        runner = MultiProjectRunner()
        report = runner.analyze([bad, good], fail_fast=True)
        assert report.total_projects == 1  # stopped after bad

    def test_rank_by_avg_cc(self, two_projects):
        p1, p2 = two_projects
        runner = MultiProjectRunner()
        report = runner.analyze([p1, p2])
        ranked = runner.rank_by_priority(report, key="avg_cc")
        if len(ranked) >= 2:
            assert ranked[0].avg_cc >= ranked[1].avg_cc


class TestRunMultiAnalysisHelper:
    def test_convenience_function(self, two_projects):
        p1, p2 = two_projects
        report = run_multi_analysis([p1, p2])
        assert report.total_projects == 2
        assert isinstance(report.summary(), str)
