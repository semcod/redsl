"""Reporting and summary generation."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .models import PyqualProjectResult


def _count_by_status(results: list[PyqualProjectResult], verdict: str) -> int:
    """Count projects matching *verdict*."""
    return sum(1 for r in results if r.verdict == verdict)


def _count_passed(results: list[PyqualProjectResult]) -> int:
    return _count_by_status(results, "success")


def _count_failed(results: list[PyqualProjectResult]) -> int:
    return _count_by_status(results, "failed")


def _count_ready(results: list[PyqualProjectResult]) -> int:
    return _count_by_status(results, "ready")


def _count_skipped(results: list[PyqualProjectResult]) -> int:
    return _count_by_status(results, "skipped")


def _aggregate_metrics(results: list[PyqualProjectResult]) -> dict[str, Any]:
    """Aggregate metrics across all results."""
    return {
        "total_py_files": sum(r.py_files for r in results),
        "total_loc": sum(r.total_loc for r in results),
        "total_errors": sum(len(r.errors) for r in results),
        "total_redsl_fixes": sum(r.redsl_fixes_applied for r in results),
        "total_gates": sum(r.gates_total for r in results),
        "total_gates_passing": sum(r.gates_passing for r in results),
    }


def _aggregate_verdicts(results: list[PyqualProjectResult]) -> dict[str, int]:
    """Aggregate verdict counts."""
    return {
        "success": _count_passed(results),
        "ready": _count_ready(results),
        "failed": _count_failed(results),
        "skipped": _count_skipped(results),
    }


def _aggregate_timing(results: list[PyqualProjectResult]) -> dict[str, Any]:
    """Aggregate timing information (placeholder for future timing data)."""
    return {
        "projects_processed": len(results),
    }


def _compute_batch_verdict(results: list[PyqualProjectResult]) -> str:
    """Compute overall batch verdict."""
    if any(r.verdict == "failed" for r in results):
        return "failed"
    if any(r.verdict == "ready" for r in results):
        return "ready"
    if results and all(r.verdict == "skipped" for r in results):
        return "skipped"
    if results:
        return "success"
    return "empty"


def _build_totals(results: list[PyqualProjectResult], metrics: dict[str, Any], verdicts: dict[str, int]) -> dict[str, Any]:
    """Build top-level totals section of summary."""
    return {
        "projects_processed": len(results),
        "projects_success": verdicts["success"],
        "projects_ready": verdicts["ready"],
        "projects_failed": verdicts["failed"],
        "projects_skipped": verdicts["skipped"],
        "pyqual_yamls_generated": sum(1 for r in results if r.pyqual_yaml_generated),
        "projects_config_valid": sum(1 for r in results if r.config_valid),
        "projects_config_fixed": sum(1 for r in results if r.config_fixed),
        "total_redsl_fixes": metrics["total_redsl_fixes"],
        "total_gates_total": metrics["total_gates"],
        "total_gates_passing": metrics["total_gates_passing"],
        "batch_verdict": _compute_batch_verdict(results),
    }


def _build_gate_pipeline_totals(results: list[PyqualProjectResult]) -> dict[str, Any]:
    """Build gate and pipeline pass counts."""
    return {
        "projects_gates_passed": sum(1 for r in results if r.gates_passed),
        "projects_pipeline_passed": sum(1 for r in results if r.pipeline_passed),
        "projects_publish_ready": sum(1 for r in results if r.publish_configured or r.pipeline_publish_passed),
        "projects_publish_passed": sum(1 for r in results if r.pipeline_publish_passed),
    }


def _build_git_totals(results: list[PyqualProjectResult]) -> dict[str, Any]:
    """Build git commit/push counts."""
    return {
        "projects_committed": sum(1 for r in results if r.git_committed),
        "projects_pushed": sum(1 for r in results if r.git_pushed),
        "projects_push_preflight_passed": sum(1 for r in results if r.push_preflight_passed),
    }


def _build_pipeline_totals(results: list[PyqualProjectResult]) -> dict[str, Any]:
    """Build pipeline and git totals section of summary."""
    totals = _build_gate_pipeline_totals(results)
    totals.update(_build_git_totals(results))
    return totals


def _build_project_detail(r: PyqualProjectResult) -> dict[str, Any]:
    """Build detail dict for a single project result."""
    return {
        "name": r.name,
        "py_files": r.py_files,
        "total_loc": r.total_loc,
        "avg_cc": r.avg_cc,
        "max_cc": r.max_cc,
        "critical": r.critical_count,
        "redsl_fixes": r.redsl_fixes_applied,
        "config_valid": r.config_valid,
        "config_fixed": r.config_fixed,
        "gates_pass": r.gates_passed,
        "gates_ratio": f"{r.gates_passing}/{r.gates_total}",
        "pipeline_pass": r.pipeline_passed,
        "publish_ready": r.publish_configured,
        "publish_pass": r.pipeline_publish_passed,
        "committed": r.git_committed,
        "pushed": r.git_pushed,
        "push_preflight_passed": r.push_preflight_passed,
        "dirty_before": r.dirty_before,
        "dirty_after": r.dirty_after,
        "verdict": r.verdict,
        "verdict_reasons": r.verdict_reasons,
        "errors": r.errors,
    }


def _build_summary(results: list[PyqualProjectResult]) -> dict[str, Any]:
    """Build aggregate summary from all project results."""
    metrics = _aggregate_metrics(results)
    verdicts = _aggregate_verdicts(results)
    summary = _build_totals(results, metrics, verdicts)
    summary.update(_build_pipeline_totals(results))
    summary["total_py_files"] = metrics["total_py_files"]
    summary["total_loc"] = metrics["total_loc"]
    summary["total_errors"] = metrics["total_errors"]
    summary["project_details"] = [_build_project_detail(r) for r in results]
    return summary


def _format_summary_verdicts(summary: dict[str, Any]) -> str:
    """Format verdict and project count lines."""
    lines = [
        f"Batch verdict:           {summary['batch_verdict']}",
        f"Projects processed:      {summary['projects_processed']}",
        f"Projects success:        {summary['projects_success']}",
        f"Projects ready:          {summary['projects_ready']}",
        f"Projects failed:         {summary['projects_failed']}",
        f"Projects skipped:        {summary['projects_skipped']}",
    ]
    return "\n".join(lines)


def _format_summary_config_and_gates(summary: dict[str, Any]) -> str:
    """Format config, gates, and fix lines."""
    lines = [
        f"pyqual.yaml generated:   {summary['pyqual_yamls_generated']}",
        f"Configs valid:           {summary['projects_config_valid']}/{summary['projects_processed']}",
    ]
    if summary['projects_config_fixed'] > 0:
        lines.append(f"Configs fixed:           {summary['projects_config_fixed']}")
    lines.append(f"ReDSL auto-fixes:        {summary['total_redsl_fixes']}")
    lines.append(f"Gates passing:           {summary['total_gates_passing']}/{summary['total_gates_total']}")
    lines.append(f"Projects all-gates-pass: {summary['projects_gates_passed']}/{summary['projects_processed']}")
    return "\n".join(lines)


def _format_summary_pipeline_and_totals(summary: dict[str, Any]) -> str:
    """Format pipeline, git, and size lines."""
    lines = []
    if summary['projects_publish_ready'] > 0:
        lines.append(f"Publish-ready:           {summary['projects_publish_ready']}")
        lines.append(f"Publish passed:          {summary['projects_publish_passed']}")
    if summary['projects_push_preflight_passed'] > 0:
        lines.append(f"Push preflight passed:   {summary['projects_push_preflight_passed']}")
    if summary['projects_committed'] > 0:
        lines.append(f"Git commits:             {summary['projects_committed']}")
        lines.append(f"Git pushes:              {summary['projects_pushed']}")
    lines.append(f"Total files:             {summary['total_py_files']}")
    lines.append(f"Total LOC:               {summary['total_loc']:,}")
    if summary["total_errors"] > 0:
        lines.append(f"Errors:                  {summary['total_errors']}")
    return "\n".join(lines)


def _print_summary(summary: dict[str, Any]) -> None:
    """Print summary to console."""
    print(f"\n{'=' * 60}")
    print("reDSL × pyqual — SUMMARY")
    print(f"{'=' * 60}")
    print(_format_summary_verdicts(summary))
    print(_format_summary_config_and_gates(summary))
    print(_format_summary_pipeline_and_totals(summary))


def _build_report_header(summary: dict[str, Any], workspace_root: Path, now: str) -> list[str]:
    """Build report header section."""
    return [
        "# reDSL × pyqual — Multi-Project Quality Report",
        "",
        f"> Generated: **{now}**  ",
        f"> Workspace: `{workspace_root}`  ",
        f"> Projects: **{summary['projects_processed']}**",
        f"> Batch verdict: **{summary['batch_verdict']}**",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|------:|",
        f"| Projects processed | {summary['projects_processed']} |",
        f"| Projects success | {summary['projects_success']} |",
        f"| Projects ready | {summary['projects_ready']} |",
        f"| Projects failed | {summary['projects_failed']} |",
        f"| Projects skipped | {summary['projects_skipped']} |",
        f"| pyqual.yaml generated | {summary['pyqual_yamls_generated']} |",
        f"| Configs valid | {summary['projects_config_valid']}/{summary['projects_processed']} |",
        f"| Configs fixed | {summary['projects_config_fixed']} |",
        f"| ReDSL auto-fixes | {summary['total_redsl_fixes']} |",
        f"| Gates passing | {summary['total_gates_passing']}/{summary['total_gates_total']} |",
        f"| Projects gates pass | {summary['projects_gates_passed']}/{summary['projects_processed']} |",
        f"| Publish-ready projects | {summary['projects_publish_ready']} |",
        f"| Publish passed | {summary['projects_publish_passed']} |",
        f"| Push preflight passed | {summary['projects_push_preflight_passed']} |",
        f"| Git commits | {summary['projects_committed']} |",
        f"| Git pushes | {summary['projects_pushed']} |",
        f"| Total .py files | {summary['total_py_files']} |",
        f"| Total LOC | {summary['total_loc']:,} |",
    ]


def _format_project_row(i: int, r: PyqualProjectResult) -> str:
    """Format a single project row for the details table."""
    config_str = "✅" if r.config_valid else ("🛠️" if r.config_fixed else "❌")
    gate_str = f"{'✅' if r.gates_passed else '❌'} {r.gates_passing}/{r.gates_total}" if r.gates_total else "—"
    pipe_str = "✅" if r.pipeline_passed else ("❌" if r.pipeline_ran else "—")
    publish_str = "✅" if r.pipeline_publish_passed else ("📝" if r.publish_configured else "—")
    git_str = "✅" if r.git_pushed else ("🔎" if r.push_preflight_passed else ("📝" if r.git_committed else "—"))
    return (
        f"| {i} | `{r.name}` | {r.py_files} | {r.total_loc:,} | {r.avg_cc:.1f} | {r.max_cc} "
        f"| {r.redsl_fixes_applied} | {config_str} | {gate_str} | {pipe_str} | {publish_str} | {git_str} | {r.verdict} |"
    )


def _build_project_table(results: list[PyqualProjectResult]) -> list[str]:
    """Build per-project details table."""
    lines = [
        "",
        "---",
        "",
        "## Per-Project Details",
        "",
        "| # | Project | Files | LOC | CC̄ | Max CC | Fixes | Config | Gates | Pipeline | Publish | Git | Verdict |",
        "|---|---------|------:|----:|----:|-------:|------:|--------|-------|----------|---------|-----|---------|",
    ]

    for i, r in enumerate(results, 1):
        lines.append(_format_project_row(i, r))
    return lines


def _build_project_notes(results: list[PyqualProjectResult]) -> list[str]:
    """Build project notes section."""
    lines = [
        "",
        "---",
        "",
        "## Project Notes",
        "",
    ]

    for r in results:
        if not (r.gate_details or r.verdict_reasons or r.errors):
            continue
        lines.append(f"### {r.name}")
        lines.append("")
        lines.append(f"- verdict: {r.verdict}")
        if r.verdict_reasons:
            lines.append(f"- verdict reasons: {', '.join(r.verdict_reasons)}")
        for error in r.errors:
            lines.append(f"- error: {error}")
        for gd in r.gate_details:
            lines.append(f"- gate: {gd['line']}")
        lines.append("")
    return lines


def _build_report_footer() -> list[str]:
    """Build report footer."""
    return [
        "---",
        "",
        "_Report generated by [reDSL](https://github.com/wronai/redsl) × [pyqual](https://github.com/wronai/pyqual)_",
    ]


def _save_report(
    results: list[PyqualProjectResult],
    summary: dict[str, Any],
    workspace_root: Path,
) -> None:
    """Save Markdown report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = _build_report_header(summary, workspace_root, now)
    lines.extend(_build_project_table(results))
    lines.extend(_build_project_notes(results))
    lines.extend(_build_report_footer())

    report_path = workspace_root / "redsl_pyqual_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport saved to: {report_path}")
