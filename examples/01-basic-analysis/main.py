#!/usr/bin/env python3
"""
ReDSL — Przykład 01: Podstawowa analiza projektu

Pokazuje jak:
1. Wczytać metryki z plików toon.yaml
2. Przepuścić je przez DSL Engine
3. Zobaczyć decyzje refaktoryzacji

Uruchomienie:
    python main.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.analyzers import CodeAnalyzer
from app.dsl import DSLEngine

# ──────────────────────────────────────────────────────────
# 1. Dane wejściowe — content z project_toon.yaml
# ──────────────────────────────────────────────────────────

PROJECT_TOON = """
HEALTH:
  CC̄=3.2  critical=10  dup=3  cycles=0

ALERTS[5]:
  !!! cc_exceeded      _extract_entities = 36 (limit:15)
  !!! high_fan_out     _extract_entities = 26 (limit:10)
  !!  high_fan_out     run_workflow = 18 (limit:10)
  !!  high_fan_out     _process_message = 18 (limit:10)
  !   cc_exceeded      _process_message = 17 (limit:15)

MODULES[5] (top by size):
  M[nlp-service/app/main.py] 522L C:0 F:20 CC↑10 D:0 (python)
  M[nlp-service/app/parser_rules.py] 274L C:0 F:5 CC↑36 D:2 (python)
  M[nlp-service/app/orchestrator.py] 330L C:0 F:7 CC↑17 D:1 (python)
  M[nlp-service/app/system_executor.py] 340L C:0 F:13 CC↑12 D:1 (python)
  M[worker/worker.py] 160L C:0 F:9 CC↑5 D:0 (python)
"""

DUPLICATION_TOON = """
DUPLICATES[2] (ranked by impact):
  [1899ff8e67d31c77] ! STRU  setup_logging  L=25 N=3 saved=50 sim=1.00
      nlp-service/app/logging_setup.py:0-24  (setup_logging)
      backend/app/logging_setup.py:0-24  (setup_logging)
      worker/logging_setup.py:0-24  (setup_logging)
  [ce00be02a9b12238] ! STRU  generate_invoice_from_text  L=15 N=4 saved=45 sim=1.00
      examples/01-invoice/main.py:0-14  (generate_invoice_from_text)
      examples/02-email/main.py:0-14  (generate_email_from_text)
"""


def main():
    # ──────────────────────────────────────────────────────
    # 2. Analiza — parser toon.yaml → metryki
    # ──────────────────────────────────────────────────────
    analyzer = CodeAnalyzer()
    result = analyzer.analyze_from_toon_content(
        project_toon=PROJECT_TOON,
        duplication_toon=DUPLICATION_TOON,
    )

    print("=" * 60)
    print("  ReDSL — Analiza projektu")
    print("=" * 60)
    print(f"  Pliki:     {result.total_files}")
    print(f"  Linie:     {result.total_lines}")
    print(f"  Alerty:    {len(result.alerts)}")
    print(f"  Duplikaty: {len(result.duplicates)}")

    # ──────────────────────────────────────────────────────
    # 3. DSL Engine — ewaluacja reguł
    # ──────────────────────────────────────────────────────
    engine = DSLEngine()
    contexts = result.to_dsl_contexts()
    decisions = engine.top_decisions(contexts, limit=10)

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


if __name__ == "__main__":
    main()
