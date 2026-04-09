from __future__ import annotations

from pathlib import Path
from typing import Any

from redsl.memory import AgentMemory, InMemoryCollection

from ._common import load_example_yaml, parse_scenario, print_banner


def _build_in_memory_agent_memory(persist_dir: str | Path) -> AgentMemory:
    memory = AgentMemory(persist_dir)
    memory.episodic._collection = InMemoryCollection(memory.episodic.collection_name)
    memory.semantic._collection = InMemoryCollection(memory.semantic.collection_name)
    memory.procedural._collection = InMemoryCollection(memory.procedural.collection_name)
    return memory


def run_memory_learning_example(scenario: str = "default", source: str | None = None) -> dict[str, Any]:
    data = load_example_yaml("memory_learning", scenario=scenario, source=source)
    memory_cfg = data.get("memory", {})
    format_cfg = data.get("format", {})
    sections = data.get("sections", {})
    recall_cfg = data.get("recall", {})
    stats_cfg = data.get("stats", {})

    memory = _build_in_memory_agent_memory(memory_cfg.get("persist_dir", "/tmp/redsl_example_memory"))

    print_banner(
        data.get("title", "ReDSL — System pamięci"),
        width=int(format_cfg.get("header_width", 60)),
        char=str(format_cfg.get("header_char", "=")),
    )

    episodic = sections.get("episodic", {})
    print(f"\n  {episodic.get('heading', '[EPISODIC] Zapisuję historię akcji...')}")
    for entry in episodic.get("entries", []):
        memory.remember_action(
            action=entry["action"],
            target=entry["target"],
            result=entry["result"],
            success=bool(entry.get("success", True)),
            details=dict(entry.get("details", {})),
        )

    semantic = sections.get("semantic", {})
    print(f"  {semantic.get('heading', '[SEMANTIC] Zapisuję wzorce i lekcje...')}")
    for entry in semantic.get("entries", []):
        memory.learn_pattern(
            pattern=entry["pattern"],
            context=entry["context"],
            effectiveness=float(entry.get("effectiveness", 0.0)),
        )

    procedural = sections.get("procedural", {})
    print(f"  {procedural.get('heading', '[PROCEDURAL] Zapisuję strategie...')}")
    for entry in procedural.get("entries", []):
        memory.store_strategy(
            strategy_name=entry["strategy_name"],
            steps=list(entry.get("steps", [])),
            tags=list(entry.get("tags", [])),
        )

    print("\n" + "-" * int(format_cfg.get("recall_width", 60)))
    print(f"  {recall_cfg.get('heading', 'Przywołuję z pamięci...')}")
    print("-" * int(format_cfg.get("recall_width", 60)))

    similar_cfg = recall_cfg.get("similar_actions", {})
    similar = memory.recall_similar_actions(
        similar_cfg.get("query", ""),
        limit=int(similar_cfg.get("limit", 3)),
    )
    print(f"\n  Podobne akcje ({len(similar)}):")
    for entry in similar:
        success = "✓" if entry.metadata.get("success") or "True" in entry.content else "✗"
        print(f"    {success} {entry.content[:80]}...")

    patterns_cfg = recall_cfg.get("patterns", {})
    patterns = memory.recall_patterns(
        patterns_cfg.get("query", ""),
        limit=int(patterns_cfg.get("limit", 3)),
    )
    print(f"\n  Pasujące wzorce ({len(patterns)}):")
    for entry in patterns:
        print(f"    → {entry.content[:80]}...")

    strategies_cfg = recall_cfg.get("strategies", {})
    strategies = memory.recall_strategies(
        strategies_cfg.get("query", ""),
        limit=int(strategies_cfg.get("limit", 2)),
    )
    print(f"\n  Strategie ({len(strategies)}):")
    for entry in strategies:
        print(f"    → {entry.content[:80]}...")

    stats = memory.stats()
    print(f"\n  {stats_cfg.get('title', 'Pamięć agenta:')}")
    print(f"    Episodic:   {stats['episodic']} wpisów (historia akcji)")
    print(f"    Semantic:   {stats['semantic']} wpisów (wzorce)")
    print(f"    Procedural: {stats['procedural']} wpisów (strategie)")

    return {
        "scenario": data,
        "stats": stats,
        "similar_actions": similar,
        "patterns": patterns,
        "strategies": strategies,
    }


def main(argv: list[str] | None = None) -> dict[str, Any]:
    scenario = parse_scenario(argv)
    return run_memory_learning_example(scenario=scenario)


if __name__ == "__main__":
    main()
