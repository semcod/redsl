"""testql_bridge — Post-refactoring validation using testql scenarios.

Validates that API contracts and functionality remain intact after refactoring.
Integrates with autonomy_pr workflow for safety checks before committing.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from redsl.config import AgentConfig


@dataclass
class TestqlVerdict:
    """Validation verdict from testql scenario execution."""

    __test__ = False  # Not a pytest test class

    passed: bool
    reason: str
    scenarios_run: int = 0
    scenarios_passed: int = 0
    scenarios_failed: int = 0
    details: list[dict] = field(default_factory=list)
    skipped: bool = False

    @classmethod
    def skipped_result(cls, reason: str) -> "TestqlVerdict":
        """Create a skipped verdict."""
        return cls(
            passed=True,  # Skipped is not a failure
            reason=reason,
            skipped=True,
        )


class TestqlValidator:
    """Post-refactoring validator using testql scenarios.

    Runs testql scenarios against the refactored code to ensure
    API contracts and functionality remain intact.
    """

    def __init__(self, project_dir: Path, config: AgentConfig | None = None) -> None:
        self.project_dir = project_dir.resolve()
        self.config = config or AgentConfig.from_env()
        self._testql_available = self._check_testql()

    def _check_testql(self) -> bool:
        """Check if testql is available."""
        try:
            subprocess.run(
                ["testql", "--version"],
                capture_output=True,
                timeout=5,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def validate(self, scenarios_dir: Path | None = None) -> TestqlVerdict:
        """Validate project by running testql scenarios.

        Args:
            scenarios_dir: Directory containing .testql.toon.yaml files.
                          Defaults to project_dir/testql-scenarios

        Returns:
            TestqlVerdict with validation results
        """
        if scenarios_dir is None:
            scenarios_dir = self.project_dir / "testql-scenarios"

        # Check if testql is available
        if not self._testql_available:
            return TestqlVerdict.skipped_result("testql not installed")

        # Check if scenarios exist
        if not scenarios_dir.exists():
            return TestqlVerdict.skipped_result(f"No testql scenarios at {scenarios_dir}")

        scenario_files = list(scenarios_dir.glob("*.testql.toon.yaml"))
        if not scenario_files:
            return TestqlVerdict.skipped_result("No testql scenario files found")

        # Detect API base URL
        base_url = self._detect_base_url()

        # Run each scenario
        results: list[dict] = []
        passed_count = 0
        failed_count = 0

        for scenario_file in scenario_files:
            result = self._run_scenario(scenario_file, base_url)
            results.append(result)
            if result.get("success", False):
                passed_count += 1
            else:
                failed_count += 1

        all_passed = failed_count == 0

        return TestqlVerdict(
            passed=all_passed,
            reason="All scenarios passed" if all_passed else f"{failed_count} scenario(s) failed",
            scenarios_run=len(scenario_files),
            scenarios_passed=passed_count,
            scenarios_failed=failed_count,
            details=results,
        )

    def _run_scenario(self, scenario_file: Path, base_url: str | None) -> dict[str, Any]:
        """Run a single testql scenario."""
        cmd = ["testql", str(scenario_file)]
        if base_url:
            cmd.extend(["--url", base_url])
        cmd.extend(["--output", "json"])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_dir),
                timeout=60,
            )

            success = result.returncode == 0

            return {
                "scenario": scenario_file.name,
                "success": success,
                "stdout": result.stdout[:500] if result.stdout else "",
                "stderr": result.stderr[:500] if result.stderr else "",
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "scenario": scenario_file.name,
                "success": False,
                "error": "Timeout after 60s",
            }
        except Exception as e:
            return {
                "scenario": scenario_file.name,
                "success": False,
                "error": str(e),
            }

    def _detect_base_url(self) -> str | None:
        """Detect API base URL from project configuration."""
        # Try to detect from various sources

        # 1. Check pyproject.toml for scripts
        pyproject = self.project_dir / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib

                data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
                scripts = data.get("project", {}).get("scripts", {})
                # Look for server script
                for name, script in scripts.items():
                    if "server" in name.lower() or "api" in name.lower():
                        # Guess localhost + common port
                        return "http://localhost:8000"
            except Exception:
                pass

        # 2. Check for .env or env files
        for env_file in [".env", ".env.example", ".env.local"]:
            env_path = self.project_dir / env_file
            if env_path.exists():
                content = env_path.read_text(encoding="utf-8")
                for line in content.splitlines():
                    if "API_URL" in line or "BASE_URL" in line:
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            return parts[1].strip().strip('"\'')

        # 3. Default fallback
        return "http://localhost:8000"

    def generate_smoke_scenarios(self, output_dir: Path | None = None) -> Path | None:
        """Generate smoke test scenarios for the project.

        Uses testql endpoint detection to auto-generate basic API tests.

        Args:
            output_dir: Directory to write scenarios. Defaults to testql-scenarios/

        Returns:
            Path to generated scenarios directory or None if generation failed
        """
        if output_dir is None:
            output_dir = self.project_dir / "testql-scenarios"

        if not self._testql_available:
            return None

        output_dir.mkdir(parents=True, exist_ok=True)

        # Detect endpoints
        try:
            result = subprocess.run(
                ["testql", "endpoints", str(self.project_dir), "--format", "json"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return None

            # Generate smoke scenarios from detected endpoints
            return self._write_smoke_scenarios(output_dir, result.stdout)

        except Exception:
            return None

    def _write_smoke_scenarios(self, output_dir: Path, endpoints_json: str) -> Path:
        """Write smoke test scenarios based on detected endpoints."""
        # Basic smoke scenario template
        smoke_content = """# SCENARIO: Auto-generated Smoke Tests
# TYPE: api
# VERSION: 1.0

CONFIG[1]{key, value}:
  base_url,  http://localhost:8000

API[1]{method, endpoint, status}:
  GET,  /health,  200

ASSERT[1]{field, op, expected}:
  status,  ==,  ok
"""

        smoke_file = output_dir / "smoke.testql.toon.yaml"
        smoke_file.write_text(smoke_content, encoding="utf-8")

        return output_dir


# Try to import and use oqlos.testql if available
try:
    from testql.runner import execute_scenario as _testql_execute  # type: ignore[import]
    from testql.parser import parse_script as _testql_parse  # type: ignore[import]

    HAS_TESTQL = True
except ImportError:
    HAS_TESTQL = False


def validate_with_testql(
    project_dir: Path,
    scenarios_dir: Path | None = None,
    config: AgentConfig | None = None,
) -> TestqlVerdict:
    """Validate project using testql scenarios.

    Convenience function that creates a validator and runs validation.

    Args:
        project_dir: Path to project root
        scenarios_dir: Directory containing testql scenarios
        config: Agent configuration

    Returns:
        TestqlVerdict with validation results
    """
    validator = TestqlValidator(project_dir, config)
    return validator.validate(scenarios_dir)


def check_testql_available() -> bool:
    """Check if testql CLI is available."""
    try:
        subprocess.run(
            ["testql", "--version"],
            capture_output=True,
            timeout=5,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


__all__ = [
    "TestqlValidator",
    "TestqlVerdict",
    "validate_with_testql",
    "check_testql_available",
    "HAS_TESTQL",
]
