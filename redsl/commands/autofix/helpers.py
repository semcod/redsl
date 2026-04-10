"""Helper utilities for autofix package."""

from __future__ import annotations

from pathlib import Path

from ...autonomy.quality_gate import _collect_python_files as _collect_python_files_impl, _measure_metrics as _measure_metrics_impl


def _collect_python_files(project: Path) -> list[Path]:
    """Collect all Python files in project."""
    return _collect_python_files_impl(project)


def _measure_metrics(project: Path, py_files: list[Path]) -> dict:
    """Measure code metrics for project."""
    return _measure_metrics_impl(project, py_files)
