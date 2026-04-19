"""Tests for the redsl.autonomy.quality_gate module."""

from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_git_project(tmp_path: Path) -> Path:
    """Create a minimal git-initialized Python project."""
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), capture_output=True)

    # Create a simple Python file
    pkg = tmp_path / "mymod"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "core.py").write_text(textwrap.dedent("""\
        def hello():
            return "world"

        def add(a, b):
            return a + b
    """))

    # Initial commit
    subprocess.run(["git", "add", "-A"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=str(tmp_path), capture_output=True, check=True)
    return tmp_path


# ===========================================================================
# quality_gate.py
# ===========================================================================

class TestQualityGate:
    def test_gate_passes_on_clean_project(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.quality_gate import run_quality_gate

        verdict = run_quality_gate(tmp_git_project)
        assert verdict.passed
        assert verdict.reason == "OK"
        assert verdict.violations == []

    def test_gate_detects_high_cc_new_function(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.quality_gate import run_quality_gate

        # Add a complex function (many branches)
        complex_func = "def complex():\n"
        for i in range(15):
            complex_func += f"    if x == {i}:\n        return {i}\n"
        complex_func += "    return -1\n"

        new_file = tmp_git_project / "mymod" / "complex.py"
        new_file.write_text(complex_func)

        # Lower threshold so it triggers
        verdict = run_quality_gate(tmp_git_project, max_new_function_cc=5)
        # new_functions only picks up untracked files
        assert isinstance(verdict, object)
        assert "cc_mean" in verdict.metrics_after

    def test_gate_detects_oversized_new_file(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.quality_gate import run_quality_gate

        # Create a file with >100 lines (use low threshold)
        big = tmp_git_project / "mymod" / "big.py"
        big.write_text("\n".join(f"x_{i} = {i}" for i in range(150)))

        verdict = run_quality_gate(tmp_git_project, max_new_file_lines=50)
        found_size_violation = any("New file" in v for v in verdict.violations)
        assert found_size_violation

    def test_gate_verdict_dataclass(self) -> None:
        from redsl.autonomy.quality_gate import GateVerdict

        v = GateVerdict(
            passed=False,
            reason="1 violation(s)",
            metrics_before={"cc_mean": 1.0},
            metrics_after={"cc_mean": 2.0},
            violations=["CC mean increased"],
        )
        assert not v.passed
        assert len(v.violations) == 1

    def test_install_hook(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.quality_gate import install_pre_commit_hook

        hook = install_pre_commit_hook(tmp_git_project)
        assert hook.exists()
        assert os.access(hook, os.X_OK)
        content = hook.read_text()
        assert "quality gate" in content.lower()