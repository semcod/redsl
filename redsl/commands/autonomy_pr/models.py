"""Data models for the autonomous PR workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class _CloneResult:
    clone_path: Path | None
    error: str = ""


@dataclass
class _AnalysisResult:
    success: bool
    error: str = ""


@dataclass
class _ApplyResult:
    success: bool
    real_changes: list[str]
    generated_changes: list[str]
    error: str = ""


@dataclass
class _CommitResult:
    resolved_branch_name: str
    success: bool
    error: str = ""


@dataclass
class _PushResult:
    success: bool
    error: str = ""


@dataclass
class _ValidationResult:
    success: bool
    error: str = ""
    details: list[dict] = field(default_factory=list)
