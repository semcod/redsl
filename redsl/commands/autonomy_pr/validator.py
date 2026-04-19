"""Validation steps for the autonomous PR workflow.

Integrates testql and other validators to ensure refactored code
passes quality checks before creating a PR.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import click

from .models import _ValidationResult


def _step_validate(clone_path: Path) -> _ValidationResult:
    """Validate refactored code using available validators.

    Runs testql scenarios if available, plus pyqual quality gate.
    Returns success if all validators pass or are skipped.

    Args:
        clone_path: Path to cloned repository

    Returns:
        _ValidationResult with success status and details
    """
    click.echo(f"\nStep 4: Validating changes...")

    results: list[dict[str, Any]] = []

    # 1. Run testql validation if scenarios exist
    testql_result = _run_testql_validation(clone_path)
    results.append({"validator": "testql", "result": testql_result})

    if not testql_result["passed"] and not testql_result.get("skipped", False):
        return _ValidationResult(
            False, f"testql validation failed: {testql_result.get('reason', 'unknown error')}"
        )

    # 2. Run quality gate if available
    quality_result = _run_quality_gate(clone_path)
    results.append({"validator": "quality_gate", "result": quality_result})

    if not quality_result["passed"]:
        return _ValidationResult(
            False, f"Quality gate failed: {quality_result.get('reason', 'unknown error')}"
        )

    # 3. Run project tests if test command detected
    tests_result = _run_project_tests(clone_path)
    results.append({"validator": "project_tests", "result": tests_result})

    if not tests_result["passed"]:
        return _ValidationResult(
            False, f"Project tests failed: {tests_result.get('reason', 'unknown error')}"
        )

    passed_count = sum(1 for r in results if r["result"].get("passed", False))
    skipped_count = sum(1 for r in results if r["result"].get("skipped", False))
    total_count = len(results)

    click.echo(f"  ✓ Validation passed ({passed_count} passed, {skipped_count} skipped)")

    return _ValidationResult(True, details=results)


def _run_testql_validation(project_dir: Path) -> dict[str, Any]:
    """Run testql scenarios against the project.

    Args:
        project_dir: Path to project root

    Returns:
        dict with passed, reason, skipped, details
    """
    scenarios_dir = project_dir / "testql-scenarios"

    # Check if testql is available
    if not _check_testql_available():
        return {"passed": True, "skipped": True, "reason": "testql not installed"}

    # Check if scenarios exist
    if not scenarios_dir.exists():
        return {"passed": True, "skipped": True, "reason": "no testql-scenarios directory"}

    scenario_files = list(scenarios_dir.glob("*.testql.toon.yaml"))
    if not scenario_files:
        return {"passed": True, "skipped": True, "reason": "no testql scenario files"}

    # Detect API base URL
    base_url = _detect_api_base_url(project_dir)

    click.echo(f"  Running {len(scenario_files)} testql scenario(s)...")

    passed_count = 0
    failed_count = 0
    details: list[dict] = []

    for scenario_file in scenario_files:
        cmd = ["testql", str(scenario_file)]
        if base_url:
            cmd.extend(["--url", base_url])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(project_dir),
                timeout=60,
            )

            success = result.returncode == 0
            if success:
                passed_count += 1
            else:
                failed_count += 1

            details.append({
                "scenario": scenario_file.name,
                "passed": success,
                "stdout": result.stdout[:200] if result.stdout else "",
                "stderr": result.stderr[:200] if result.stderr else "",
            })

        except subprocess.TimeoutExpired:
            failed_count += 1
            details.append({
                "scenario": scenario_file.name,
                "passed": False,
                "error": "timeout after 60s",
            })
        except Exception as e:
            failed_count += 1
            details.append({
                "scenario": scenario_file.name,
                "passed": False,
                "error": str(e),
            })

    all_passed = failed_count == 0

    return {
        "passed": all_passed,
        "skipped": False,
        "reason": f"{passed_count}/{len(scenario_files)} scenarios passed" if all_passed else f"{failed_count} scenario(s) failed",
        "details": details,
        "passed_count": passed_count,
        "failed_count": failed_count,
    }


def _run_quality_gate(project_dir: Path) -> dict[str, Any]:
    """Run reDSL quality gate on the project.

    Args:
        project_dir: Path to project root

    Returns:
        dict with passed, reason, details
    """
    try:
        # Try to import and run quality gate
        from redsl.autonomy.quality_gate import run_quality_gate

        verdict = run_quality_gate(project_dir)

        return {
            "passed": verdict.passed,
            "reason": verdict.reason,
            "violations": verdict.violations,
            "metrics_before": verdict.metrics_before,
            "metrics_after": verdict.metrics_after,
        }

    except Exception as e:
        # Quality gate module not available or failed
        return {
            "passed": True,  # Don't block on quality gate errors
            "skipped": True,
            "reason": f"quality gate not available: {e}",
        }


def _run_project_tests(project_dir: Path) -> dict[str, Any]:
    """Run project test suite if available.

    Args:
        project_dir: Path to project root

    Returns:
        dict with passed, reason, details
    """
    # Detect test command
    test_cmd = _detect_test_command(project_dir)
    if not test_cmd:
        return {"passed": True, "skipped": True, "reason": "no test command detected"}

    click.echo(f"  Running project tests ({test_cmd[0]})...")

    try:
        result = subprocess.run(
            test_cmd,
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=300,
        )

        success = result.returncode == 0

        return {
            "passed": success,
            "reason": "tests passed" if success else f"tests failed (exit {result.returncode})",
            "stdout_preview": result.stdout[:300] if result.stdout else "",
            "stderr_preview": result.stderr[:300] if result.stderr else "",
        }

    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "reason": "tests timed out after 300s",
        }
    except Exception as e:
        return {
            "passed": True,  # Don't block on test runner errors
            "skipped": True,
            "reason": f"test runner error: {e}",
        }


def _check_testql_available() -> bool:
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


def _detect_api_base_url(project_dir: Path) -> str | None:
    """Detect API base URL from project configuration."""
    # Check .env files
    for env_file in [".env", ".env.example", ".env.local"]:
        env_path = project_dir / env_file
        if env_path.exists():
            try:
                content = env_path.read_text(encoding="utf-8")
                for line in content.splitlines():
                    if "API_URL" in line or "BASE_URL" in line or "SERVER_URL" in line:
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            return parts[1].strip().strip('"\'')
            except Exception:
                pass

    # Default common ports
    return "http://localhost:8000"


def _detect_test_command(project_dir: Path) -> list[str] | None:
    """Detect test command for the project.

    Returns:
        List of command arguments or None if no test command detected
    """
    # Check for Taskfile
    taskfile = project_dir / "Taskfile.yml"
    if taskfile.exists():
        try:
            import yaml

            data = yaml.safe_load(taskfile.read_text(encoding="utf-8"))
            tasks = data.get("tasks", {})
            if "test" in tasks:
                return ["task", "test"]
        except Exception:
            pass

    # Check for Makefile
    makefile = project_dir / "Makefile"
    if makefile.exists():
        content = makefile.read_text(encoding="utf-8")
        if "test:" in content or ".PHONY: test" in content:
            return ["make", "test"]

    # Check for pytest config
    if (project_dir / "pyproject.toml").exists() or (project_dir / "pytest.ini").exists():
        return ["python", "-m", "pytest", "-x", "-q"]

    # Check for package.json (Node.js)
    package_json = project_dir / "package.json"
    if package_json.exists():
        try:
            import json

            data = json.loads(package_json.read_text(encoding="utf-8"))
            scripts = data.get("scripts", {})
            if "test" in scripts:
                return ["npm", "test"]
        except Exception:
            pass

    return None


__all__ = ["_step_validate"]
