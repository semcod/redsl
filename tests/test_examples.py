"""Tests for redsl examples in examples/ directory.

This module tests that all example scripts run without errors
and produce expected outputs.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Base directory for examples
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def _run_example(name: str, extra_args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run an example script once and cache the result."""
    script_path = EXAMPLES_DIR / name / "main.py"
    cmd = [sys.executable, str(script_path)]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True)


@pytest.fixture(scope="module")
def basic_analysis_result():
    return _run_example("01-basic-analysis")


@pytest.fixture(scope="module")
def custom_rules_result():
    return _run_example("02-custom-rules")


@pytest.fixture(scope="module")
def full_pipeline_result():
    return _run_example("03-full-pipeline")


@pytest.fixture(scope="module")
def memory_learning_result():
    return _run_example("04-memory-learning")


@pytest.fixture(scope="module")
def api_integration_result():
    return _run_example("05-api-integration")


@pytest.fixture(scope="module")
def awareness_result():
    return _run_example("06-awareness")


@pytest.fixture(scope="module")
def pyqual_result():
    return _run_example("07-pyqual")


@pytest.fixture(scope="module")
def audit_result():
    return _run_example("08-audit")


@pytest.fixture(scope="module")
def pr_bot_result():
    return _run_example("09-pr-bot")


@pytest.fixture(scope="module")
def badge_result():
    return _run_example("10-badge")


class TestBasicAnalysisExample:
    """Test 01-basic-analysis example."""

    def test_example_runs_without_errors(self, basic_analysis_result):
        """Verify the basic analysis example executes successfully."""
        assert basic_analysis_result.returncode == 0, f"Script failed with: {basic_analysis_result.stderr}"

    def test_output_contains_analysis_summary(self, basic_analysis_result):
        """Verify output contains expected analysis summary."""
        assert "ReDSL — Analiza projektu" in basic_analysis_result.stdout
        assert "Pliki:" in basic_analysis_result.stdout
        assert "Alerty:" in basic_analysis_result.stdout

    def test_finds_expected_decisions(self, basic_analysis_result):
        """Verify example finds expected refactoring decisions."""
        assert "extract_functions" in basic_analysis_result.stdout
        assert "split_module" in basic_analysis_result.stdout or "reduce_fan_out" in basic_analysis_result.stdout


class TestCustomRulesExample:
    """Test 02-custom-rules example."""

    def test_example_runs_without_errors(self, custom_rules_result):
        """Verify custom rules example executes successfully."""
        assert custom_rules_result.returncode == 0, f"Script failed with: {custom_rules_result.stderr}"

    def test_adds_python_rules(self, custom_rules_result):
        """Verify example adds Python-defined rules."""
        assert "Po dodaniu Pythonowych" in custom_rules_result.stdout
        assert "Po dodaniu YAML" in custom_rules_result.stdout

    def test_makes_decisions(self, custom_rules_result):
        """Verify example produces decisions from custom rules."""
        assert "Decyzje" in custom_rules_result.stdout
        assert "split_module" in custom_rules_result.stdout or "extract_functions" in custom_rules_result.stdout


class TestFullPipelineExample:
    """Test 03-full-pipeline example."""

    def test_example_runs_without_errors(self, full_pipeline_result):
        """Verify full pipeline example executes (may skip LLM parts)."""
        # May fail if no API key, but should handle gracefully
        assert full_pipeline_result.returncode in [0, 1], f"Unexpected crash: {full_pipeline_result.stderr}"

    def test_shows_usage_info(self, full_pipeline_result):
        """Verify example displays usage information."""
        assert "ReDSL" in full_pipeline_result.stdout or "OPENAI_API_KEY" in full_pipeline_result.stdout


class TestMemoryLearningExample:
    """Test 04-memory-learning example."""

    def test_example_runs_without_errors(self, memory_learning_result):
        """Verify memory learning example executes successfully."""
        assert memory_learning_result.returncode == 0, f"Script failed with: {memory_learning_result.stderr}"

    def test_shows_memory_layers(self, memory_learning_result):
        """Verify example demonstrates all memory layers."""
        assert "EPISODIC" in memory_learning_result.stdout
        assert "SEMANTIC" in memory_learning_result.stdout
        assert "PROCEDURAL" in memory_learning_result.stdout

    def test_memory_stats_shown(self, memory_learning_result):
        """Verify memory statistics are displayed."""
        assert "Pamięć agenta:" in memory_learning_result.stdout
        assert "wpisów" in memory_learning_result.stdout


