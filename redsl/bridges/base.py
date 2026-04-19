"""redsl/bridges/base.py — shared base for all CLI tool bridges.

Eliminates the ~7× duplicated is_available() pattern across:
  analyzers/code2llm_bridge, analyzers/radon_analyzer, analyzers/redup_bridge,
  commands/batch_pyqual/config_gen, commands/batch_pyqual/runner,
  validation/regix_bridge, validation/vallm_bridge.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from abc import ABC
from subprocess import TimeoutExpired


class CliBridge(ABC):
    """Base class for bridges wrapping external CLI tools.

    Subclasses set ``cli_name`` (and optionally ``check_args``) to get a
    working ``is_available()`` without any boilerplate.

    Minimal subclass::

        class RedupBridge(CliBridge):
            cli_name = "redup"
    """

    #: Name of the CLI executable (must be set by subclass).
    cli_name: str

    #: Arguments passed to the CLI for the availability check.
    #: Defaults to ``["--help"]`` which works for most tools.
    check_args: list[str] = ["--help"]

    #: Timeout (seconds) for the availability probe.
    check_timeout: int = 5

    # ------------------------------------------------------------------
    # Availability
    # ------------------------------------------------------------------

    @classmethod
    def is_available(cls) -> bool:
        """Return True if the CLI tool is installed *and* responds correctly.

        Uses ``check_args`` instead of bare ``shutil.which`` — the tool may
        exist in PATH but crash on startup (e.g. import error in a Python CLI).
        """
        if shutil.which(cls.cli_name) is None:
            return False
        try:
            proc = subprocess.run(
                [cls.cli_name, *cls.check_args],
                capture_output=True,
                text=True,
                timeout=cls.check_timeout,
            )
            return proc.returncode == 0
        except (OSError, TimeoutExpired, Exception):
            return False

    # ------------------------------------------------------------------
    # Helpers shared by multiple bridges (dup group #11)
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_json(output: str) -> dict:
        """Parse first valid JSON object from *output* (stdout or stderr).

        Tries the whole string first; if that fails, scans line-by-line for
        a line that starts with ``{`` or ``[``.
        """
        text = output.strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        for line in text.splitlines():
            line = line.strip()
            if line.startswith(("{", "[")):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        return {}
