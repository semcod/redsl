"""Batch runner and command utilities."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

# Import submodules for monkeypatch support in tests
from . import discovery, pipeline, reporting
from .utils import (
    run_cmd as _run_cmd,
    git_status_lines as _git_status_lines,
    resolve_profile as _resolve_profile,
    AUTO_PROFILE as _AUTO_PROFILE,
    DEFAULT_PROFILE as _DEFAULT_PROFILE,
    FULL_PROFILE as _FULL_PROFILE,
    PUBLISH_PROFILE as _PUBLISH_PROFILE,
)


def _pyqual_cli_available() -> bool:
    """Check if pyqual CLI is available."""
    return shutil.which("pyqual") is not None


def _print_batch_header(
    workspace_root: Path,
    project_count: int,
    pyqual_ok: bool,
    pipeline_mode: bool,
    git_push: bool,
    publish: bool,
    fix_config: bool,
    dry_run: bool,
    skip_dirty: bool,
    profile: str,
) -> None:
    """Print batch execution header with configuration summary."""
    print(f"\n{'=' * 60}")
    print(f"reDSL × pyqual — Multi-Project Quality Pipeline")
    print(f"{'=' * 60}")
    print(f"Workspace:      {workspace_root}")
    print(f"Projects found: {project_count}")
    print(f"pyqual CLI:     {'✅ available' if pyqual_ok else '⚠️  not found (install: pip install pyqual)'}")
    print(f"Pipeline mode:  {'full (fix+verify+publish)' if pipeline_mode else 'gates only'}")
    print(f"Git push:       {'enabled' if git_push else 'disabled'}")
    print(f"Publish:        {'enabled' if publish else 'disabled'}")
    print(f"Config fix:     {'enabled' if fix_config else 'disabled'}")
    print(f"Dry run:        {'enabled' if dry_run else 'disabled'}")
    print(f"Skip dirty:     {'enabled' if skip_dirty else 'disabled'}")
    print(f"Profile:        {profile}")
    print(f"{'=' * 60}")


def _status_config_parts(result: Any) -> list[str]:
    """Build config-related status parts."""
    if not result.config_valid:
        return ["config FAIL"]
    if result.config_fixed:
        return ["config fixed"]
    return []


def _status_gates_parts(result: Any) -> list[str]:
    """Build gates/pipeline status parts."""
    parts = []
    if result.gates_passed:
        parts.append(f"gates PASS ({result.gates_passing}/{result.gates_total})")
    elif result.gates_total > 0:
        parts.append(f"gates FAIL ({result.gates_passing}/{result.gates_total})")
    if result.pipeline_passed:
        parts.append("pipeline OK")
    elif result.pipeline_ran:
        parts.append("pipeline FAIL")
    return parts


def _status_git_parts(result: Any) -> list[str]:
    """Build git/publish status parts."""
    parts = []
    if result.push_preflight_passed:
        parts.append("push preflight OK")
    if result.pipeline_publish_passed:
        parts.append("publish OK")
    if result.git_committed:
        parts.append("committed")
    if result.git_pushed:
        parts.append("pushed")
    return parts


def _format_project_status(result: Any) -> str:
    """Format project result status into readable parts."""
    parts = []
    if result.skipped:
        parts.append(f"skipped: {result.skip_reason}")
    if result.pyqual_yaml_generated:
        parts.append("pyqual.yaml generated")
    parts.extend(_status_config_parts(result))
    if result.redsl_fixes_applied > 0:
        parts.append(f"{result.redsl_fixes_applied} ReDSL fixes")
    parts.extend(_status_gates_parts(result))
    parts.extend(_status_git_parts(result))
    parts.append(f"verdict={result.verdict}")
    if not parts:
        parts.append(f"{result.py_files} files, CC̄={result.avg_cc}")
    return ", ".join(parts)


def run_pyqual_batch(
    workspace_root: Path,
    max_fixes: int = 30,
    run_pipeline: bool = False,
    git_push: bool = False,
    limit: int = 0,
    profile: str = _AUTO_PROFILE,
    publish: bool = False,
    fix_config: bool = False,
    include: tuple[str, ...] | list[str] | None = None,
    exclude: tuple[str, ...] | list[str] | None = None,
    dry_run: bool = False,
    skip_dirty: bool = False,
    fail_fast: bool = False,
) -> dict[str, Any]:
    """Run ReDSL + pyqual on all projects in workspace."""
    # Use module-level imports for testability
    _find_packages = discovery._find_packages
    _filter_packages = discovery._filter_packages
    process_project = pipeline.process_project
    _build_summary = reporting._build_summary
    _print_summary = reporting._print_summary
    _save_report = reporting._save_report

    packages = _filter_packages(_find_packages(workspace_root), include=include, exclude=exclude)
    if limit > 0:
        packages = packages[:limit]
    pyqual_ok = _pyqual_cli_available()
    resolved_profile = _resolve_profile(profile, run_pipeline, publish)
    effective_pipeline = run_pipeline or publish

    _print_batch_header(
        workspace_root, len(packages), pyqual_ok, effective_pipeline,
        git_push, publish, fix_config, dry_run, skip_dirty, resolved_profile
    )

    from .models import PyqualProjectResult
    all_results: list[PyqualProjectResult] = []

    for i, package in enumerate(packages, 1):
        print(f"\n[{i}/{len(packages)}] {package.name}")
        print("-" * 40)

        result = process_project(
            package, max_fixes, effective_pipeline, git_push, resolved_profile,
            publish, fix_config, dry_run, skip_dirty, pyqual_ok
        )
        all_results.append(result)

        print(f"  → {_format_project_status(result)}")

        if fail_fast and result.verdict == "failed":
            print("  → fail-fast triggered, stopping batch")
            break

    summary = _build_summary(all_results)
    _print_summary(summary)
    _save_report(all_results, summary, workspace_root)

    return summary
