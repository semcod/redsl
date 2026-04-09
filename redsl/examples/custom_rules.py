from __future__ import annotations

from typing import Any

from redsl.dsl import Condition, DSLEngine, Operator, RefactorAction, Rule

from ._common import load_example_yaml, parse_scenario, print_banner


def _build_python_rule(rule_data: dict[str, Any]) -> Rule:
    conditions = [
        Condition(item["field"], Operator(item["op"]), item["value"])
        for item in rule_data.get("conditions", [])
    ]
    return Rule(
        name=rule_data.get("name", "custom_rule"),
        conditions=conditions,
        action=RefactorAction(rule_data.get("action", "do_nothing")),
        priority=float(rule_data.get("priority", 0.5)),
        description=rule_data.get("description", ""),
        tags=list(rule_data.get("tags", [])),
    )


def run_custom_rules_example(scenario: str = "default", source: str | None = None) -> dict[str, Any]:
    data = load_example_yaml("custom_rules", scenario=scenario, source=source)
    engine = DSLEngine()

    print_banner(data.get("title", "ReDSL — Własne reguły DSL"))
    print(f"\n  Domyślne reguły: {len(engine.rules)}")

    for rule_data in data.get("python_rules", []):
        engine.add_rule(_build_python_rule(rule_data))

    print(f"  Po dodaniu Pythonowych: {len(engine.rules)}")

    engine.add_rules_from_yaml(data.get("yaml_rules", []))
    print(f"  Po dodaniu YAML: {len(engine.rules)}")

    contexts = data.get("contexts", [])
    decisions = engine.top_decisions(contexts, limit=int(data.get("decision_limit", 10)))

    print(f"\n  Decyzje ({len(decisions)}):")
    print("-" * 60)

    for i, decision in enumerate(decisions, 1):
        tags_str = f" [{', '.join(decision.context.get('tags', []))}]" if decision.context.get("tags") else ""
        print(f"\n  [{i}] {decision.action.value}{tags_str}")
        print(f"      {decision.target_file}")
        if decision.target_function:
            print(f"      → {decision.target_function}")
        print(f"      score={decision.score:.2f}  rule={decision.rule_name}")

    print("\n\n  Szczegóły top decyzji:")
    print("-" * 60)
    if decisions:
        print(engine.explain(decisions[0]))

    return {"engine": engine, "decisions": decisions, "scenario": data}


def main(argv: list[str] | None = None) -> dict[str, Any]:
    scenario = parse_scenario(argv)
    return run_custom_rules_example(scenario=scenario)


if __name__ == "__main__":
    main()
