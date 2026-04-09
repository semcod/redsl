"""Tests for the batch pyqual multi-project orchestrator."""

from __future__ import annotations

from pathlib import Path

from redsl.commands.batch_pyqual import (
    PyqualProjectResult,
    _find_packages,
    _filter_packages,
    _build_summary,
    _compute_verdict,
    _process_project,
    _PYQUAL_YAML_TEMPLATE,
    _resolve_profile,
    _save_report,
    run_pyqual_batch,
)


def test_find_packages_finds_real_packages(tmp_path: Path) -> None:
    """Packages with pyproject.toml are detected."""
    pkg_a = tmp_path / "alpha"
    pkg_a.mkdir()
    (pkg_a / "pyproject.toml").write_text("[project]\nname='alpha'\n")

    pkg_b = tmp_path / "beta"
    pkg_b.mkdir()
    (pkg_b / "setup.py").write_text("# setup\n")

    # Not a package — no marker
    plain = tmp_path / "plain"
    plain.mkdir()

    # Skipped dirs
    venv = tmp_path / "venv"
    venv.mkdir()
    (venv / "pyproject.toml").write_text("[project]\n")

    hidden = tmp_path / ".hidden"
    hidden.mkdir()
    (hidden / "pyproject.toml").write_text("[project]\n")

    found = _find_packages(tmp_path)
    names = [p.name for p in found]
    assert "alpha" in names
    assert "beta" in names
    assert "plain" not in names
    assert "venv" not in names
    assert ".hidden" not in names


def test_filter_packages_supports_include_and_exclude(tmp_path: Path) -> None:
    alpha = tmp_path / "alpha"
    alpha.mkdir()
    (alpha / "pyproject.toml").write_text("[project]\nname='alpha'\n")

    beta = tmp_path / "beta-service"
    beta.mkdir()
    (beta / "pyproject.toml").write_text("[project]\nname='beta-service'\n")

    gamma = tmp_path / "gamma"
    gamma.mkdir()
    (gamma / "pyproject.toml").write_text("[project]\nname='gamma'\n")

    packages = _find_packages(tmp_path)
    filtered = _filter_packages(packages, include=("b*", "gamma"), exclude=("gamma",))
    assert [pkg.name for pkg in filtered] == ["beta-service"]


def test_build_summary_aggregates_correctly() -> None:
    r1 = PyqualProjectResult(name="a", path="/a", py_files=10, total_loc=500, avg_cc=5.0, gates_passed=True, gates_total=3, gates_passing=3, verdict="success")
    r2 = PyqualProjectResult(name="b", path="/b", py_files=20, total_loc=1200, avg_cc=8.0, redsl_fixes_applied=4, gates_passed=False, gates_total=3, gates_passing=2, verdict="failed")

    summary = _build_summary([r1, r2])
    assert summary["projects_processed"] == 2
    assert summary["projects_success"] == 1
    assert summary["projects_failed"] == 1
    assert summary["batch_verdict"] == "failed"
    assert summary["projects_config_valid"] == 2
    assert summary["total_redsl_fixes"] == 4
    assert summary["total_py_files"] == 30
    assert summary["total_loc"] == 1700
    assert summary["projects_gates_passed"] == 1
    assert summary["total_gates_passing"] == 5
    assert summary["total_gates_total"] == 6


def test_resolve_profile_prefers_publish_when_auto() -> None:
    assert _resolve_profile("auto", run_pipeline=False, publish=True) == "python-publish"


def test_resolve_profile_defaults_to_python_when_pipeline_requested() -> None:
    assert _resolve_profile("auto", run_pipeline=True, publish=False) == "python"


def test_compute_verdict_returns_ready_for_dry_run_success() -> None:
    result = PyqualProjectResult(
        name="x",
        path="/x",
        config_valid=True,
        gates_passed=True,
        pipeline_passed=True,
        push_preflight_passed=True,
        dry_run=True,
    )
    verdict, reasons = _compute_verdict(result, require_pipeline=True, require_push=True)
    assert verdict == "ready"
    assert reasons == []


