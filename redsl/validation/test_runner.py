"""
Test runner validation — walidacja refaktoryzacji automatycznymi testami.

Cykl:
1. Uruchom testy PRZED zmianą → baseline
2. Zaaplikuj zmianę
3. Uruchom testy PO zmianie → after
4. Jeśli after.passed i baseline.passed: sukces
5. Jeśli after fail: git checkout -- . → rollback → log failure
6. Jeśli baseline fail: ostrzeżenie "testy już wcześniej nie przechodziły"
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

_TEST_COMMANDS = [
    (["pytest", "--tb=short", "-q"], "pytest.ini|setup.cfg|pyproject.toml|conftest.py"),
    (["python", "-m", "pytest", "--tb=short", "-q"], "pytest.ini|setup.cfg|pyproject.toml"),
    (["python3", "-m", "pytest", "--tb=short", "-q"], "pytest.ini|setup.cfg|pyproject.toml"),
    (["python", "-m", "unittest", "discover", "-s", "tests"], "tests/"),
    (["python3", "-m", "unittest", "discover", "-s", "tests"], "tests/"),
    (["tox"], "tox.ini"),
    (["make", "test"], "Makefile"),
]


@dataclass
class TestResult:
    """Wynik uruchomienia testów."""

    passed: bool
    output: str
    duration: float
    command: list[str] = field(default_factory=list)
    error: str = ""


class TestRunner:
    """Uruchamia testy projektu i waliduje wyniki refaktoryzacji."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self._command: list[str] | None = None

    def discover_command(self) -> list[str] | None:
        """Wykryj komendę testową na podstawie plików konfiguracyjnych."""
        return discover_test_command(self.project_dir)

    def run(self) -> TestResult:
        """Uruchom testy w projekcie."""
        return run_tests(self.project_dir, self._command)

    def validate_refactor(self, apply_fn: Callable[[], bool]) -> bool:
        """Waliduj refaktoryzację: uruchom testy przed i po zmianie.

        Returns True jeśli zmiana nie złamała testów.
        """
        return validate_refactor(self.project_dir, apply_fn)


def discover_test_command(project_dir: Path) -> list[str] | None:
    """Wykryj jak uruchamiać testy w projekcie.

    Sprawdza kolejno: pytest, unittest, tox, make test.
    Zwraca komendę jako listę lub None jeśli nie znaleziono.
    """
    for cmd, marker in _TEST_COMMANDS:
        if _command_exists(cmd[0]) and _marker_present(project_dir, marker):
            logger.info("Discovered test command: %s", cmd)
            return cmd

    # Last resort: check if tests/ directory exists with any pytest runner
    if (project_dir / "tests").is_dir() and shutil.which("pytest"):
        return ["pytest", "--tb=short", "-q"]
    if (project_dir / "tests").is_dir() and shutil.which("python3"):
        return ["python3", "-m", "pytest", "--tb=short", "-q"]

    logger.warning("No test command discovered in %s", project_dir)
    return None


def run_tests(
    project_dir: Path,
    command: list[str] | None = None,
) -> TestResult:
    """Uruchom testy projektu i zwróć wynik.

    Args:
        project_dir: Katalog projektu
        command: Komenda testowa (None = auto-wykryj)

    Returns:
        TestResult z passed, output, duration
    """
    if command is None:
        command = discover_test_command(project_dir)

    if command is None:
        return TestResult(
            passed=True,
            output="no tests found, skipping validation",
            duration=0.0,
            command=[],
            error="no_tests_found",
        )

    start = time.monotonic()
    try:
        result = subprocess.run(
            command,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=300,
        )
        duration = time.monotonic() - start
        passed = result.returncode == 0
        output = result.stdout + result.stderr
        logger.info(
            "Tests %s in %.1fs (cmd=%s)",
            "PASSED" if passed else "FAILED",
            duration,
            command,
        )
        return TestResult(
            passed=passed,
            output=output[:4000],
            duration=duration,
            command=command,
        )
    except subprocess.TimeoutExpired:
        duration = time.monotonic() - start
        logger.error("Tests timed out after %.0fs", duration)
        return TestResult(
            passed=False,
            output="",
            duration=duration,
            command=command,
            error="timeout",
        )
    except FileNotFoundError:
        duration = time.monotonic() - start
        logger.error("Test command not found: %s", command[0])
        return TestResult(
            passed=False,
            output="",
            duration=duration,
            command=command,
            error=f"command_not_found: {command[0]}",
        )


def validate_refactor(
    project_dir: Path,
    apply_fn: Callable[[], bool],
    command: list[str] | None = None,
) -> bool:
    """Waliduj refaktoryzację testami przed i po zmianie.

    Jeśli testy przechodzą przed zmianą ale nie po — rollback i log.
    Jeśli testy nie przechodziły przed zmianą — ostrzeżenie ale kontynuacja.

    Returns:
        True jeśli zmiana bezpieczna (testy pass lub brak testów)
    """
    # Baseline — testy przed zmianą
    baseline = run_tests(project_dir, command)

    if baseline.error == "no_tests_found":
        logger.warning("No tests found in %s, skipping validation", project_dir)
        apply_fn()
        return True

    if not baseline.passed:
        logger.warning(
            "Tests already failing before refactor in %s — proceeding with caution",
            project_dir,
        )

    # Zaaplikuj zmianę
    try:
        applied = apply_fn()
    except Exception as e:
        logger.error("Apply function raised exception: %s", e)
        return False

    if not applied:
        return False

    # Testy po zmianie
    after = run_tests(project_dir, command)

    if baseline.passed and not after.passed:
        logger.error(
            "Refactor BROKE tests in %s (%.1fs):\n%s",
            project_dir,
            after.duration,
            after.output[-2000:],
        )
        _rollback_git(project_dir)
        return False

    if after.passed:
        logger.info(
            "Refactor validated ✓ tests pass in %.1fs",
            after.duration,
        )
    return after.passed or not baseline.passed


def _command_exists(name: str) -> bool:
    """Sprawdź czy komenda jest dostępna w PATH."""
    return shutil.which(name) is not None


def _marker_present(project_dir: Path, marker: str) -> bool:
    """Sprawdź czy marker (plik/katalog) istnieje w katalogu projektu."""
    for m in marker.split("|"):
        if (project_dir / m.strip()).exists():
            return True
    return False


def _rollback_git(project_dir: Path) -> None:
    """Cofnij zmiany git w katalogu projektu."""
    try:
        result = subprocess.run(
            ["git", "checkout", "--", "."],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logger.info("Git rollback successful in %s", project_dir)
        else:
            logger.error("Git rollback failed: %s", result.stderr)
    except FileNotFoundError:
        logger.warning("git not available, cannot rollback")
