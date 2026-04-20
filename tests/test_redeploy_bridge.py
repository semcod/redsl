"""Tests for redsl.bridges.redeploy_bridge.

Unit tests use mocks so they run without redeploy installed.
Integration tests (marked @pytest.mark.integration) require redeploy installed.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from redsl.bridges import redeploy_bridge


# ── helpers ───────────────────────────────────────────────────────────────────

def _fake_redeploy_modules(**overrides):
    """Build a sys.modules patch dict that stubs out the redeploy package."""
    base = {
        "redeploy": MagicMock(),
        "redeploy.detect": MagicMock(),
        "redeploy.plan": MagicMock(),
        "redeploy.apply": MagicMock(),
        "redeploy.models": MagicMock(),
    }
    base.update(overrides)
    return base


def _make_state(strategy="docker_full", version="1.2.3", conflicts=None):
    s = MagicMock()
    s.detected_strategy.value = strategy
    s.current_version = version
    s.conflicts = conflicts or []
    s.model_dump.return_value = {"host": "local", "app": "app"}
    return s


def _make_migration(from_s="k3s", to_s="docker_full", n_steps=2):
    m = MagicMock()
    m.risk.value = "low"
    m.estimated_downtime = "~30s"
    m.steps = [MagicMock() for _ in range(n_steps)]
    m.from_strategy.value = from_s
    m.to_strategy.value = to_s
    m.notes = []
    m.model_dump.return_value = {
        "from_strategy": from_s, "to_strategy": to_s,
        "risk": "low", "steps": [], "notes": [],
    }
    return m


def _make_executor(ok=True):
    step = MagicMock()
    step.id = "docker_compose_up"
    step.status.value = "done"
    step.result = "ok"
    step.error = None

    ex = MagicMock()
    ex.plan.steps = [step]
    ex.run.return_value = ok
    ex.summary.return_value = "✅ 1/1 steps completed"
    return ex


# ── availability ──────────────────────────────────────────────────────────────

class TestRedeployBridgeAvailability:
    def test_is_available_returns_bool(self):
        assert isinstance(redeploy_bridge.is_available(), bool)

    def test_is_available_cached(self):
        assert redeploy_bridge.is_available() == redeploy_bridge.is_available()

    def test_unavailable_detect_returns_error(self):
        with patch("redsl.bridges.redeploy_bridge.is_available", return_value=False):
            r = redeploy_bridge.detect("local")
        assert r["available"] is False
        assert "error" in r

    def test_unavailable_plan_returns_error(self, tmp_path):
        with patch("redsl.bridges.redeploy_bridge.is_available", return_value=False):
            r = redeploy_bridge.plan(tmp_path / "infra.yaml")
        assert r["available"] is False and "error" in r

    def test_unavailable_apply_returns_error(self, tmp_path):
        with patch("redsl.bridges.redeploy_bridge.is_available", return_value=False):
            r = redeploy_bridge.apply(tmp_path / "plan.yaml")
        assert r["available"] is False and "error" in r

    def test_unavailable_run_spec_returns_error(self, tmp_path):
        with patch("redsl.bridges.redeploy_bridge.is_available", return_value=False):
            r = redeploy_bridge.run_spec(tmp_path / "spec.yaml")
        assert r["available"] is False and "error" in r

    def test_unavailable_migrate_returns_error(self):
        with patch("redsl.bridges.redeploy_bridge.is_available", return_value=False):
            r = redeploy_bridge.migrate("local")
        assert r["available"] is False and "error" in r


# ── detect (mocked) ───────────────────────────────────────────────────────────

class TestRedeployDetectMocked:
    def test_detect_returns_strategy(self):
        state = _make_state()
        mods = _fake_redeploy_modules()
        mods["redeploy.detect"].Detector.return_value.run.return_value = state

        with patch("redsl.bridges.redeploy_bridge.is_available", return_value=True), \
             patch.dict(sys.modules, mods):
            r = redeploy_bridge.detect("local", app="myapp")

        assert r["available"] is True
        assert r["strategy"] == "docker_full"
        assert r["version"] == "1.2.3"
        assert r["conflicts"] == []

    def test_detect_and_save_returns_saved_to(self, tmp_path):
        state = _make_state()
        mods = _fake_redeploy_modules()
        mods["redeploy.detect"].Detector.return_value.run.return_value = state
        out = tmp_path / "infra.yaml"

        with patch("redsl.bridges.redeploy_bridge.is_available", return_value=True), \
             patch.dict(sys.modules, mods):
            r = redeploy_bridge.detect_and_save("local", output=out)

        assert r["available"] is True
        assert r["saved_to"] == str(out)

    def test_detect_handles_connection_error(self):
        mods = _fake_redeploy_modules()
        mods["redeploy.detect"].Detector.return_value.run.side_effect = ConnectionError("unreachable")

        with patch("redsl.bridges.redeploy_bridge.is_available", return_value=True), \
             patch.dict(sys.modules, mods):
            r = redeploy_bridge.detect("bad-host")

        assert "error" in r
        assert "unreachable" in r["error"]


# ── plan (mocked) ─────────────────────────────────────────────────────────────

class TestRedeployPlanMocked:
    def test_plan_returns_steps_and_risk(self, tmp_path):
        infra = tmp_path / "infra.yaml"
        infra.write_text("host: local\napp: app\n")
        migration = _make_migration(n_steps=2)
        mods = _fake_redeploy_modules()
        mods["redeploy.plan"].Planner.from_files.return_value.run.return_value = migration

        with patch("redsl.bridges.redeploy_bridge.is_available", return_value=True), \
             patch.dict(sys.modules, mods):
            r = redeploy_bridge.plan(infra)

        assert r["available"] is True
        assert r["steps"] == 2
        assert r["risk"] == "low"

    def test_plan_from_spec_returns_strategies(self, tmp_path):
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text("name: test\nsource:\n  host: local\ntarget:\n  host: local\n")
        migration = _make_migration()
        mods = _fake_redeploy_modules()
        mods["redeploy.models"].MigrationSpec.from_file.return_value = MagicMock()
        mods["redeploy.plan"].Planner.from_spec.return_value.run.return_value = migration

        with patch("redsl.bridges.redeploy_bridge.is_available", return_value=True), \
             patch.dict(sys.modules, mods):
            r = redeploy_bridge.plan_from_spec(spec_file)

        assert r["available"] is True
        assert r["from_strategy"] == "k3s"
        assert r["to_strategy"] == "docker_full"

    def test_plan_and_save_returns_saved_to(self, tmp_path):
        infra = tmp_path / "infra.yaml"
        infra.write_text("host: local\napp: app\n")
        out = tmp_path / "plan.yaml"
        migration = _make_migration()
        mods = _fake_redeploy_modules()
        mods["redeploy.plan"].Planner.from_files.return_value.run.return_value = migration

        with patch("redsl.bridges.redeploy_bridge.is_available", return_value=True), \
             patch.dict(sys.modules, mods):
            r = redeploy_bridge.plan_and_save(infra, out)

        assert r["available"] is True
        assert r["saved_to"] == str(out)


# ── apply (mocked) ────────────────────────────────────────────────────────────

class TestRedeployApplyMocked:
    def _mods_with_executor(self, ok=True):
        ex = _make_executor(ok=ok)
        mods = _fake_redeploy_modules()
        mods["redeploy.apply"].Executor.from_file.return_value = ex
        return mods, ex

    def test_apply_dry_run_returns_ok_true(self, tmp_path):
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("host: local\napp: app\n")
        mods, _ = self._mods_with_executor(ok=True)

        with patch("redsl.bridges.redeploy_bridge.is_available", return_value=True), \
             patch.dict(sys.modules, mods):
            r = redeploy_bridge.apply(plan_file, dry_run=True)

        assert r["available"] is True
        assert r["ok"] is True
        assert r["dry_run"] is True

    def test_apply_failed_returns_ok_false(self, tmp_path):
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("host: local\napp: app\n")
        mods, _ = self._mods_with_executor(ok=False)

        with patch("redsl.bridges.redeploy_bridge.is_available", return_value=True), \
             patch.dict(sys.modules, mods):
            r = redeploy_bridge.apply(plan_file)

        assert r["available"] is True
        assert r["ok"] is False

    def test_apply_step_filter_missing_id(self, tmp_path):
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("host: local\napp: app\n")
        mods, _ = self._mods_with_executor()

        with patch("redsl.bridges.redeploy_bridge.is_available", return_value=True), \
             patch.dict(sys.modules, mods):
            r = redeploy_bridge.apply(plan_file, step_id="nonexistent")

        assert "error" in r
        assert "nonexistent" in r["error"]

    def test_apply_results_structure(self, tmp_path):
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("host: local\napp: app\n")
        mods, _ = self._mods_with_executor(ok=True)

        with patch("redsl.bridges.redeploy_bridge.is_available", return_value=True), \
             patch.dict(sys.modules, mods):
            r = redeploy_bridge.apply(plan_file)

        assert isinstance(r["results"], list)
        assert r["results"][0]["id"] == "docker_compose_up"


# ── run_spec (mocked) ─────────────────────────────────────────────────────────

class TestRedeployRunSpecMocked:
    def test_run_spec_plan_only(self, tmp_path):
        spec = tmp_path / "spec.yaml"
        spec.write_text("name: t\nsource:\n  host: local\ntarget:\n  host: local\n")
        migration = _make_migration(n_steps=0)
        mods = _fake_redeploy_modules()
        mods["redeploy.models"].MigrationSpec.from_file.return_value = MagicMock()
        mods["redeploy.plan"].Planner.from_spec.return_value.run.return_value = migration

        with patch("redsl.bridges.redeploy_bridge.is_available", return_value=True), \
             patch.dict(sys.modules, mods):
            r = redeploy_bridge.run_spec(spec, plan_only=True)

        assert r["available"] is True
        assert r["plan_only"] is True
        assert r["ok"] is True

    def test_run_spec_full_ok(self, tmp_path):
        spec = tmp_path / "spec.yaml"
        spec.write_text("name: t\nsource:\n  host: local\ntarget:\n  host: local\n")
        migration = _make_migration()
        mods = _fake_redeploy_modules()
        mods["redeploy.models"].MigrationSpec.from_file.return_value = MagicMock()
        mods["redeploy.plan"].Planner.from_spec.return_value.run.return_value = migration
        ex = _make_executor(ok=True)
        mods["redeploy.apply"].Executor.return_value = ex

        with patch("redsl.bridges.redeploy_bridge.is_available", return_value=True), \
             patch.dict(sys.modules, mods):
            r = redeploy_bridge.run_spec(spec, dry_run=True)

        assert r["available"] is True
        assert r["ok"] is True


# ── CLI ───────────────────────────────────────────────────────────────────────

class TestDeployCLI:
    def test_deploy_group_registered(self):
        from click.testing import CliRunner
        from redsl.cli import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["deploy", "--help"])
        assert result.exit_code == 0
        for cmd in ("detect", "plan", "apply", "run", "migrate"):
            assert cmd in result.output

    def test_deploy_detect_help(self):
        from click.testing import CliRunner
        from redsl.cli import cli
        result = CliRunner().invoke(cli, ["deploy", "detect", "--help"])
        assert result.exit_code == 0
        assert "HOST" in result.output

    def test_deploy_plan_help(self):
        from click.testing import CliRunner
        from redsl.cli import cli
        result = CliRunner().invoke(cli, ["deploy", "plan", "--help"])
        assert result.exit_code == 0
        assert "--infra" in result.output

    def test_deploy_apply_help(self):
        from click.testing import CliRunner
        from redsl.cli import cli
        result = CliRunner().invoke(cli, ["deploy", "apply", "--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.output

    def test_deploy_run_help(self):
        from click.testing import CliRunner
        from redsl.cli import cli
        result = CliRunner().invoke(cli, ["deploy", "run", "--help"])
        assert result.exit_code == 0
        assert "--plan-only" in result.output

    def test_deploy_migrate_help(self):
        from click.testing import CliRunner
        from redsl.cli import cli
        result = CliRunner().invoke(cli, ["deploy", "migrate", "--help"])
        assert result.exit_code == 0
        assert "HOST" in result.output
        assert "--strategy" in result.output

    def test_deploy_detect_without_redeploy_exits_1(self):
        from click.testing import CliRunner
        from redsl.cli import cli
        with patch("redsl.bridges.redeploy_bridge.is_available", return_value=False):
            result = CliRunner().invoke(cli, ["deploy", "detect", "local"])
        assert result.exit_code == 1
        assert "not installed" in result.output

    def test_deploy_migrate_without_redeploy_exits_1(self):
        from click.testing import CliRunner
        from redsl.cli import cli
        with patch("redsl.bridges.redeploy_bridge.is_available", return_value=False):
            result = CliRunner().invoke(cli, ["deploy", "migrate", "local"])
        assert result.exit_code == 1
        assert "not installed" in result.output
