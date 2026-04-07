#!/usr/bin/env python3
"""
ReDSL — Przykład 02: Własne reguły DSL

Pokazuje jak:
1. Definiować reguły DSL programowo (Python)
2. Ładować reguły z YAML
3. Łączyć z domyślnymi regułami
4. Ewaluować na dowolnych metrykach

Uruchomienie:
    python main.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.dsl import Condition, DSLEngine, Operator, RefactorAction, Rule


def main():
    engine = DSLEngine()

    print("=" * 60)
    print("  ReDSL — Własne reguły DSL")
    print("=" * 60)
    print(f"\n  Domyślne reguły: {len(engine.rules)}")

    # ──────────────────────────────────────────────────────
    # 1. Dodaj regułę programowo
    # ──────────────────────────────────────────────────────
    engine.add_rule(Rule(
        name="security_audit_long_functions",
        conditions=[
            Condition("cyclomatic_complexity", Operator.GT, 20),
            Condition("is_public_api", Operator.EQ, True),
        ],
        action=RefactorAction.EXTRACT_FUNCTIONS,
        priority=0.95,
        description="Publiczne API o CC > 20 — priorytet bezpieczeństwa",
        tags=["security", "critical"],
    ))

    engine.add_rule(Rule(
        name="inline_tiny_wrappers",
        conditions=[
            Condition("module_lines", Operator.LT, 5),
            Condition("function_count", Operator.EQ, 1),
        ],
        action=RefactorAction.INLINE_FUNCTION,
        priority=0.40,
        description="Jednoliniowe wrappery — zinlinuj do wywołującego",
        tags=["cleanup"],
    ))

    print(f"  Po dodaniu Pythonowych: {len(engine.rules)}")

    # ──────────────────────────────────────────────────────
    # 2. Dodaj reguły z formatu YAML/dict
    # ──────────────────────────────────────────────────────
    yaml_rules = [
        {
            "name": "enforce_max_module_size",
            "description": "Moduł > 600L → natychmiastowy split",
            "tags": ["team-standard"],
            "when": {
                "module_lines": {"gt": 600},
            },
            "then": {
                "action": "split_module",
                "priority": 0.92,
            },
        },
        {
            "name": "flag_untested_complex",
            "description": "CC > 10 bez testów → dodaj testy przed refaktorem",
            "tags": ["testing"],
            "when": {
                "cyclomatic_complexity": {"gt": 10},
                "linter_warnings": {"gt": 0},
            },
            "then": {
                "action": "add_type_hints",
                "priority": 0.55,
            },
        },
    ]

    engine.add_rules_from_yaml(yaml_rules)
    print(f"  Po dodaniu YAML: {len(engine.rules)}")

    # ──────────────────────────────────────────────────────
    # 3. Ewaluacja na przykładowych metrykach
    # ──────────────────────────────────────────────────────
    contexts = [
        {
            "file_path": "api/auth.py",
            "function_name": "verify_token",
            "cyclomatic_complexity": 25,
            "fan_out": 8,
            "module_lines": 180,
            "is_public_api": True,
            "function_count": 6,
        },
        {
            "file_path": "utils/wrap.py",
            "function_name": "log_wrapper",
            "cyclomatic_complexity": 1,
            "module_lines": 3,
            "function_count": 1,
        },
        {
            "file_path": "services/mega_service.py",
            "cyclomatic_complexity": 12,
            "module_lines": 720,
            "function_count": 28,
            "linter_warnings": 5,
        },
    ]

    decisions = engine.top_decisions(contexts, limit=10)

    print(f"\n  Decyzje ({len(decisions)}):")
    print("-" * 60)

    for i, d in enumerate(decisions, 1):
        tags_str = f" [{', '.join(d.context.get('tags', []))}]" if d.context.get('tags') else ""
        print(f"\n  [{i}] {d.action.value}{tags_str}")
        print(f"      {d.target_file}")
        if d.target_function:
            print(f"      → {d.target_function}")
        print(f"      score={d.score:.2f}  rule={d.rule_name}")

    # ──────────────────────────────────────────────────────
    # 4. Pokaż dopasowanie reguły
    # ──────────────────────────────────────────────────────
    print("\n\n  Szczegóły top decyzji:")
    print("-" * 60)
    if decisions:
        print(engine.explain(decisions[0]))


if __name__ == "__main__":
    main()
