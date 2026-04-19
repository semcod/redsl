"""Tests for testql_bridge integration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from redsl.validation.testql_bridge import (
    HAS_TESTQL,
    TestqlValidator,
    TestqlVerdict,
    check_testql_available,
    validate_with_testql,
)


class TestTestqlVerdict:
    """Test TestqlVerdict dataclass."""

    def test_passed_verdict(self) -> None:
        """Test creating a passed verdict."""
        verdict = TestqlVerdict(
            passed=True,
            reason="All scenarios passed",
            scenarios_run=3,
            scenarios_passed=3,
            scenarios_failed=0,
        )
        assert verdict.passed is True
        assert verdict.scenarios_run == 3
        assert verdict.skipped is False

    def test_failed_verdict(self) -> None:
        """Test creating a failed verdict."""
        verdict = TestqlVerdict(
            passed=False,
            reason="2 scenario(s) failed",
            scenarios_run=3,
            scenarios_passed=1,
            scenarios_failed=2,
        )
        assert verdict.passed is False
        assert verdict.scenarios_failed == 2

    def test_skipped_result(self) -> None:
        """Test creating a skipped verdict."""
        verdict = TestqlVerdict.skipped_result("No scenarios found")
        assert verdict.passed is True  # Skipped counts as pass
        assert verdict.skipped is True
        assert verdict.reason == "No scenarios found"


class TestTestqlValidator:
    """Test TestqlValidator class."""

    def test_init_without_testql(self, tmp_path: Path) -> None:
        """Test initialization when testql is not available."""
        with patch.object(TestqlValidator, '_check_testql', return_value=False):
            validator = TestqlValidator(tmp_path)
            assert validator._testql_available is False

    def test_validate_skips_when_testql_unavailable(self, tmp_path: Path) -> None:
        """Test validation skips when testql is not available."""
        validator = TestqlValidator(tmp_path)
        validator._testql_available = False

        verdict = validator.validate()

        assert verdict.skipped is True
        assert verdict.passed is True  # Skipped = not a failure
        assert "testql not installed" in verdict.reason

    def test_validate_skips_without_scenarios(self, tmp_path: Path) -> None:
        """Test validation skips when no scenarios exist."""
        validator = TestqlValidator(tmp_path)
        validator._testql_available = True

        # No scenarios directory
        verdict = validator.validate()

        assert verdict.skipped is True
        assert "no testql scenarios" in verdict.reason.lower()

    def test_validate_skips_empty_scenarios_dir(self, tmp_path: Path) -> None:
        """Test validation skips when scenarios directory is empty."""
        scenarios_dir = tmp_path / "testql-scenarios"
        scenarios_dir.mkdir()

        validator = TestqlValidator(tmp_path)
        validator._testql_available = True

        verdict = validator.validate(scenarios_dir)

        assert verdict.skipped is True
        assert "no testql scenario files" in verdict.reason.lower()

    @patch('redsl.validation.testql_bridge.subprocess.run')
    def test_validate_runs_scenarios(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test running validation with scenarios."""
        # Create scenarios directory and file
        scenarios_dir = tmp_path / "testql-scenarios"
        scenarios_dir.mkdir()
        (scenarios_dir / "api.testql.toon.yaml").write_text(
            "# SCENARIO: API Test\nAPI[1]{method, endpoint, status}:\n  GET, /health, 200\n",
            encoding="utf-8",
        )

        # Mock successful testql execution
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"passed": true}',
            stderr='',
        )

        validator = TestqlValidator(tmp_path)
        validator._testql_available = True

        verdict = validator.validate(scenarios_dir)

        assert verdict.skipped is False
        assert verdict.scenarios_run == 1
        assert mock_run.called

    @patch('redsl.validation.testql_bridge.subprocess.run')
    def test_validate_detects_failures(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test validation detects failing scenarios."""
        # Create scenarios
        scenarios_dir = tmp_path / "testql-scenarios"
        scenarios_dir.mkdir()
        (scenarios_dir / "api.testql.toon.yaml").write_text("# test", encoding="utf-8")

        # Mock failed testql execution
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='',
            stderr='Connection refused',
        )

        validator = TestqlValidator(tmp_path)
        validator._testql_available = True

        verdict = validator.validate(scenarios_dir)

        assert verdict.passed is False
        assert verdict.scenarios_failed == 1

    def test_detect_base_url_from_env(self, tmp_path: Path) -> None:
        """Test detecting base URL from .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("API_URL=http://localhost:9000\n", encoding="utf-8")

        validator = TestqlValidator(tmp_path)
        url = validator._detect_base_url()

        assert url == "http://localhost:9000"

    def test_detect_base_url_default(self, tmp_path: Path) -> None:
        """Test default base URL when no config found."""
        validator = TestqlValidator(tmp_path)
        url = validator._detect_base_url()

        assert url == "http://localhost:8000"

    def test_generate_smoke_scenarios_without_testql(self, tmp_path: Path) -> None:
        """Test smoke scenario generation when testql unavailable."""
        validator = TestqlValidator(tmp_path)
        validator._testql_available = False

        result = validator.generate_smoke_scenarios()

        assert result is None

    @patch('redsl.validation.testql_bridge.subprocess.run')
    def test_generate_smoke_scenarios(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test smoke scenario generation."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"endpoints": [{"path": "/health", "method": "GET"}]}',
            stderr='',
        )

        validator = TestqlValidator(tmp_path)
        validator._testql_available = True

        result = validator.generate_smoke_scenarios()

        # Should create testql-scenarios directory
        assert result is not None
        assert result.exists()
        assert (result / "smoke.testql.toon.yaml").exists()


class TestValidateWithTestql:
    """Test validate_with_testql convenience function."""

    def test_validate_empty_project(self, tmp_path: Path) -> None:
        """Test validating empty project."""
        with patch.object(TestqlValidator, '_check_testql', return_value=False):
            verdict = validate_with_testql(tmp_path)
            assert verdict.skipped is True


class TestCheckTestqlAvailable:
    """Test check_testql_available function."""

    @patch('redsl.validation.testql_bridge.subprocess.run')
    def test_returns_true_when_testql_available(self, mock_run: MagicMock) -> None:
        """Test returns True when testql CLI exists."""
        mock_run.return_value = MagicMock(returncode=0)
        assert check_testql_available() is True

    @patch('redsl.validation.testql_bridge.subprocess.run')
    def test_returns_false_when_testql_missing(self, mock_run: MagicMock) -> None:
        """Test returns False when testql CLI not found."""
        mock_run.side_effect = FileNotFoundError()
        assert check_testql_available() is False

    @patch('redsl.validation.testql_bridge.subprocess.run')
    def test_returns_false_on_timeout(self, mock_run: MagicMock) -> None:
        """Test returns False when testql times out."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("testql", 5)
        assert check_testql_available() is False


class TestIntegrationScenarios:
    """Integration-style tests with mocked subprocess."""

    @patch('redsl.validation.testql_bridge.subprocess.run')
    def test_full_validation_workflow(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test complete validation workflow."""
        # Setup project structure
        scenarios_dir = tmp_path / "testql-scenarios"
        scenarios_dir.mkdir()

        # Create multiple scenarios
        for i in range(3):
            (scenarios_dir / f"test{i}.testql.toon.yaml").write_text(
                f"# SCENARIO: Test {i}\nAPI[1]{{method, endpoint, status}}:\n  GET, /api/{i}, 200\n",
                encoding="utf-8",
            )

        # Mock all subprocess calls
        def side_effect(cmd, **kwargs):
            mock = MagicMock()
            if cmd[0] == "testql" and cmd[1] == "--version":
                mock.returncode = 0
            elif cmd[0] == "testql":
                # All scenarios pass
                mock.returncode = 0
                mock.stdout = '{"status": "passed"}'
            else:
                mock.returncode = 0
            return mock

        mock_run.side_effect = side_effect

        validator = TestqlValidator(tmp_path)

        verdict = validator.validate(scenarios_dir)

        assert verdict.passed is True
        assert verdict.scenarios_run == 3
        assert verdict.scenarios_passed == 3
        assert verdict.scenarios_failed == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
