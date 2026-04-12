"""Markdown report rendering for project scan results.

Generates prioritized markdown reports from ProjectScanResult data,
including executive summary tables, priority tier sections, and
actionable recommendations for batch refactoring workflows.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .scan import ProjectScanResult

_TIER_CRITICAL = "critical"
_TIER_HIGH = "high"
_TIER_MEDIUM = "medium"
_TIER_LOW = "low"

_TIER_BADGES = {
    _TIER_CRITICAL: "🔴 Critical",
    _TIER_HIGH: "🟠 High",
    _TIER_MEDIUM: "🟡 Medium",
    _TIER_LOW: "🟢 Low",
}


def _group_results_by_tier(results: list[ProjectScanResult]) -> dict[str, list[ProjectScanResult]]:
    """Bucket results by tier; returns dict with all four tier keys."""
    tiers: dict[str, list[ProjectScanResult]] = {t: [] for t in [_TIER_CRITICAL, _TIER_HIGH, _TIER_MEDIUM, _TIER_LOW]}
    for result in results:
        tiers[result.tier].append(result)
    return tiers


def _render_executive_summary(results: list[ProjectScanResult]) -> list[str]:
    """Render the executive-summary table section as a list of Markdown lines."""
    lines = [
        "## 📊 Executive Summary",
        "",
        "| # | Project | Tier | Files | LoC | Avg CC | Max CC | Critical | Tests | Commits/30d |",
        "|---|---------|------|------:|----:|-------:|-------:|---------:|:-----:|------------:|",
    ]
    for i, result in enumerate(results, 1):
        badge = _TIER_BADGES.get(result.tier, result.tier)
        tests_icon = "✅" if result.has_tests else "❌"
        cc_str = f"{result.avg_cc:.1f}" if result.avg_cc else "—"
        max_cc_str = str(result.max_cc) if result.max_cc else "—"
        err_note = " ⚠️" if not result.is_ok() else ""
        lines.append(
            f"| {i} | `{result.name}`{err_note} | {badge} | {result.py_files} | {result.total_loc:,} "
            f"| {cc_str} | {max_cc_str} | {result.critical_count} | {tests_icon} | {result.recent_commits} |"
        )
    lines.append("")
    return lines


def _render_priority_tiers(tiers: dict[str, list[ProjectScanResult]]) -> list[str]:
    """Render per-tier project detail sections as Markdown lines."""
    lines = ["---", "", "## 🎯 Priority Tiers", ""]
    for tier in [_TIER_CRITICAL, _TIER_HIGH, _TIER_MEDIUM, _TIER_LOW]:
        bucket = tiers[tier]
        if not bucket:
            continue
        badge = _TIER_BADGES[tier]
        lines += [f"### {badge} ({len(bucket)} projects)", ""]
        for result in bucket:
            last = f"{result.last_commit_days_ago}d ago" if result.last_commit_days_ago is not None else "unknown"
            lines += [
                f"#### `{result.name}`",
                "",
                f"- **Languages**: {', '.join(result.languages) or '—'}",
                f"- **Python files**: {result.py_files}  |  **LoC**: {result.total_loc:,}",
                f"- **Avg CC**: {result.avg_cc:.1f}  |  **Max CC**: {result.max_cc}  |  **Critical functions**: {result.critical_count}",
                f"- **Recent activity**: {result.recent_commits} commits in last 30 days  |  Last commit: {last}",
                f"- **Tests**: {'✅ yes' if result.has_tests else '❌ none found'}  |  **Toon files**: {'✅ yes' if result.has_toon else '❌ none'}",
            ]
            if result.hotspots:
                lines.append("- **Top hotspots** (CC):")
                for fname, cc in result.hotspots:
                    lines.append(f"  - `{fname}` — CC {cc}")
            lines.append("")
    return lines


def _render_analysis_errors(errors: list[ProjectScanResult]) -> list[str]:
    """Render the analysis-errors section; returns empty list when there are none."""
    if not errors:
        return []
    lines = ["---", "", "## ⚠️ Analysis Errors", ""]
    for result in errors:
        lines.append(f"- `{result.name}`: {result.error}")
    lines.append("")
    return lines


def _render_report_header(now: str, folder: Path, results: list[ProjectScanResult], ok: list[ProjectScanResult], errors: list[ProjectScanResult]) -> list[str]:
    """Render the report title and metadata header as Markdown lines."""
    return [
        "# reDSL Project Scan Report",
        "",
        f"> Generated: **{now}**  ",
        f"> Folder: `{folder}`  ",
        f"> Projects found: **{len(results)}** ({len(ok)} analysed, {len(errors)} errors)",
        "",
        "---",
        "",
    ]


def _build_recommendations(tiers: dict[str, list[ProjectScanResult]]) -> str:
    """Build a prioritised plain-text recommendations block from tier buckets."""
    parts: list[str] = []
    if tiers[_TIER_CRITICAL]:
        names = ", ".join(f"`{r.name}`" for r in tiers[_TIER_CRITICAL][:3])
        parts.append(f"1. **Immediate refactoring needed** in {names} — run `redsl refactor <path>` to apply fixes.")
    if tiers[_TIER_HIGH]:
        names = ", ".join(f"`{r.name}`" for r in tiers[_TIER_HIGH][:3])
        parts.append(f"2. **Schedule deep analysis** for {names} — use `redsl refactor <path> --dry-run` to preview changes.")
    no_tests = [r for r in tiers[_TIER_CRITICAL] + tiers[_TIER_HIGH] if not r.has_tests]
    if no_tests:
        names = ", ".join(f"`{r.name}`" for r in no_tests[:3])
        parts.append(f"3. **Add test coverage** to {names} before automated refactoring.")
    no_toon = [r for r in tiers[_TIER_CRITICAL] + tiers[_TIER_HIGH] if not r.has_toon]
    if no_toon:
        names = ", ".join(f"`{r.name}`" for r in no_toon[:3])
        parts.append(f"4. **Generate toon analysis** (`code2llm . -f toon -o project`) in {names} to unlock deeper reDSL insights.")
    if not parts:
        parts.append("All projects are in good shape! Consider running `redsl refactor --dry-run` periodically to stay ahead of complexity growth.")
    return "\n".join(parts)


def render_markdown(results: list[ProjectScanResult], folder: Path) -> str:
    """Render a markdown priority report from scan results."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    ok = [r for r in results if r.is_ok()]
    errors = [r for r in results if not r.is_ok()]
    tiers = _group_results_by_tier(ok)

    lines: list[str] = []
    lines.extend(_render_report_header(now, folder, results, ok, errors))
    lines.extend(_render_executive_summary(results))
    lines.extend(_render_priority_tiers(tiers))
    lines.extend(_render_analysis_errors(errors))
    lines.extend([
        "---",
        "",
        "## 📋 Recommended Actions",
        "",
        _build_recommendations(tiers),
        "",
        "_Report generated by [reDSL](https://github.com/wronai/redsl)_",
    ])

    return "\n".join(lines)
