"""Batch runner for autofix package."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .discovery import _find_packages
from .models import ProjectFixResult
from .pipeline import _process_project
from .reporting import _build_summary, _print_summary, _save_reports


def run_autofix_batch(
    semcod_root: Path,
    max_changes: int = 30,
) -> dict[str, Any]:
    """Run full autofix pipeline on all semcod packages."""
    packages = _find_packages(semcod_root)
    print(f"\nFound {len(packages)} packages in {semcod_root}")
    print(f"Max changes per project: {max_changes}")
    print("=" * 60)

    all_results: list[ProjectFixResult] = []

    for i, package in enumerate(packages, 1):
        print(f"\n[{i}/{len(packages)}] {package.name}")
        print("-" * 40)

        result = _process_project(package, max_changes)
        all_results.append(result)

        # Brief status
        reduction = result.todo_issues_before - result.todo_issues_after
        status_parts = []
        if result.todo_generated:
            status_parts.append(f"TODO generated ({result.todo_issues_before} issues)")
        if result.hybrid_applied > 0:
            status_parts.append(f"{result.hybrid_applied} hybrid fixes")
        if result.gate_fixed > 0:
            status_parts.append(f"{result.gate_fixed} gate fixes")
        if reduction > 0:
            status_parts.append(f"TODO: {result.todo_issues_before}->{result.todo_issues_after}")
        if not status_parts:
            status_parts.append("no changes needed")

        print(f"  -> {', '.join(status_parts)}")

    # Summary
    summary = _build_summary(all_results)
    _print_summary(summary, all_results)
    _save_reports(all_results, summary, semcod_root)

    return summary
