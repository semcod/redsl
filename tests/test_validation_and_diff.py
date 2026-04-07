"""Tests for validation/test_runner and refactors/diff_manager (Phase 1.4 + 1.5)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from redsl.validation import (
    TestResult,
    TestRunner,
    discover_test_command,
    run_tests,
    validate_refactor,
)
from redsl.refactors import (
    generate_diff,
    create_checkpoint,
    rollback_to_checkpoint,
    rollback_single_file,
)
from redsl.refactors.diff_manager import preview_proposal


# ─────────────────────────────────────────────────────────────────────────────
# TestResult dataclass
# ─────────────────────────────────────────────────────────────────────────────

class TestTestResultDataclass:
    def test_passed_result(self):
        r = TestResult(passed=True, output="1 passed", duration=0.1)
        assert r.passed is True
        assert r.duration == 0.1

    def test_failed_result(self):
        r = TestResult(passed=False, output="FAILED", duration=1.5, error="timeout")
        assert r.passed is False
        assert r.error == "timeout"


# ─────────────────────────────────────────────────────────────────────────────
# discover_test_command
# ─────────────────────────────────────────────────────────────────────────────

class TestDiscoverTestCommand:
    def test_discovers_pytest_via_pyproject(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("[tool.pytest]\n")
        with patch("shutil.which", side_effect=lambda x: "/usr/bin/" + x if x == "pytest" else None):
            cmd = discover_test_command(tmp_path)
        assert cmd is not None
        assert "pytest" in cmd[0]

    def test_discovers_pytest_via_tests_dir(self, tmp_path: Path):
        (tmp_path / "tests").mkdir()
        with patch("shutil.which", side_effect=lambda x: "/usr/bin/pytest" if x == "pytest" else None):
            cmd = discover_test_command(tmp_path)
        assert cmd is not None
        assert "pytest" in " ".join(cmd)

    def test_returns_none_when_nothing_found(self, tmp_path: Path):
        with patch("shutil.which", return_value=None):
            cmd = discover_test_command(tmp_path)
        assert cmd is None


# ─────────────────────────────────────────────────────────────────────────────
# run_tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRunTests:
    def test_returns_no_tests_when_command_none(self, tmp_path: Path):
        with patch("redsl.validation.test_runner.discover_test_command", return_value=None):
            result = run_tests(tmp_path)
        assert result.passed is True
        assert result.error == "no_tests_found"

    def test_returns_passed_on_zero_exit_code(self, tmp_path: Path):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "1 passed"
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            result = run_tests(tmp_path, command=["pytest"])
        assert result.passed is True
        assert "1 passed" in result.output

    def test_returns_failed_on_nonzero_exit_code(self, tmp_path: Path):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "FAILED test_foo"
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            result = run_tests(tmp_path, command=["pytest"])
        assert result.passed is False

    def test_returns_error_on_timeout(self, tmp_path: Path):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("pytest", 300)):
            result = run_tests(tmp_path, command=["pytest"])
        assert result.passed is False
        assert result.error == "timeout"

    def test_returns_error_when_command_not_found(self, tmp_path: Path):
        with patch("subprocess.run", side_effect=FileNotFoundError("pytest")):
            result = run_tests(tmp_path, command=["pytest"])
        assert result.passed is False
        assert "command_not_found" in result.error


# ─────────────────────────────────────────────────────────────────────────────
# validate_refactor
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateRefactor:
    def test_returns_true_when_no_tests(self, tmp_path: Path):
        applied = []
        with patch("redsl.validation.test_runner.discover_test_command", return_value=None):
            result = validate_refactor(tmp_path, lambda: applied.append(True) or True)
        assert result is True
        assert applied  # apply_fn was called

    def test_returns_false_and_rollbacks_when_tests_break(self, tmp_path: Path):
        call_count = {"n": 0}

        def fake_run_tests(project_dir, command=None):
            call_count["n"] += 1
            return TestResult(passed=call_count["n"] == 1, output="", duration=0.1)

        with patch("redsl.validation.test_runner.run_tests", side_effect=fake_run_tests), \
             patch("redsl.validation.test_runner._rollback_git") as mock_rollback:
            result = validate_refactor(tmp_path, lambda: True)

        assert result is False
        mock_rollback.assert_called_once_with(tmp_path)

    def test_returns_true_when_tests_pass_before_and_after(self, tmp_path: Path):
        def fake_run_tests(project_dir, command=None):
            return TestResult(passed=True, output="all pass", duration=0.1)

        with patch("redsl.validation.test_runner.run_tests", side_effect=fake_run_tests):
            result = validate_refactor(tmp_path, lambda: True)

        assert result is True


# ─────────────────────────────────────────────────────────────────────────────
# TestRunner class
# ─────────────────────────────────────────────────────────────────────────────

class TestTestRunnerClass:
    def test_runner_run_delegates_to_run_tests(self, tmp_path: Path):
        runner = TestRunner(tmp_path)
        with patch("redsl.validation.test_runner.run_tests",
                   return_value=TestResult(passed=True, output="ok", duration=0.1)) as mock_run:
            result = runner.run()
        mock_run.assert_called_once()
        assert result.passed is True

    def test_runner_discover_command(self, tmp_path: Path):
        runner = TestRunner(tmp_path)
        with patch("redsl.validation.test_runner.discover_test_command", return_value=["pytest"]):
            cmd = runner.discover_command()
        assert cmd == ["pytest"]


# ─────────────────────────────────────────────────────────────────────────────
# generate_diff
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateDiff:
    def test_produces_unified_diff(self):
        original = "def foo():\n    return 1\n"
        refactored = "def foo():\n    return 2\n"
        diff = generate_diff(original, refactored, "test.py")
        assert "--- a/test.py" in diff
        assert "+++ b/test.py" in diff
        assert "-    return 1" in diff
        assert "+    return 2" in diff

    def test_empty_diff_for_identical_files(self):
        code = "def foo():\n    pass\n"
        diff = generate_diff(code, code, "test.py")
        assert diff == ""

    def test_diff_for_new_file(self):
        diff = generate_diff("", "def bar(): pass\n", "new.py")
        assert "+def bar(): pass" in diff


# ─────────────────────────────────────────────────────────────────────────────
# create_checkpoint / rollback
# ─────────────────────────────────────────────────────────────────────────────

class TestCheckpointRollback:
    def test_create_and_rollback_file_based(self, tmp_path: Path):
        (tmp_path / "module.py").write_text("x = 1\n")

        # No git repo — uses file-copy fallback
        with patch("redsl.refactors.diff_manager._is_git_repo", return_value=False):
            checkpoint_id = create_checkpoint(tmp_path)

        assert checkpoint_id.startswith("files:")

        # Modify file
        (tmp_path / "module.py").write_text("x = 999\n")

        # Rollback
        with patch("redsl.refactors.diff_manager._is_git_repo", return_value=False):
            success = rollback_to_checkpoint(checkpoint_id, tmp_path)

        assert success is True
        assert (tmp_path / "module.py").read_text() == "x = 1\n"

    def test_rollback_single_file(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("a = 1\n")
        (tmp_path / "b.py").write_text("b = 2\n")

        with patch("redsl.refactors.diff_manager._is_git_repo", return_value=False):
            checkpoint_id = create_checkpoint(tmp_path)

        (tmp_path / "a.py").write_text("a = 999\n")
        (tmp_path / "b.py").write_text("b = 999\n")

        with patch("redsl.refactors.diff_manager._is_git_repo", return_value=False):
            success = rollback_single_file(tmp_path / "a.py", checkpoint_id, tmp_path)

        assert success is True
        assert (tmp_path / "a.py").read_text() == "a = 1\n"
        # b.py should NOT be rolled back
        assert (tmp_path / "b.py").read_text() == "b = 999\n"

    def test_rollback_returns_false_for_unknown_checkpoint(self, tmp_path: Path):
        success = rollback_to_checkpoint("unknown:abc", tmp_path)
        assert success is False
