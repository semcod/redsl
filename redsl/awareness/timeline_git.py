"""Git operations for timeline analysis."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Sequence

from redsl.awareness.timeline_models import MetricPoint
from redsl.analyzers import CodeAnalyzer

logger = logging.getLogger(__name__)


class GitTimelineProvider:
    """Provides git-based timeline data."""

    _TOON_PRIORITY = (
        "project_toon.yaml",
        "analysis.toon.yaml",
        "project.toon.yaml",
        "analysis_toon.yaml",
        "project_toon.toon",
        "analysis_toon.toon",
    )

    def __init__(
        self,
        project_path: Path,
        analyzer: CodeAnalyzer | None = None,
    ) -> None:
        self.project_path = Path(project_path).resolve()
        self.analyzer = analyzer or CodeAnalyzer()
        self.repo_root = self._resolve_repo_root()

    def _resolve_repo_root(self) -> Path | None:
        """Resolve repository root, returning None when git is unavailable."""
        try:
            result = subprocess.run(
                ["git", "-C", str(self.project_path), "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            return None

        root = result.stdout.strip()
        if not root:
            return None
        return Path(root).resolve()

    def _project_rel_path(self) -> str:
        if self.repo_root is None:
            return "."
        try:
            rel = self.project_path.relative_to(self.repo_root)
        except ValueError:
            return "."
        return "." if str(rel) == "." else str(rel)

    def _git_log(self, depth: int) -> list[tuple[str, int, str]]:
        rel_path = self._project_rel_path()
        args = [
            "git",
            "-C",
            str(self.repo_root or self.project_path),
            "log",
            "--reverse",
            f"--max-count={depth}",
            "--format=%H%x1f%ct%x1f%s",
        ]
        if rel_path != ".":
            args.extend(["--", rel_path])
        else:
            args.extend(["--", "."])

        try:
            result = subprocess.run(args, capture_output=True, text=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            logger.info("git log failed for %s", self.project_path)
            return []

        commits: list[tuple[str, int, str]] = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split("\x1f")
            if len(parts) < 3:
                continue
            commit_hash, timestamp_text, message = parts[0], parts[1], parts[2]
            try:
                timestamp = int(timestamp_text)
            except ValueError:
                timestamp = 0
            commits.append((commit_hash, timestamp, message))
        return commits

    def _git_show(self, commit_hash: str, rel_file: str) -> str:
        try:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(self.repo_root or self.project_path),
                    "show",
                    f"{commit_hash}:{rel_file}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            return ""
        return result.stdout

    @staticmethod
    def _is_duplication_file(name: str) -> bool:
        return "duplication" in name or "redup" in name or "duplicate" in name

    @staticmethod
    def _is_validation_file(name: str) -> bool:
        return "validation" in name or name.startswith("lint")


__all__ = ["GitTimelineProvider"]
