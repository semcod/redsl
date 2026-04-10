"""Batch report formatters."""

from __future__ import annotations

import json
from typing import Any, Dict, List
from pathlib import Path

import yaml

from .core import _get_timestamp


def format_batch_results(results: List[Dict[str, Any]], format: str = "text") -> str:
    """Format batch processing results."""
    if format == "yaml":
        return yaml.dump({"batch_results": results}, default_flow_style=False, sort_keys=False)
    elif format == "json":
        return json.dumps({"batch_results": results}, indent=2, default=str)
    else:
        # Rich text format
        output = ["\n=== BATCH PROCESSING RESULTS ===\n"]

        for i, result in enumerate(results, 1):
            output.append(f"{i}. Project: {result.get('project_name', 'Unknown')}")
            output.append(f"   Status: {result.get('status', 'Unknown')}")
            output.append(f"   Files processed: {result.get('files_processed', 0)}")
            output.append(f"   Changes applied: {result.get('changes_applied', 0)}")
            if result.get('error'):
                output.append(f"   Error: {result['error']}")
            output.append("")

        # Summary
        total = len(results)
        successful = sum(1 for r in results if r.get('status') == 'success')
        output.append(f"\nSummary: {successful}/{total} projects processed successfully")

        return "\n".join(output)


def _as_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _batch_detail_name(detail: Dict[str, Any]) -> str:
    return detail.get("name", detail.get("project", "Unknown"))


def _batch_report_totals(report: Dict[str, Any], details: list[Dict[str, Any]]) -> tuple[int, int, int, int, int]:
    total_before = _as_int(report.get("total_before"), sum(_as_int(d.get("before_issues")) for d in details))
    total_after = _as_int(report.get("total_after"), sum(_as_int(d.get("after_issues")) for d in details))
    total_applied = _as_int(
        report.get("total_applied"),
        sum(_as_int(d.get("applied", d.get("changes_applied"))) for d in details),
    )
    total_decisions = _as_int(
        report.get("total_decisions"),
        sum(_as_int(d.get("decisions", d.get("quality_decisions"))) for d in details),
    )
    total_errors = _as_int(report.get("total_errors"), sum(_as_int(d.get("errors")) for d in details))
    return total_before, total_after, total_applied, total_decisions, total_errors


def _batch_header_lines(
    title: str,
    now: str,
    root: Path,
    projects_processed: int,
    total_decisions: int,
    total_applied: int,
    total_errors: int,
) -> list[str]:
    return [
        f"# {title}",
        "",
        f"> Generated: **{now}**  ",
        f"> Root: `{root}`  ",
        f"> Projects processed: **{projects_processed}**  ",
        f"> Decisions: **{total_decisions}**  ",
        f"> Applied: **{total_applied}**  ",
        f"> Errors: **{total_errors}**  ",
        "",
        "---",
        "",
    ]


def _batch_summary_lines(
    total_before: int,
    total_after: int,
    total_decisions: int,
    total_applied: int,
    total_errors: int,
) -> list[str]:
    return [
        "## Summary",
        "",
        f"- TODO issues before: **{total_before}**",
        f"- TODO issues after: **{total_after}**",
        f"- TODO reduction: **{total_before - total_after}**",
        f"- Decisions: **{total_decisions}**",
        f"- Applied changes: **{total_applied}**",
        f"- Errors: **{total_errors}**",
        "",
    ]


def _batch_project_lines(details: list[Dict[str, Any]]) -> list[str]:
    if not details:
        return []

    lines = [
        "## Projects",
        "",
        "| Project | Decisions | Applied | TODO before | TODO after | Δ TODO | Errors |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for detail in details:
        before = _as_int(detail.get("before_issues"), 0)
        after = _as_int(detail.get("after_issues"), 0)
        reduction = detail.get("todo_reduction")
        if reduction is None:
            reduction = before - after
        decisions_count = _as_int(detail.get("decisions", detail.get("quality_decisions")))
        applied = _as_int(detail.get("applied", detail.get("changes_applied")))
        errors = _as_int(detail.get("errors"))
        lines.append(
            f"| `{_batch_detail_name(detail)}` | "
            f"{decisions_count} | {applied} | {before} | {after} | {reduction} | {errors} |"
        )
    lines.append("")
    return lines


def _batch_top_improvement_lines(details: list[Dict[str, Any]]) -> list[str]:
    improvements = sorted(
        details,
        key=lambda item: _as_int(
            item.get("todo_reduction"),
            _as_int(item.get("before_issues")) - _as_int(item.get("after_issues")),
        ),
        reverse=True,
    )
    improvements = [
        item for item in improvements
        if _as_int(item.get("todo_reduction"), _as_int(item.get("before_issues")) - _as_int(item.get("after_issues"))) > 0
    ]
    if not improvements:
        return []

    lines = ["## Top improvements", ""]
    for detail in improvements[:5]:
        before = _as_int(detail.get("before_issues"), 0)
        after = _as_int(detail.get("after_issues"), 0)
        reduction = _as_int(detail.get("todo_reduction"), before - after)
        lines.append(
            f"- `{_batch_detail_name(detail)}`: **{reduction}** fewer TODOs "
            f"({before} → {after})"
        )
    lines.append("")
    return lines


def _batch_error_lines(details: list[Dict[str, Any]]) -> list[str]:
    errors = [detail for detail in details if _as_int(detail.get("errors")) > 0]
    if not errors:
        return []

    lines = ["## Errors", ""]
    for detail in errors:
        lines.append(f"- `{_batch_detail_name(detail)}`: {detail.get('errors')} errors")
    lines.append("")
    return lines


def format_batch_report_markdown(report: Dict[str, Any], root: Path, title: str) -> str:
    """Format a batch run report as Markdown."""
    from datetime import datetime

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    details = list(report.get("project_details", []))
    total_before, total_after, total_applied, total_decisions, total_errors = _batch_report_totals(report, details)

    lines: list[str] = []
    lines.extend(
        _batch_header_lines(
            title,
            now,
            root,
            report.get("projects_processed", len(details)),
            total_decisions,
            total_applied,
            total_errors,
        )
    )
    lines.extend(_batch_summary_lines(total_before, total_after, total_decisions, total_applied, total_errors))
    lines.extend(_batch_project_lines(details))
    lines.extend(_batch_top_improvement_lines(details))
    lines.extend(_batch_error_lines(details))

    lines.extend([
        "---",
        "",
        "_Report generated by [reDSL](https://github.com/wronai/redsl)_",
    ])
    return "\n".join(lines)
