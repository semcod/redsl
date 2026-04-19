"""One-click Audit — pełny flow: connect → scan → grade report → badge."""

from __future__ import annotations

import time
from typing import Any

from ._common import load_example_yaml, parse_scenario, print_banner


# -- grade helpers -----------------------------------------------------------

_PRIORITY_ICON = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}


def _compute_score(metrics: dict[str, Any]) -> float:
    """Heuristic 0-100 score from raw metrics."""
    cc_score = max(0.0, 1.0 - metrics.get("avg_cc", 0) / 25.0)
    crit_score = max(0.0, 1.0 - metrics.get("critical_functions", 0) / 12.0)
    dup_score = max(0.0, 1.0 - metrics.get("duplicate_lines_pct", 0) / 20.0)
    sec_score = max(0.0, 1.0 - metrics.get("security_issues", 0) / 10.0)
    type_score = metrics.get("type_coverage_pct", 50) / 100.0
    raw = (
        cc_score * 0.30
        + crit_score * 0.20
        + dup_score * 0.15
        + sec_score * 0.20
        + type_score * 0.15
    )
    return round(min(100.0, max(0.0, raw * 100)), 1)


def _grade_for_score(score: float, thresholds: dict[str, dict]) -> str:
    for grade in ("A+", "A", "B", "C", "D", "F"):
        if score >= thresholds.get(grade, {}).get("min_score", 0):
            return grade
    return "F"


_GRADE_ART = {
    "A+": ("🟢", "██████████"),
    "A":  ("🟢", "████████░░"),
    "B":  ("🟡", "██████░░░░"),
    "C":  ("🟠", "████░░░░░░"),
    "D":  ("🔴", "██░░░░░░░░"),
    "F":  ("⛔", "░░░░░░░░░░"),
}


# -- step helpers ------------------------------------------------------------

def _print_connect_section(repo: dict[str, Any]) -> None:
    print(f"\n  📡 Connecting to GitHub …")
    print(f"     {repo['owner']}/{repo['name']}  ({repo.get('language', '?')}, ⭐ {repo.get('stars', '?')})")
    print(f"     Branch: {repo.get('branch', 'main')}")


def _print_scan_phases(phases: list[dict[str, Any]]) -> None:
    print(f"\n  🔄 Skanowanie …")
    total_ms = 0
    for phase in phases:
        ms = phase.get("duration_ms", 500)
        total_ms += ms
        sec = ms / 1000
        print(f"     {phase.get('icon', '▸')} {phase['name']:.<40s} {sec:.1f}s")
        time.sleep(min(sec * 0.05, 0.05))
    print(f"     ✅ Gotowe w {total_ms / 1000:.1f}s")


def _print_grade_box(score: float, grade: str) -> None:
    icon, bar = _GRADE_ART.get(grade, ("?", "░░░░░░░░░░"))
    print(f"\n  ┌─────────────────────────────────────────────┐")
    print(f"  │               AUDIT REPORT                   │")
    print(f"  │                                               │")
    print(f"  │         {icon}  Grade: {grade:>2s}   Score: {score:5.1f}         │")
    print(f"  │            [{bar}]              │")
    print(f"  │                                               │")
    print(f"  └─────────────────────────────────────────────┘")


def _print_metrics_table(metrics: dict[str, Any]) -> None:
    print(f"\n  📊 Metryki:")
    print(f"  {'─' * 50}")
    rows = [
        ("Pliki", metrics.get("total_files")),
        ("Linie kodu", f"{metrics.get('total_lines', 0):,}"),
        ("Średni CC", metrics.get("avg_cc")),
        ("Max CC", metrics.get("max_cc")),
        ("Krytyczne funkcje", metrics.get("critical_functions")),
        ("Duplikacje", f"{metrics.get('duplicate_lines_pct', 0)}%  ({metrics.get('duplicated_blocks', 0)} bloków)"),
        ("Problemy security", metrics.get("security_issues")),
        ("Type coverage", f"{metrics.get('type_coverage_pct', 0)}%"),
        ("Nieużywane importy", metrics.get("unused_imports")),
        ("Brakujące docstringi", metrics.get("missing_docstrings")),
    ]
    for label, value in rows:
        print(f"     {label:.<35s} {value}")


def _print_recommendations(recs: list[dict[str, Any]]) -> None:
    print(f"\n  💡 Rekomendacje ({len(recs)}):")
    print(f"  {'─' * 50}")
    for i, rec in enumerate(recs, 1):
        prio = rec.get("priority", "medium")
        icon_p = _PRIORITY_ICON.get(prio, "⚪")
        fix = " [autofix]" if rec.get("auto_fixable") else ""
        print(f"\n  {icon_p} [{i}] {rec['title']}{fix}")
        print(f"      {rec.get('description', '')}")
        if rec.get("estimated_impact"):
            print(f"      → {rec['estimated_impact']}")


def _print_badge(grade: str, badge_conf: dict[str, Any]) -> str:
    style = badge_conf.get("style", "flat")
    label = badge_conf.get("label", "code quality").replace(" ", "%20")
    badge_color = {
        "A+": "brightgreen", "A": "green", "B": "yellow",
        "C": "orange", "D": "red", "F": "critical",
    }.get(grade, "lightgrey")
    badge_url = f"https://img.shields.io/badge/{label}-{grade}-{badge_color}?style={style}"
    print(f"\n  🏷  Badge:")
    print(f"  {'─' * 50}")
    print(f"     Markdown:  [![{label}]({badge_url})](https://redsl.dev)")
    print(f"     HTML:      <img src=\"{badge_url}\" alt=\"{label}\">")
    print(f"     URL:       {badge_url}")
    return badge_url


# -- main --------------------------------------------------------------------

def run_audit_example(scenario: str = "default", source: str | None = None) -> dict[str, Any]:
    data = load_example_yaml("audit", scenario=scenario, source=source)
    repo = data["repo"]
    metrics = data["metrics"]

    print_banner(data.get("title", "ReDSL — One-click Audit"))

    _print_connect_section(repo)
    _print_scan_phases(data.get("scan_phases", []))

    score = _compute_score(metrics)
    grade = _grade_for_score(score, data.get("grade_thresholds", {}))

    _print_grade_box(score, grade)
    _print_metrics_table(metrics)
    _print_recommendations(data.get("recommendations", []))
    badge_url = _print_badge(grade, data.get("badge", {}))

    print(f"\n  {'═' * 55}")
    print(f"  {repo['owner']}/{repo['name']}  →  Grade {grade} ({score:.1f}/100)")
    print(f"  {'═' * 55}")

    return {
        "scenario": data,
        "score": score,
        "grade": grade,
        "metrics": metrics,
        "badge_url": badge_url,
    }


def main(argv: list[str] | None = None) -> dict[str, Any]:
    scenario = parse_scenario(argv)
    return run_audit_example(scenario=scenario)


if __name__ == "__main__":
    main()