def test_compute_verdict_fails_when_dry_run_push_preflight_fails() -> None:
    result = PyqualProjectResult(
        name="x",
        path="/x",
        config_valid=True,
        gates_passed=True,
        pipeline_passed=True,
        push_preflight_passed=False,
        dry_run=True,
    )
    verdict, reasons = _compute_verdict(result, require_pipeline=True, require_push=True)
    assert verdict == "failed"
    assert reasons == ["push-preflight"]


def test_process_project_skips_dirty_repo_when_requested(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "dirty-project"
    project.mkdir()
    (project / "pyproject.toml").write_text("[project]\nname='dirty-project'\n")

    monkeypatch.setattr("redsl.commands.batch_pyqual._git_status_lines", lambda project: [" M app.py"])

    result = _process_project(project, skip_dirty=True)

    assert result.skipped is True
    assert result.skip_reason.startswith("dirty-repo")
    assert result.verdict == "skipped"
    assert result.verdict_reasons == [result.skip_reason]


def test_run_pyqual_batch_stops_on_fail_fast(tmp_path: Path, monkeypatch) -> None:
    pkg_a = tmp_path / "alpha"
    pkg_b = tmp_path / "beta"
    pkg_a.mkdir()
    pkg_b.mkdir()

    monkeypatch.setattr("redsl.commands.batch_pyqual._find_packages", lambda workspace_root: [pkg_a, pkg_b])
    monkeypatch.setattr("redsl.commands.batch_pyqual._filter_packages", lambda packages, include=None, exclude=None: packages)
    monkeypatch.setattr("redsl.commands.batch_pyqual._print_summary", lambda summary: None)
    monkeypatch.setattr("redsl.commands.batch_pyqual._save_report", lambda results, summary, workspace_root: None)

    seen: list[str] = []

    def fake_process_project(
        project: Path,
        max_fixes: int = 30,
        run_pipeline: bool = False,
        git_push: bool = False,
        profile: str = "python",
        publish: bool = False,
        fix_config: bool = False,
        dry_run: bool = False,
        skip_dirty: bool = False,
    ) -> PyqualProjectResult:
        seen.append(project.name)
        if project.name == "alpha":
            return PyqualProjectResult(name="alpha", path=str(project), verdict="failed", config_valid=False)
        return PyqualProjectResult(name="beta", path=str(project), verdict="success", gates_passed=True, config_valid=True)

    monkeypatch.setattr("redsl.commands.batch_pyqual._process_project", fake_process_project)

    summary = run_pyqual_batch(tmp_path, fail_fast=True)

    assert seen == ["alpha"]
    assert summary["projects_processed"] == 1
    assert summary["projects_failed"] == 1
    assert summary["batch_verdict"] == "failed"


def test_run_pyqual_batch_smoke_with_mocked_project_flow(tmp_path: Path, monkeypatch) -> None:
    pkg_a = tmp_path / "alpha"
    pkg_b = tmp_path / "beta"
    pkg_a.mkdir()
    pkg_b.mkdir()

    monkeypatch.setattr("redsl.commands.batch_pyqual._find_packages", lambda workspace_root: [pkg_a, pkg_b])
    monkeypatch.setattr("redsl.commands.batch_pyqual._filter_packages", lambda packages, include=None, exclude=None: packages)
    monkeypatch.setattr("redsl.commands.batch_pyqual._pyqual_cli_available", lambda: True)
    monkeypatch.setattr("redsl.commands.batch_pyqual._print_summary", lambda summary: None)

    calls: list[dict[str, object]] = []

    def fake_process_project(
        project: Path,
        max_fixes: int = 30,
        run_pipeline: bool = False,
        git_push: bool = False,
        profile: str = "python",
        publish: bool = False,
        fix_config: bool = False,
        dry_run: bool = False,
        skip_dirty: bool = False,
    ) -> PyqualProjectResult:
        calls.append(
            {
                "name": project.name,
                "max_fixes": max_fixes,
                "run_pipeline": run_pipeline,
                "git_push": git_push,
                "profile": profile,
                "publish": publish,
                "fix_config": fix_config,
                "dry_run": dry_run,
                "skip_dirty": skip_dirty,
            }
        )
        if project.name == "alpha":
            return PyqualProjectResult(
                name="alpha",
                path=str(project),
                pyqual_available=True,
                pyqual_yaml_generated=True,
                profile_used=profile,
                config_valid=True,
                config_fixed=True,
                publish_requested=publish,
                publish_configured=True,
                redsl_fixes_applied=2,
                gates_passed=True,
                gates_total=3,
                gates_passing=3,
                pipeline_ran=True,
                pipeline_passed=True,
                pipeline_push_passed=True,
                pipeline_publish_passed=True,
                push_preflight_passed=True,
                dry_run=dry_run,
                verdict="ready",
            )
        return PyqualProjectResult(
            name="beta",
            path=str(project),
            pyqual_available=True,
            publish_requested=publish,
            dry_run=dry_run,
            skipped=True,
            skip_reason="dirty-repo (2 changes)",
            dirty_before=True,
            dirty_entries_before=2,
            verdict="skipped",
            verdict_reasons=["dirty-repo (2 changes)"],
        )

    monkeypatch.setattr("redsl.commands.batch_pyqual._process_project", fake_process_project)

    summary = run_pyqual_batch(
        tmp_path,
        max_fixes=7,
        run_pipeline=True,
        git_push=True,
        publish=True,
        fix_config=True,
        dry_run=True,
        skip_dirty=True,
    )

    assert [call["name"] for call in calls] == ["alpha", "beta"]
    assert all(call["max_fixes"] == 7 for call in calls)
    assert all(call["run_pipeline"] is True for call in calls)
    assert all(call["git_push"] is True for call in calls)
    assert all(call["profile"] == "python-publish" for call in calls)
    assert all(call["publish"] is True for call in calls)
    assert all(call["fix_config"] is True for call in calls)
    assert all(call["dry_run"] is True for call in calls)
    assert all(call["skip_dirty"] is True for call in calls)

    assert summary["projects_processed"] == 2
    assert summary["projects_ready"] == 1
    assert summary["projects_skipped"] == 1
    assert summary["projects_failed"] == 0
    assert summary["projects_push_preflight_passed"] == 1
    assert summary["projects_publish_ready"] == 1
    assert summary["projects_publish_passed"] == 1
    assert summary["batch_verdict"] == "ready"

    report = (tmp_path / "redsl_pyqual_report.md").read_text(encoding="utf-8")
    assert "Batch verdict: **ready**" in report
    assert "| 1 | `alpha` |" in report
    assert "| 2 | `beta` |" in report
    assert "- verdict reasons: dirty-repo (2 changes)" in report


def test_save_report_includes_project_notes_for_verdict_reasons_and_errors(tmp_path: Path) -> None:
    result = PyqualProjectResult(
        name="alpha",
        path="/alpha",
        verdict="skipped",
        verdict_reasons=["dirty-repo (2 changes)"],
        errors=["Push skipped: repository had local changes before batch run"],
    )
    summary = _build_summary([result])

    _save_report([result], summary, tmp_path)

    content = (tmp_path / "redsl_pyqual_report.md").read_text(encoding="utf-8")
    assert "## Project Notes" in content
    assert "### alpha" in content
    assert "- verdict: skipped" in content
    assert "- verdict reasons: dirty-repo (2 changes)" in content
    assert "- error: Push skipped: repository had local changes before batch run" in content


def test_pyqual_yaml_template_is_valid_yaml() -> None:
    import yaml
    data = yaml.safe_load(_PYQUAL_YAML_TEMPLATE.format(name="test-project"))
    assert data["pipeline"]["name"] == "quality-loop-test-project"
    assert "metrics" in data["pipeline"]
    assert "stages" in data["pipeline"]


def test_pyqual_project_result_defaults() -> None:
    r = PyqualProjectResult(name="x", path="/x")
    assert r.gates_passed is False
    assert r.pipeline_ran is False
    assert r.git_committed is False
    assert r.redsl_fixes_applied == 0
