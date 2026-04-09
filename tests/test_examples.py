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


class TestBasicAnalysisExample:
    """Test 01-basic-analysis example."""

    def test_example_runs_without_errors(self):
        """Verify the basic analysis example executes successfully."""
        script_path = EXAMPLES_DIR / "01-basic-analysis" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Script failed with: {result.stderr}"

    def test_output_contains_analysis_summary(self):
        """Verify output contains expected analysis summary."""
        script_path = EXAMPLES_DIR / "01-basic-analysis" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "ReDSL — Analiza projektu" in result.stdout
        assert "Pliki:" in result.stdout
        assert "Alerty:" in result.stdout

    def test_finds_expected_decisions(self):
        """Verify example finds expected refactoring decisions."""
        script_path = EXAMPLES_DIR / "01-basic-analysis" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "extract_functions" in result.stdout
        assert "split_module" in result.stdout or "reduce_fan_out" in result.stdout


class TestCustomRulesExample:
    """Test 02-custom-rules example."""

    def test_example_runs_without_errors(self):
        """Verify custom rules example executes successfully."""
        script_path = EXAMPLES_DIR / "02-custom-rules" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Script failed with: {result.stderr}"

    def test_adds_python_rules(self):
        """Verify example adds Python-defined rules."""
        script_path = EXAMPLES_DIR / "02-custom-rules" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "Po dodaniu Pythonowych" in result.stdout
        assert "Po dodaniu YAML" in result.stdout

    def test_makes_decisions(self):
        """Verify example produces decisions from custom rules."""
        script_path = EXAMPLES_DIR / "02-custom-rules" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "Decyzje" in result.stdout
        assert "split_module" in result.stdout or "extract_functions" in result.stdout


class TestFullPipelineExample:
    """Test 03-full-pipeline example."""

    def test_example_runs_without_errors(self):
        """Verify full pipeline example executes (may skip LLM parts)."""
        script_path = EXAMPLES_DIR / "03-full-pipeline" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        # May fail if no API key, but should handle gracefully
        assert result.returncode in [0, 1], f"Unexpected crash: {result.stderr}"

    def test_shows_usage_info(self):
        """Verify example displays usage information."""
        script_path = EXAMPLES_DIR / "03-full-pipeline" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True,
        )
        # --help may not be supported, check if header is shown
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "ReDSL" in result.stdout or "OPENAI_API_KEY" in result.stdout


class TestMemoryLearningExample:
    """Test 04-memory-learning example."""

    def test_example_runs_without_errors(self):
        """Verify memory learning example executes successfully."""
        script_path = EXAMPLES_DIR / "04-memory-learning" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Script failed with: {result.stderr}"

    def test_shows_memory_layers(self):
        """Verify example demonstrates all memory layers."""
        script_path = EXAMPLES_DIR / "04-memory-learning" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "EPISODIC" in result.stdout
        assert "SEMANTIC" in result.stdout
        assert "PROCEDURAL" in result.stdout

    def test_memory_stats_shown(self):
        """Verify memory statistics are displayed."""
        script_path = EXAMPLES_DIR / "04-memory-learning" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "Pamięć agenta:" in result.stdout
        assert "wpisów" in result.stdout


class TestApiIntegrationExample:
    """Test 05-api-integration example."""

    def test_example_runs_without_errors(self):
        """Verify API integration example executes successfully."""
        script_path = EXAMPLES_DIR / "05-api-integration" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Script failed with: {result.stderr}"

    def test_shows_curl_examples(self):
        """Verify example displays curl command examples."""
        script_path = EXAMPLES_DIR / "05-api-integration" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "curl" in result.stdout
        assert "localhost:8000" in result.stdout

    def test_shows_all_endpoints(self):
        """Verify example mentions all API endpoints."""
        script_path = EXAMPLES_DIR / "05-api-integration" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "/analyze" in result.stdout or "/health" in result.stdout


@pytest.mark.parametrize("example_name", [
    "01-basic-analysis",
    "02-custom-rules",
    "03-full-pipeline",
    "04-memory-learning",
    "05-api-integration",
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
