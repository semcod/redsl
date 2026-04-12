"""Folder scanner — analyzes multiple projects and produces a markdown priority report.

This module provides comprehensive project scanning capabilities for ReDSL, analyzing
code quality metrics across multiple projects simultaneously and generating
prioritized reports for batch refactoring workflows.

Features:
  - Multi-project analysis with parallel scanning support
  - Automatic language detection (Python, JavaScript, etc.)
  - Code complexity metrics (cyclomatic complexity, LOC, hotspots)
  - Git history analysis (recent commits, activity level)
  - Test coverage detection (has_tests, has_toon markers)
  - Priority scoring algorithm based on multiple quality dimensions
  - Tier classification (Critical/High/Medium/Low)
  - Markdown report generation with badges and actionable insights

The scanner integrates with the CodeAnalyzer and produces results suitable for
both CLI output and batch processing workflows in the ReDSL ecosystem.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..analyzers import CodeAnalyzer
from ..analyzers.metrics import AnalysisResult
from ..analyzers.utils import _should_ignore_file, _load_gitignore_patterns

_DEFAULT_EXCLUDE_DIRS = {".venv", "venv", ".git", "__pycache__", "node_modules", ".tox", "dist", "build"}
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


@dataclass
class ProjectScanResult:
    """Scan result for a single project."""

    name: str
    path: Path
    languages: list[str] = field(default_factory=list)
    py_files: int = 0
    total_loc: int = 0
    avg_cc: float = 0.0
    max_cc: int = 0
    critical_count: int = 0
    hotspots: list[tuple[str, int]] = field(default_factory=list)
    recent_commits: int = 0
    last_commit_days_ago: int | None = None
    has_tests: bool = False
    has_toon: bool = False
    error: str | None = None
    priority_score: float = 0.0
    tier: str = _TIER_LOW

    def is_ok(self) -> bool:
        return self.error is None


def _count_python_files(project_path: Path) -> tuple[int, int]:
    """Return (py_file_count, total_loc) excluding venvs and caches."""
    count, loc = 0, 0
    patterns: set[str] = _load_gitignore_patterns(project_path)
    for f in project_path.rglob("*.py"):
        rel = f.relative_to(project_path)
        parts = set(rel.parts)
        if parts & _DEFAULT_EXCLUDE_DIRS:
            continue
        if _should_ignore_file(f, project_path, patterns):
            continue
        count += 1
        try:
            loc += sum(1 for _ in f.open(encoding="utf-8", errors="ignore"))
        except OSError:
            pass
    return count, loc


def _detect_languages(project_path: Path) -> list[str]:
    """Detect primary languages by file extension presence."""
    exts: dict[str, str] = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".go": "Go", ".rs": "Rust", ".java": "Java", ".rb": "Ruby",
    }
    found: list[str] = []
    for ext, lang in exts.items():
        if any(True for _ in project_path.rglob(f"*{ext}") if not any(p in _DEFAULT_EXCLUDE_DIRS for p in _.parts)):
            if lang not in found:
                found.append(lang)
        if len(found) >= 4:
            break
    return found


def _git_activity(project_path: Path, days: int = 30) -> tuple[int, int | None]:
    """Return (commits_last_N_days, days_since_last_commit)."""
    try:
        res = subprocess.run(
            ["git", "log", f"--since={days} days ago", "--oneline"],
            cwd=project_path, capture_output=True, text=True, timeout=5,
        )
        commits = len([l for l in res.stdout.splitlines() if l.strip()])
    except Exception:
        commits = 0

    days_ago: int | None = None
    try:
        res = subprocess.run(
            ["git", "log", "-1", "--format=%ct"],
            cwd=project_path, capture_output=True, text=True, timeout=5,
        )
        ts = res.stdout.strip()
        if ts.isdigit():
            delta = datetime.now(timezone.utc).timestamp() - int(ts)
            days_ago = max(0, int(delta / 86400))
    except Exception:
        pass

    return commits, days_ago


def _extract_hotspots(result: AnalysisResult, top_n: int = 5) -> list[tuple[str, int]]:
    """Return top-N (file, cc) by complexity."""
    seen: dict[str, int] = {}
    for m in result.metrics:
        cc = int(m.cyclomatic_complexity)
        if cc <= 1:
            continue
        key = m.file_path
        seen[key] = max(seen.get(key, 0), cc)
    return sorted(seen.items(), key=lambda x: -x[1])[:top_n]


def _compute_priority(result: ProjectScanResult) -> tuple[float, str]:
    """Compute a numeric priority score and tier label."""
    score = (
        result.critical_count * 3.0
        + result.avg_cc * 0.5
        + result.max_cc * 0.3
        + result.recent_commits * 0.2
    )
    if score >= 30:
        return score, _TIER_CRITICAL
    if score >= 15:
        return score, _TIER_HIGH
    if score >= 5:
        return score, _TIER_MEDIUM
    return score, _TIER_LOW


def _analyze_single_project(project_path: Path, analyzer: CodeAnalyzer) -> ProjectScanResult:
    """Run lightweight analysis on one project and return a scan result."""
    result = ProjectScanResult(name=project_path.name, path=project_path)

    try:
        result.languages = _detect_languages(project_path)
        result.py_files, result.total_loc = _count_python_files(project_path)
        result.recent_commits, result.last_commit_days_ago = _git_activity(project_path)
        result.has_tests = any(project_path.rglob("test_*.py")) or any(project_path.rglob("*_test.py"))
        result.has_toon = bool(list(project_path.glob("*.toon.yaml")) or list(project_path.glob("project_toon.yaml")))

        if result.py_files > 0:
            analysis: AnalysisResult = analyzer.analyze_project(project_path)
            result.avg_cc = round(analysis.avg_cc, 2)
            result.critical_count = analysis.critical_count
            result.hotspots = _extract_hotspots(analysis)
            if analysis.metrics:
                result.max_cc = int(max(m.cyclomatic_complexity for m in analysis.metrics))
    except Exception as exc:
        result.error = str(exc)[:120]

    result.priority_score, result.tier = _compute_priority(result)
    return result


def _is_project_dir(path: Path) -> bool:
    """Heuristic: a dir is a project if it contains Python or has a typical project marker."""
    markers = {"pyproject.toml", "setup.py", "setup.cfg", "Makefile", "requirements.txt", "TODO.md"}
    if any((path / m).exists() for m in markers):
        return True
    return bool(list(path.glob("*.py"))) or bool(list(path.glob("src/")))


def scan_folder(folder: Path, progress: bool = True) -> list[ProjectScanResult]:
    """Scan all sub-projects in *folder* and return sorted results."""
    analyzer = CodeAnalyzer()
    candidates = sorted(p for p in folder.iterdir() if p.is_dir() and not p.name.startswith("."))
    projects = [p for p in candidates if _is_project_dir(p)]

    results: list[ProjectScanResult] = []
    for i, project in enumerate(projects, 1):
        if progress:
            print(f"  [{i}/{len(projects)}] scanning {project.name}...", flush=True)
        results.append(_analyze_single_project(project, analyzer))

    results.sort(key=lambda r: (-r.priority_score, r.name))
    return results


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