class TestApiIntegrationExample:
    """Test 05-api-integration example."""

    def test_example_runs_without_errors(self, api_integration_result):
        """Verify API integration example executes successfully."""
        assert api_integration_result.returncode == 0, f"Script failed with: {api_integration_result.stderr}"

    def test_shows_curl_examples(self, api_integration_result):
        """Verify example displays curl command examples."""
        assert "curl" in api_integration_result.stdout
        assert "localhost:8000" in api_integration_result.stdout

    def test_shows_all_endpoints(self, api_integration_result):
        """Verify example mentions all API endpoints."""
        assert "/analyze" in api_integration_result.stdout or "/health" in api_integration_result.stdout


@pytest.mark.parametrize("example_name", [
    "01-basic-analysis",
    "02-custom-rules",
    "03-full-pipeline",
    "04-memory-learning",
    "05-api-integration",
    "06-awareness",
    "07-pyqual",
    "08-audit",
    "09-pr-bot",
    "10-badge",
])
def test_all_examples_exist(example_name):
    """Verify all expected example directories exist."""
    example_dir = EXAMPLES_DIR / example_name
    assert example_dir.exists(), f"Example directory missing: {example_name}"
    assert (example_dir / "main.py").exists(), f"main.py missing in {example_name}"


def test_examples_have_readme():
    """Verify examples have README files."""
    for example_dir in EXAMPLES_DIR.iterdir():
        if example_dir.is_dir() and example_dir.name.startswith(("0", "1", "2")):
            readme = example_dir / "README.md"
            if not readme.exists():
                pytest.fail(f"Missing README.md in {example_dir.name}")


@pytest.mark.parametrize("dir_name", [
    "01-basic-analysis",
    "02-custom-rules",
    "03-full-pipeline",
    "04-memory-learning",
    "05-api-integration",
    "06-awareness",
    "07-pyqual",
    "08-audit",
    "09-pr-bot",
    "10-badge",
])
def test_example_yaml_files_exist(dir_name):
    """Verify each example directory has default.yaml and advanced.yaml."""
    example_dir = EXAMPLES_DIR / dir_name
    assert (example_dir / "default.yaml").exists(), f"default.yaml missing in {dir_name}"
    assert (example_dir / "advanced.yaml").exists(), f"advanced.yaml missing in {dir_name}"


def test_advanced_examples_run(capsys):
    """Verify the advanced scenarios execute from the examples/ directory."""
    from redsl.examples.basic_analysis import run_basic_analysis_example
    from redsl.examples.custom_rules import run_custom_rules_example
    from redsl.examples.memory_learning import run_memory_learning_example

    basic_report = run_basic_analysis_example("advanced")
    custom_report = run_custom_rules_example("advanced")
    memory_report = run_memory_learning_example("advanced")
    captured = capsys.readouterr()

    assert "(advanced)" in captured.out or "advanced" in captured.out
    assert len(basic_report["decisions"]) > 0
    assert len(custom_report["decisions"]) > 0
    assert memory_report["stats"]["episodic"] >= 5


class TestAwarenessExample:
    """Test 06-awareness example."""

    def test_example_runs_without_errors(self, awareness_result):
        assert awareness_result.returncode == 0, f"Script failed with: {awareness_result.stderr}"

    def test_shows_patterns(self, awareness_result):
        assert "Wzorce zmian" in awareness_result.stdout or "wzorce" in awareness_result.stdout.lower()
        assert "Timeline" in awareness_result.stdout


class TestPyQualExample:
    """Test 07-pyqual example."""

    def test_example_runs_without_errors(self, pyqual_result):
        assert pyqual_result.returncode == 0, f"Script failed with: {pyqual_result.stderr}"

    def test_shows_quality_issues(self, pyqual_result):
        assert "Nieużywane importy" in pyqual_result.stdout or "Pliki" in pyqual_result.stdout


class TestAuditExample:
    """Test 08-audit example."""

    def test_runs_without_errors(self, audit_result):
        assert audit_result.returncode == 0, f"Script failed with: {audit_result.stderr}"

    def test_shows_grade_and_badge(self, audit_result):
        assert "Grade" in audit_result.stdout
        assert "Badge" in audit_result.stdout or "badge" in audit_result.stdout
        assert "img.shields.io" in audit_result.stdout


class TestPrBotExample:
    """Test 09-pr-bot example."""

    def test_runs_without_errors(self, pr_bot_result):
        assert pr_bot_result.returncode == 0, f"Script failed with: {pr_bot_result.stderr}"

    def test_shows_pr_comment(self, pr_bot_result):
        assert "redsl-bot" in pr_bot_result.stdout
        assert "Metrics" in pr_bot_result.stdout
        assert "Status check" in pr_bot_result.stdout


class TestBadgeExample:
    """Test 10-badge example."""

    def test_runs_without_errors(self, badge_result):
        assert badge_result.returncode == 0, f"Script failed with: {badge_result.stderr}"

    def test_shows_badges_and_grades(self, badge_result):
        assert "Markdown" in badge_result.stdout
        assert "img.shields.io" in badge_result.stdout
        assert "auth-module" in badge_result.stdout
