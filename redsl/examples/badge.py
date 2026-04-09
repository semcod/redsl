"""Badge Generator — grade A+ do F z kodem Markdown/HTML."""

from __future__ import annotations

from typing import Any

from ._common import load_example_yaml, parse_scenario, print_banner


def _compute_project_score(metrics: dict[str, Any], scoring: dict[str, Any]) -> float:
    w = scoring.get("weights", {})
    cc = max(0.0, 1.0 - metrics.get("avg_cc", 0) / scoring.get("complexity_max_cc", 25))
    sec = max(0.0, 1.0 - metrics.get("security_issues", 0) / scoring.get("security_max_issues", 10))
    dup = max(0.0, 1.0 - metrics.get("duplicate_pct", 0) / scoring.get("duplication_max_pct", 20))
    types = metrics.get("type_coverage_pct", 50) / 100.0
    size = max(0.0, 1.0 - metrics.get("total_lines", 0) / scoring.get("size_max_lines", 50000))
    raw = (
        cc * w.get("complexity", 0.3)
        + sec * w.get("security", 0.25)
        + dup * w.get("duplication", 0.2)
        + types * w.get("type_coverage", 0.15)
        + size * w.get("size", 0.1)
    )
    return round(min(100.0, max(0.0, raw * 100)), 1)


def _grade_for_score(score: float, scale: list[dict]) -> dict[str, Any]:
    for entry in scale:
        if score >= entry["min_score"]:
            return entry
    return scale[-1]


def run_badge_example(scenario: str = "default", source: str | None = None) -> dict[str, Any]:
    data = load_example_yaml("badge", scenario=scenario, source=source)
    scale = data.get("grade_scale", [])
    styles = data.get("badge_styles", [])
    projects = data.get("projects", [])
    scoring = data.get("scoring", {})
    dim_badges = data.get("dimension_badges", [])

    print_banner(data.get("title", "ReDSL — Badge Generator"))

    results: list[dict[str, Any]] = []

    for proj in projects:
        name = proj["name"]
        metrics = proj.get("metrics", {})
        score = _compute_project_score(metrics, scoring)
        entry = _grade_for_score(score, scale)
        grade = entry["grade"]
        color = entry["color"].lstrip("#")

        results.append({"name": name, "score": score, "grade": grade, "color": color})

        # -- Grade display --
        bar_len = int(score / 10)
        bar = "█" * bar_len + "░" * (10 - bar_len)
        print(f"\n  ┌{'─' * 55}┐")
        print(f"  │  {name:<40s}  {grade:>3s}  {score:5.1f}  │")
        print(f"  │  [{bar}]  {entry.get('label', '')}{'':>25s}│")
        print(f"  └{'─' * 55}┘")

        # -- Metrics breakdown --
        print(f"     CC={metrics.get('avg_cc', '?'):>5}   "
              f"Sec={metrics.get('security_issues', '?')}   "
              f"Dup={metrics.get('duplicate_pct', '?')}%   "
              f"Types={metrics.get('type_coverage_pct', '?')}%   "
              f"LOC={metrics.get('total_lines', '?'):,}")

        # -- Dimension badges (advanced) --
        if dim_badges:
            parts = []
            for db in dim_badges:
                val = metrics.get(db["key"], 0)
                th = db["thresholds"]
                # For type_coverage, higher is better
                if "coverage" in db["key"]:
                    if val >= th["green"]:
                        dc = "brightgreen"
                    elif val >= th["yellow"]:
                        dc = "yellow"
                    else:
                        dc = "red"
                else:
                    if val <= th["green"]:
                        dc = "brightgreen"
                    elif val <= th["yellow"]:
                        dc = "yellow"
                    else:
                        dc = "red"
                parts.append(f"{db['label']}:{dc}")
            print(f"     Dimensions: {' | '.join(parts)}")

        # -- History (advanced) --
        history = proj.get("history", [])
        if history:
            trend = " → ".join(f"{h['grade']}" for h in history)
            print(f"     Trend: {trend}")

        # -- Badge code --
        label = "code%20quality"
        for style in styles[:1]:  # show first style
            url = style["url_template"].format(label=label, grade=grade, color=color)
            print(f"\n     Markdown:")
            print(f"       [![code quality]({url})](https://redsl.dev)")
            print(f"     HTML:")
            print(f"       <img src=\"{url}\" alt=\"code quality {grade}\">")

    # -- Summary table --
    if len(results) > 1:
        print(f"\n  {'═' * 55}")
        print(f"  📋 Podsumowanie ekosystemu:")
        print(f"  {'─' * 55}")
        print(f"  {'Projekt':<25s} {'Grade':>6s} {'Score':>8s}")
        print(f"  {'─' * 55}")
        for r in results:
            print(f"  {r['name']:<25s} {r['grade']:>6s} {r['score']:>7.1f}")
        avg_score = sum(r["score"] for r in results) / len(results)
        avg_entry = _grade_for_score(avg_score, scale)
        print(f"  {'─' * 55}")
        print(f"  {'ECOSYSTEM AVG':<25s} {avg_entry['grade']:>6s} {avg_score:>7.1f}")

    print(f"\n  {'═' * 55}")

    return {"scenario": data, "results": results}


def main(argv: list[str] | None = None) -> dict[str, Any]:
    scenario = parse_scenario(argv)
    return run_badge_example(scenario=scenario)


if __name__ == "__main__":
    main()
