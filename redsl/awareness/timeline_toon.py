"""Toon file collection and processing for timeline analysis."""

from __future__ import annotations

import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from redsl.awareness.timeline_git import GitTimelineProvider
from redsl.awareness.timeline_models import MetricPoint
from redsl.analyzers import CodeAnalyzer

logger = logging.getLogger(__name__)


class ToonCollector:
    """Collects and processes toon files from git history."""

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
        git_provider: GitTimelineProvider,
        analyzer: CodeAnalyzer | None = None,
    ) -> None:
        self.project_path = project_path
        self.git_provider = git_provider
        self.analyzer = analyzer or CodeAnalyzer()

    def snapshot_for_commit(
        self,
        commit_hash: str,
        timestamp: int,
        message: str,
    ) -> MetricPoint | None:
        """Build a MetricPoint from toon content at a specific commit."""
        contents = self._collect_toon_contents(commit_hash)
        if not contents["project_toon"] and not contents["analysis_toon"]:
            return None

        analysis = self.analyzer.analyze_from_toon_content(
            project_toon=contents["project_toon"],
            duplication_toon=contents["duplication_toon"],
            validation_toon=contents["validation_toon"],
        )
        if analysis.total_files == 0 and not analysis.metrics and not analysis.alerts:
            return None

        commit_time = datetime.fromtimestamp(timestamp or 0, tz=timezone.utc).isoformat()
        validation_issues = sum(m.linter_errors + m.linter_warnings for m in analysis.metrics)
        project_name = analysis.project_name or self.project_path.name

        return MetricPoint(
            commit_hash=commit_hash,
            timestamp=commit_time,
            commit_message=message,
            project_name=project_name,
            total_files=analysis.total_files,
            total_lines=analysis.total_lines,
            avg_cc=analysis.avg_cc,
            critical_count=analysis.critical_count,
            module_count=len(analysis.metrics),
            duplicate_count=len(analysis.duplicates),
            validation_issues=validation_issues,
            raw={
                "alerts": list(analysis.alerts),
                "duplicates": list(analysis.duplicates),
                "recommendations": list(analysis.recommendations),
            },
        )

    def _collect_toon_contents(self, commit_hash: str) -> dict[str, str]:
        rel_path = self.git_provider._project_rel_path()
        args = [
            "git",
            "-C",
            str(self.git_provider.repo_root or self.project_path),
            "ls-tree",
            "-r",
            "--name-only",
            commit_hash,
            "--",
            rel_path if rel_path != "." else ".",
        ]
        try:
            result = subprocess.run(args, capture_output=True, text=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            return {"project_toon": "", "duplication_toon": "", "validation_toon": "", "analysis_toon": ""}

        candidates = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        contents = self._empty_toon_contents()

        for rel_file in self._sorted_toon_candidates(candidates):
            content = self.git_provider._git_show(commit_hash, rel_file)
            if not content.strip():
                continue
            self._store_toon_content(contents, rel_file, content)

        if not contents["project_toon"] and contents["analysis_toon"]:
            contents["project_toon"] = contents["analysis_toon"]

        return contents

    @staticmethod
    def _empty_toon_contents() -> dict[str, str]:
        return {
            "project_toon": "",
            "analysis_toon": "",
            "duplication_toon": "",
            "validation_toon": "",
        }

    def _store_toon_content(self, contents: dict[str, str], rel_file: str, content: str) -> None:
        bucket = self._toon_bucket(Path(rel_file).name.lower())
        if bucket is None:
            return
        if bucket == "project_toon" and contents["project_toon"]:
            return
        contents[bucket] = content

    def _toon_bucket(self, name: str) -> str | None:
        if self._is_duplication_file(name):
            return "duplication_toon"
        if self._is_validation_file(name):
            return "validation_toon"
        if "analysis" in name:
            return "analysis_toon"
        if "project" in name and "toon" in name:
            return "project_toon"
        if "toon" in name:
            return "project_toon"
        return None

    def _sorted_toon_candidates(self, candidates: Sequence[str]) -> list[str]:
        return sorted(candidates, key=self._toon_candidate_priority)

    def _toon_candidate_priority(self, candidate: str) -> tuple[int, str]:
        """Backward-compatible helper used by existing tests."""
        name = Path(candidate).name.lower()
        if name in self._TOON_PRIORITY:
            return (0, name)
        if "project" in name and "toon" in name:
            return (1, name)
        if "analysis" in name and "toon" in name:
            return (2, name)
        if "duplication" in name and "toon" in name:
            return (3, name)
        if "validation" in name and "toon" in name:
            return (4, name)
        if "toon" in name:
            return (5, name)
        return (6, name)

    @staticmethod
    def _is_duplication_file(name: str) -> bool:
        return "duplication" in name or "redup" in name or "duplicate" in name

    @staticmethod
    def _is_validation_file(name: str) -> bool:
        return "validation" in name or name.startswith("lint")


__all__ = ["ToonCollector"]
