#!/usr/bin/env python3
"""
ReDSL — Przykład 04: System pamięci i uczenia

Pokazuje 3 warstwy pamięci:
1. EPISODIC  — „co zrobiłem" (historia akcji)
2. SEMANTIC  — „co wiem" (wzorce, lekcje)
3. PROCEDURAL — „jak to robić" (strategie)

Agent uczy się z doświadczeń i wykorzystuje wiedzę
w kolejnych cyklach refaktoryzacji.

Uruchomienie:
    python main.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.memory import AgentMemory, InMemoryCollection


def main():
    # Używamy in-memory fallback (bez ChromaDB / sieci)
    memory = AgentMemory("/tmp/redsl_example_memory")
    memory.episodic._collection = InMemoryCollection("episodic")
    memory.semantic._collection = InMemoryCollection("semantic")
    memory.procedural._collection = InMemoryCollection("procedural")

    print("=" * 60)
    print("  ReDSL — System pamięci")
    print("=" * 60)

    # ──────────────────────────────────────────────────────
    # 1. EPISODIC — zapamiętaj wykonane akcje
    # ──────────────────────────────────────────────────────
    print("\n  [EPISODIC] Zapisuję historię akcji...")

    memory.remember_action(
        action="extract_functions",
        target="parser_rules.py:_extract_entities",
        result="Rozbito na 4 funkcje: _extract_dates, _extract_amounts, _extract_names, _extract_addresses",
        success=True,
        details={"cc_before": 36, "cc_after": 8, "time_spent": "12min"},
    )

    memory.remember_action(
        action="split_module",
        target="main.py",
        result="Podzielono na: routes.py, handlers.py, middleware.py",
        success=True,
        details={"lines_before": 522, "lines_after_max": 180},
    )

    memory.remember_action(
        action="deduplicate",
        target="logging_setup.py",
        result="Wyciągnięto do shared/logging.py, 3 pliki zaktualizowane",
        success=True,
        details={"saved_lines": 50, "files_touched": 3},
    )

    memory.remember_action(
        action="extract_functions",
        target="api/views.py:handle_upload",
        result="Niepowodzenie — LLM zmienił sygnaturę publicznego API",
        success=False,
        details={"cc_before": 22, "error": "public API signature changed"},
    )

    # ──────────────────────────────────────────────────────
    # 2. SEMANTIC — zapamiętaj wzorce
    # ──────────────────────────────────────────────────────
    print("  [SEMANTIC] Zapisuję wzorce i lekcje...")

    memory.learn_pattern(
        pattern="extract_functions for CC>30",
        context="Działa dobrze na zagnieżdżonych if/else. Klucz: zachowaj guard clauses na górze.",
        effectiveness=0.92,
    )

    memory.learn_pattern(
        pattern="split_module for god modules",
        context="Grupuj po odpowiedzialności: routes, business logic, models. __init__.py z re-exportami.",
        effectiveness=0.88,
    )

    memory.learn_pattern(
        pattern="AVOID: extract from public API handlers",
        context="LLM często zmienia sygnatury publicznych endpointów. Lepiej refaktoryzować wewnętrzne helpery.",
        effectiveness=0.35,
    )

    # ──────────────────────────────────────────────────────
    # 3. PROCEDURAL — zapisz strategie
    # ──────────────────────────────────────────────────────
    print("  [PROCEDURAL] Zapisuję strategie...")

    memory.store_strategy(
        strategy_name="handle_high_cc_function",
        steps=[
            "Zidentyfikuj guard clauses — wynieś na górę jako early returns",
            "Znajdź grupy powiązanych operacji (np. walidacja, obliczenia, zapis)",
            "Wyciągnij każdą grupę jako osobną funkcję z opisową nazwą",
            "Zachowaj oryginalne error handling i logging",
            "Dodaj type hints do nowych funkcji",
            "Uruchom testy — upewnij się, że zachowanie się nie zmieniło",
        ],
        tags=["complexity", "extract_functions"],
    )

    memory.store_strategy(
        strategy_name="safe_god_module_split",
        steps=[
            "Zmapuj importy — kto importuje co z tego modułu",
            "Pogrupuj funkcje po odpowiedzialności (routes, logic, models, utils)",
            "Stwórz nowe moduły w tym samym pakiecie",
            "Przenieś funkcje grupami (nie pojedynczo)",
            "Stwórz __init__.py z re-exportami dla backward compatibility",
            "Zaktualizuj importy w innych plikach",
            "Uruchom pełen test suite",
        ],
        tags=["structure", "split_module"],
    )

    # ──────────────────────────────────────────────────────
    # 4. RECALL — przywołaj z pamięci
    # ──────────────────────────────────────────────────────
    print("\n" + "-" * 60)
    print("  Przywołuję z pamięci...")
    print("-" * 60)

    # Szukaj podobnych akcji
    similar = memory.recall_similar_actions("extract functions high complexity", limit=3)
    print(f"\n  Podobne akcje ({len(similar)}):")
    for entry in similar:
        success = "✓" if "True" in entry.content else "✗"
        print(f"    {success} {entry.content[:80]}...")

    # Szukaj wzorców
    patterns = memory.recall_patterns("complex function refactoring", limit=3)
    print(f"\n  Pasujące wzorce ({len(patterns)}):")
    for entry in patterns:
        print(f"    → {entry.content[:80]}...")

    # Szukaj strategii
    strategies = memory.recall_strategies("split large function", limit=2)
    print(f"\n  Strategie ({len(strategies)}):")
    for entry in strategies:
        print(f"    → {entry.content[:80]}...")

    # ──────────────────────────────────────────────────────
    # 5. Statystyki
    # ──────────────────────────────────────────────────────
    stats = memory.stats()
    print(f"\n  Pamięć agenta:")
    print(f"    Episodic:   {stats['episodic']} wpisów (historia akcji)")
    print(f"    Semantic:   {stats['semantic']} wpisów (wzorce)")
    print(f"    Procedural: {stats['procedural']} wpisów (strategie)")


if __name__ == "__main__":
    main()
