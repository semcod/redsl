"""PR Bot — realistyczny preview komentarza w stylu GitHub."""

from __future__ import annotations

from typing import Any

from ._common import load_example_yaml, parse_scenario, print_banner


_LEVEL_ICON = {"error": "🔴", "warn": "🟡", "info": "🔵"}


def _delta(before: float | int, after: float | int, lower_is_better: bool = True) -> str:
    diff = after - before
    if diff == 0:
        return "—"
    arrow = "↓" if diff < 0 else "↑"
    sign = "" if diff < 0 else "+"
    good = (diff < 0) if lower_is_better else (diff > 0)
    marker = "✅" if good else "⚠️"
    if isinstance(diff, float):
        return f"{sign}{diff:.1f} {arrow} {marker}"
    return f"{sign}{diff} {arrow} {marker}"


def run_pr_bot_example(scenario: str = "default", source: str | None = None) -> dict[str, Any]:
    data = load_example_yaml("pr_bot", scenario=scenario, source=source)
    pr = data["pr"]
    before = data["before"]
    after = data["after"]
    flags = data.get("risk_flags", [])
    suggestions = data.get("suggestions", [])
    status = data.get("status_check", {})

    print_banner(data.get("title", "ReDSL — PR Bot"))

    # -- GitHub PR header --
    print(f"\n  ┌{'─' * 62}┐")
    print(f"  │  🤖 redsl-bot  commented just now                            │")
    print(f"  ├{'─' * 62}┤")
    print(f"  │                                                              │")
    print(f"  │  ## ReDSL Analysis — PR #{pr['number']}                        ")
    print(f"  │  **{pr['title']}**")
    print(f"  │  `{pr['branch']}` → `{pr['base']}`  by @{pr['author']}")
    print(f"  │  {pr['files_changed']} files  (+{pr['additions']} / -{pr['deletions']})")
    print(f"  │                                                              │")

    # -- Metrics delta table --
    print(f"  │  ### 📊 Metrics")
    print(f"  │  {'─' * 56}")
    print(f"  │  {'Metric':<25s} {'Before':>8s} {'After':>8s} {'Delta':>18s}")
    print(f"  │  {'─' * 56}")
    rows = [
        ("Avg CC",          f"{before['avg_cc']:.1f}",    f"{after['avg_cc']:.1f}",    _delta(before['avg_cc'], after['avg_cc'])),
        ("Max CC",          str(before['max_cc']),         str(after['max_cc']),         _delta(before['max_cc'], after['max_cc'])),
        ("Critical funcs",  str(before['critical_count']), str(after['critical_count']), _delta(before['critical_count'], after['critical_count'])),
        ("Duplicate %",     f"{before['duplicate_pct']}%", f"{after['duplicate_pct']}%", _delta(before['duplicate_pct'], after['duplicate_pct'])),
        ("Security issues", str(before['security_issues']),str(after['security_issues']),_delta(before['security_issues'], after['security_issues'])),
        ("Type coverage",   f"{before['type_coverage_pct']}%", f"{after['type_coverage_pct']}%", _delta(before['type_coverage_pct'], after['type_coverage_pct'], lower_is_better=False)),
    ]
    for label, bv, av, d in rows:
        print(f"  │  {label:<25s} {bv:>8s} {av:>8s} {d:>18s}")

    # -- Risk flags --
    if flags:
        print(f"  │")
        print(f"  │  ### 🚩 Risk Flags ({len(flags)})")
        print(f"  │  {'─' * 56}")
        for flag in flags:
            icon = _LEVEL_ICON.get(flag["level"], "⚪")
            print(f"  │  {icon} **{flag['file']}**")
            print(f"  │     {flag['message']}")
            if flag.get("suggestion"):
                print(f"  │     💡 _{flag['suggestion']}_")

    # -- Code suggestions --
    if suggestions:
        print(f"  │")
        print(f"  │  ### 💬 Suggestions ({len(suggestions)})")
        print(f"  │  {'─' * 56}")
        for sug in suggestions:
            stype = sug.get("type", "info")
            print(f"  │")
            print(f"  │  **{sug['title']}** — `{sug['file']}:{sug.get('line', '?')}` [{stype}]")
            for line in sug.get("body", "").strip().splitlines():
                print(f"  │  {line}")

    # -- Status check --
    print(f"  │")
    print(f"  │  {'─' * 56}")
    conclusion = status.get("conclusion", "neutral")
    check_icon = "✅" if conclusion == "success" else "❌" if conclusion == "failure" else "⏸"
    print(f"  │  {check_icon} **Status check: {conclusion.upper()}**")
    print(f"  │  {status.get('summary', '')}")
    blockers = status.get("blockers", [])
    if blockers:
        print(f"  │")
        print(f"  │  **Blockers:**")
        for b in blockers:
            print(f"  │  - 🔴 {b}")

    print(f"  │                                                              │")
    print(f"  └{'─' * 62}┘")

    print(f"\n  {'═' * 60}")

    return {
        "scenario": data,
        "pr": pr,
        "delta": {r[0]: r[3] for r in rows},
        "risk_flags": len(flags),
        "suggestions": len(suggestions),
        "conclusion": conclusion,
    }


def main(argv: list[str] | None = None) -> dict[str, Any]:
    scenario = parse_scenario(argv)
    return run_pr_bot_example(scenario=scenario)


if __name__ == "__main__":
    main()
