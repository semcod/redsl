"""End-to-end tests for ReDSL on real projects without mocks."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

import redsl.cli as cli_module

TEST_PROJECT_SRC = Path(__file__).parent.parent / "test_sample_project"
WORKSPACE = Path(__file__).parent.parent
pytestmark = [pytest.mark.slow, pytest.mark.e2e]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_project(tmp_path: Path) -> Path:
    """Isolated copy of test_sample_project in a temp directory."""
    if not TEST_PROJECT_SRC.exists():
        pytest.skip(f"Test project not found at {TEST_PROJECT_SRC}")
    dst = tmp_path / "project"
    shutil.copytree(TEST_PROJECT_SRC, dst, ignore=shutil.ignore_patterns("__pycache__", ".git"))
    return dst


@pytest.fixture
def git_project(test_project: Path) -> Path:
    """Isolated test project with a git repo and initial commit."""
    _init_git_repo(test_project)
    return test_project


@pytest.fixture
def runner() -> CliRunner:
    """Return Click runner for CLI testing."""
    return CliRunner()


@pytest.fixture
def api_client():
    """Return FastAPI TestClient."""
    from fastapi.testclient import TestClient
    from redsl.api import create_app
    return TestClient(create_app())


def _init_git_repo(path: Path) -> None:
    """Initialize a git repo with an initial commit."""
    subprocess.run(["git", "init"], cwd=str(path), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(path), capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=str(path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=str(path), capture_output=True)


# ===========================================================================
# CLI Refactor E2E Tests
# ===========================================================================

class TestCliRefactorE2E:
    """End-to-end tests for CLI refactor on real projects."""

    def test_refactor_dry_run_on_test_project(self, runner: CliRunner, test_project: Path) -> None:
        """Test that refactor dry-run works on real project without mocks."""
        result = runner.invoke(
            cli_module.cli,
            ["refactor", str(test_project), "--max-actions", "3", "--dry-run"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        output_lower = result.output.lower()
        assert "analysis" in output_lower or "refactor" in output_lower or "decision" in output_lower

    def test_refactor_with_regix_validation(self, runner: CliRunner, git_project: Path) -> None:
        """Test that refactor with regix validation works on real project."""
        try:
            subprocess.run(["regix", "--help"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("regix not available")

        result = runner.invoke(
            cli_module.cli,
            ["refactor", str(git_project), "--max-actions", "2", "--validate-regix", "--dry-run"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, f"Refactor with regix failed: {result.output}"

    def test_refactor_yaml_format_output(self, runner: CliRunner, test_project: Path) -> None:
        """Test that refactor --format yaml produces structured output."""
        result = runner.invoke(
            cli_module.cli,
            ["refactor", str(test_project), "--max-actions", "3", "--dry-run", "--format", "yaml"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        # YAML output should contain key structural markers
        output = result.output
        assert "decisions" in output.lower() or "actions" in output.lower() or "score" in output.lower()


# ===========================================================================
# CLI Awareness E2E Tests
# ===========================================================================

class TestCliAwarenessE2E:
    """End-to-end tests for CLI awareness commands on real projects."""

    def test_history_command_on_git_project(self, runner: CliRunner, git_project: Path) -> None:
        """Test that history command works on real project with git history."""
        result = runner.invoke(
            cli_module.cli,
            ["history", "--project", str(git_project), "--depth", "3"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, f"History failed: {result.output}"
        # History should return JSON with depth field
        import json
        payload = json.loads(result.output)
        assert "depth" in payload

    def test_ecosystem_command_on_workspace(self, runner: CliRunner) -> None:
        """Test that ecosystem command works on workspace."""
        result = runner.invoke(
            cli_module.cli,
            ["ecosystem", "--root", str(WORKSPACE)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, f"Ecosystem failed: {result.output}"
        # Ecosystem should return JSON with project_count
        import json
        payload = json.loads(result.output)
        assert "project_count" in payload


# ===========================================================================
# CLI Scan E2E Tests
# ===========================================================================

class TestCliScanE2E:
    """End-to-end tests for CLI scan command on real directories."""

    def test_scan_command_on_workspace(self, runner: CliRunner) -> None:
        """Test that scan command produces a markdown report."""
        result = runner.invoke(
            cli_module.cli,
            ["scan", str(WORKSPACE), "--quiet"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, f"Scan failed: {result.output}"
        # Scan should produce markdown with header
        assert "#" in result.output or "project" in result.output.lower()


# ===========================================================================
# Batch Processing E2E Tests
# ===========================================================================

class TestBatchE2E:
    """End-to-end tests for batch processing on real projects."""

    def test_batch_pyqual_run_on_test_project(self, runner: CliRunner, git_project: Path) -> None:
        """Test that batch pyqual-run works on real project."""
        result = runner.invoke(
            cli_module.cli,
            ["batch", "pyqual-run", str(git_project), "--dry-run"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, f"Batch pyqual-run failed: {result.output}"


# ===========================================================================
# API E2E Tests
# ===========================================================================

class TestApiE2E:
    """End-to-end tests for API endpoints."""

    def test_health_endpoint(self, api_client) -> None:
        """Test that /health returns valid payload."""
        response = api_client.get("/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert "version" in payload

    def test_refactor_endpoint_post(self, api_client) -> None:
        """Test that /refactor endpoint processes a real project."""
        response = api_client.post(
            "/refactor",
            json={"project_path": str(TEST_PROJECT_SRC), "max_actions": 2, "dry_run": True},
        )
        assert response.status_code == 200, f"Unexpected status: {response.text}"
        payload = response.json()
        # Should return structured output
        assert "output" in payload or "decisions" in payload or "actions" in payload

    def test_analyze_endpoint(self, api_client) -> None:
        """Test that /analyze endpoint returns metrics."""
        response = api_client.post(
            "/analyze",
            json={"project_dir": str(TEST_PROJECT_SRC)},
        )
        assert response.status_code == 200, f"Unexpected status: {response.text}"
        payload = response.json()
        assert "metrics" in payload or "alerts" in payload

    def test_memory_stats_endpoint(self, api_client) -> None:
        """Test that /memory/stats returns memory statistics."""
        response = api_client.get("/memory/stats")
        assert response.status_code == 200
        payload = response.json()
        assert isinstance(payload, dict)

    def test_debug_config_endpoint(self, api_client) -> None:
        """Test that /debug/config returns configuration info."""
        response = api_client.get("/debug/config")
        assert response.status_code == 200
        payload = response.json()
        assert isinstance(payload, dict)

    def test_decide_endpoint(self, api_client) -> None:
        """Test that /decide endpoint returns DSL decisions explanation."""
        response = api_client.post(
            "/decide",
            json={"project_dir": str(TEST_PROJECT_SRC)},
        )
        assert response.status_code == 200, f"Unexpected status: {response.text}"
        payload = response.json()
        assert "explanation" in payload

    def test_debug_decisions_endpoint(self, api_client) -> None:
        """Test that /debug/decisions returns DSL decisions for a project."""
        response = api_client.get(
            "/debug/decisions",
            params={"project_path": str(TEST_PROJECT_SRC), "limit": 10},
        )
        assert response.status_code == 200, f"Unexpected status: {response.text}"
        payload = response.json()
        # Should return dict with decisions list
        assert "decisions" in payload
        assert isinstance(payload["decisions"], list)

    def test_examples_list_endpoint(self, api_client) -> None:
        """Test that /examples endpoint returns list of examples."""
        response = api_client.get("/examples")
        assert response.status_code == 200
        payload = response.json()
        assert "examples" in payload
        assert isinstance(payload["examples"], list)

    def test_examples_yaml_endpoint(self, api_client) -> None:
        """Test that /examples/{name}/yaml endpoint returns scenario data."""
        response = api_client.get("/examples/basic-analysis/yaml")
        assert response.status_code == 200
        payload = response.json()
        assert isinstance(payload, dict)

    def test_rules_endpoint(self, api_client) -> None:
        """Test that /rules endpoint accepts custom DSL rules."""
        custom_rules = [
            {
                "name": "test-rule",
                "condition": {"metric": "cc", "operator": ">", "threshold": 10},
                "action": "refactor",
                "priority": 1,
            }
        ]
        response = api_client.post("/rules", json={"rules": custom_rules})
        assert response.status_code == 200
        payload = response.json()
        assert payload.get("status") == "ok"


# ===========================================================================
# Autonomy PR Workflow E2E Tests
# ===========================================================================

class TestAutonomyPRE2E:
    """End-to-end tests for autonomy PR workflow."""

    def test_quality_gate_workflow_on_git_project(self, git_project: Path) -> None:
        """Test that quality gate workflow works on real project."""
        from redsl.autonomy.quality_gate import run_quality_gate

        verdict = run_quality_gate(git_project)
        assert verdict is not None
        assert verdict.passed or len(verdict.violations) == 0

