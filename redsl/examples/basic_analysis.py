from __future__ import annotations

from typing import Any

from redsl.analyzers import CodeAnalyzer
from redsl.dsl import DSLEngine

from ._common import load_example_yaml, parse_scenario, print_banner


def run_basic_analysis_example(scenario: str = "default", source: str | None = None) -> dict[str, Any]:
    data = load_example_yaml("basic_analysis", scenario=scenario, source=source)
    analyzer = CodeAnalyzer()
    result = analyzer.analyze_from_toon_content(
        project_toon=data["project_toon"],
        duplication_toon=data.get("duplication_toon", ""),
    )

    print_banner(data.get("title", "ReDSL — Analiza projektu"))
    print(f"  Pliki:     {result.total_files}")
    print(f"  Linie:     {result.total_lines}")
    print(f"  Alerty:    {len(result.alerts)}")
    print(f"  Duplikaty: {len(result.duplicates)}")

    engine = DSLEngine()
    contexts = result.to_dsl_contexts()
    decisions = engine.top_decisions(contexts, limit=int(data.get("decision_limit", 10)))

    print(f"\n  Top {len(decisions)} decyzji refaktoryzacji:")
    print("-" * 60)

    for i, decision in enumerate(decisions, 1):
        print(f"\n  [{i}] {decision.action.value}")
        print(f"      Plik:     {decision.target_file}")
        if decision.target_function:
            print(f"      Funkcja:  {decision.target_function}")
        print(f"      Score:    {decision.score:.2f}")
        print(f"      Reguła:   {decision.rule_name}")
        print(f"      Powód:    {decision.rationale}")

    print("\n" + "=" * 60)
    print(f"  Gotowe — {len(decisions)} akcji do rozważenia")
    print("=" * 60)

    return {"analysis": result, "decisions": decisions, "scenario": data}


def main(argv: list[str] | None = None) -> dict[str, Any]:
    scenario = parse_scenario(argv)
    return run_basic_analysis_example(scenario=scenario)


if __name__ == "__main__":
    main()
