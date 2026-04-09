from __future__ import annotations

import argparse
from typing import Any

from redsl.config import AgentConfig
from redsl.execution import get_memory_stats
from redsl.orchestrator import RefactorOrchestrator

from ._common import load_example_yaml, print_banner


def run_full_pipeline_example(
    scenario: str = "default",
    source: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    data = load_example_yaml("full_pipeline", scenario=scenario, source=source)
    selected_model = model or data.get("model", "gpt-5.4-mini")

    config = AgentConfig.from_env()
    config.llm.model = selected_model
    config.refactor.dry_run = bool(data.get("dry_run", True))
    config.refactor.reflection_rounds = int(data.get("reflection_rounds", 1))

    orchestrator = RefactorOrchestrator(config)

    print_banner(data.get("title", "ReDSL — Pełny pipeline"))
    print(f"  Model: {selected_model}")

    report = orchestrator.run_from_toon_content(
        project_toon=data["project_toon"],
        source_files=data.get("source_files", {}),
        max_actions=int(data.get("max_actions", 3)),
    )

    print(f"\n  Cykl #{report.cycle_number}")
    print(f"  Analiza:       {report.analysis_summary}")
    print(f"  Decyzje:       {report.decisions_count}")
    print(f"  Propozycje:    {report.proposals_generated}")
    print(f"  Zaaplikowane:  {report.proposals_applied}")
    print(f"  Odrzucone:     {report.proposals_rejected}")

    if report.errors:
        print("\n  Błędy:")
        for err in report.errors:
            print(f"    - {err}")

    print(f"\n  Propozycje zapisane w: {config.refactor.output_dir}")

    stats = get_memory_stats(orchestrator)
    print(f"\n  Pamięć agenta: {stats['memory']}")
    print(f"  Wywołania LLM: {stats['total_llm_calls']}")

    return {"report": report, "stats": stats, "scenario": data, "model": selected_model}


def main(argv: list[str] | None = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--scenario", choices=["default", "advanced"], default="default")
    parser.add_argument("--model", default=None)
    args = parser.parse_args(argv)
    return run_full_pipeline_example(scenario=args.scenario, model=args.model)


if __name__ == "__main__":
    main()
