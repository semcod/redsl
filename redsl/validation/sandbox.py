"""
Tier 3D — Refactor Sandbox (pactfix / Docker integration).

Izolowane środowisko Docker do bezpiecznego testowania propozycji refaktoryzacji
ZANIM zostaną zaaplikowane na żywym kodzie.

Przepływ:
  1. start()   — uruchom kontener z read-only kopią projektu
  2. apply_and_test()  — zaaplikuj patch, uruchom testy wewnątrz kontenera
  3. stop()    — zniszcz kontener (ephemeral — żadnych śladów)

Jeśli Docker nie jest dostępny, rzuca DockerNotFoundError z czytelnym komunikatem.
Jeśli pactfix CLI jest zainstalowane, deleguje sandbox management do pactfix.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from redsl.utils.tool_check import is_tool_available

logger = logging.getLogger(__name__)

_DOCKER_IMAGE = "python:3.12-slim"
_TEST_TIMEOUT = 120


class DockerNotFoundError(RuntimeError):
    """Raised when Docker daemon is not available."""


class SandboxError(RuntimeError):
    """Raised for sandbox-level failures."""


def _docker_available() -> bool:
    return is_tool_available(["docker", "info"], timeout=5)


def _pactfix_available() -> bool:
    return is_tool_available(["pactfix", "--version"], timeout=5)


class RefactorSandbox:
    """Docker sandbox do bezpiecznego testowania refaktoryzacji."""

    def __init__(self, project_dir: Path, image: str = _DOCKER_IMAGE) -> None:
        self.project_dir = project_dir.resolve()
        self.image = image
        self.container_name = f"redsl-sandbox-{id(self)}"
        self._running = False

    def start(self) -> None:
        """Uruchom sandbox z kopią projektu."""
        if not _docker_available():
            raise DockerNotFoundError(
                "Docker is not running or not installed. "
                "Install Docker Desktop / Docker Engine and ensure the daemon is running."
            )

        logger.info("Starting sandbox container: %s", self.container_name)

        subprocess.run(
            [
                "docker", "run", "-d",
                "--name", self.container_name,
                "-v", f"{self.project_dir}:/mnt/project:ro",
                "-w", "/workspace",
                self.image,
                "sleep", "3600",
            ],
            check=True,
            capture_output=True,
        )

        subprocess.run(
            [
                "docker", "exec", self.container_name,
                "cp", "-r", "/mnt/project/.", "/workspace/",
            ],
            check=True,
            capture_output=True,
        )

        req = self.project_dir / "requirements.txt"
        if req.exists():
            subprocess.run(
                [
                    "docker", "exec", self.container_name,
                    "pip", "install", "-q", "-r", "/workspace/requirements.txt",
                ],
                capture_output=True,
                timeout=180,
            )

        self._running = True
        logger.info("Sandbox ready: %s", self.container_name)

    def apply_and_test(self, proposal) -> dict:
        """Zaaplikuj propozycję w sandboxie i uruchom testy.

        Returns dict:
          applied: bool
          tests_pass: bool
          errors: list[str]
          output: str
        """
        if not self._running:
            raise SandboxError("Sandbox is not running — call start() first")

        results: dict = {"applied": False, "tests_pass": False, "errors": [], "output": ""}

        changes = getattr(proposal, "changes", [])
        if not changes:
            results["errors"].append("Proposal has no changes to apply")
            return results

        for change in changes:
            file_path = getattr(change, "file_path", None)
            refactored_code = getattr(change, "refactored_code", None)
            if not file_path or refactored_code is None:
                continue

            import tempfile
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
                encoding="utf-8",
            ) as tmp:
                tmp.write(refactored_code)
                tmp_path = tmp.name

            cp = subprocess.run(
                [
                    "docker", "cp",
                    tmp_path,
                    f"{self.container_name}:/workspace/{file_path}",
                ],
                capture_output=True,
            )
            Path(tmp_path).unlink(missing_ok=True)

            if cp.returncode != 0:
                results["errors"].append(
                    f"Failed to copy {file_path} to sandbox: {cp.stderr.decode()}"
                )
                return results

        results["applied"] = True

        if changes:
            first_file = getattr(changes[0], "file_path", None)
            if first_file:
                syntax = subprocess.run(
                    [
                        "docker", "exec", self.container_name,
                        "python", "-m", "py_compile", f"/workspace/{first_file}",
                    ],
                    capture_output=True,
                    text=True,
                )
                if syntax.returncode != 0:
                    results["errors"].append(f"Syntax error: {syntax.stderr}")
                    return results

        test_result = subprocess.run(
            [
                "docker", "exec", self.container_name,
                "python", "-m", "pytest", "/workspace/tests/", "-q", "--tb=short",
            ],
            capture_output=True,
            text=True,
            timeout=_TEST_TIMEOUT,
        )

        results["tests_pass"] = test_result.returncode == 0
        results["output"] = (test_result.stdout + test_result.stderr)[-1000:]
        if not results["tests_pass"]:
            results["errors"].append(
                f"Tests failed:\n{test_result.stdout[-500:]}"
            )

        return results

    def stop(self) -> None:
        """Zatrzymaj i usuń sandbox (ephemeral)."""
        if not self._running:
            return
        subprocess.run(
            ["docker", "rm", "-f", self.container_name],
            capture_output=True,
        )
        self._running = False
        logger.info("Sandbox stopped and removed: %s", self.container_name)

    def __enter__(self) -> "RefactorSandbox":
        self.start()
        return self

    def __exit__(self, *args) -> None:
        self.stop()


def sandbox_available() -> bool:
    """True if Docker or pactfix is available for sandbox testing."""
    return _docker_available() or _pactfix_available()
