"""
CLI — interfejs konsolowy agenta refaktoryzacji.

Użycie:
    python -m app.main analyze --project ./my-project
    python -m app.main refactor --project ./my-project --dry-run
    python -m app.main refactor --project ./my-project --auto
    python -m app.main explain --project ./my-project
    python -m app.main memory-stats
    python -m app.main serve --port 8000
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from app.config import AgentConfig
from app.orchestrator import RefactorOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-5s | %(message)s",
)
logger = logging.getLogger("refactor-agent")


def _get_orchestrator(model: str | None = None) -> RefactorOrchestrator:
    config = AgentConfig.from_env()
    if model:
        config.llm.model = model
    return RefactorOrchestrator(config)


def cmd_analyze(project_dir: str) -> None:
    """Analiza projektu — wyświetl metryki i alerty."""
    from app.dsl.engine import DSLEngine

    orch = _get_orchestrator()
    path = Path(project_dir)

    if not path.exists():
        print(f"Katalog nie istnieje: {path}")
        sys.exit(1)

    result = orch.analyzer.analyze_project(path)
    toon_files = orch.analyzer._find_toon_files(path)
    source_method = f"toon ({', '.join(toon_files.keys())})" if toon_files else "AST fallback"

    print("\n" + "=" * 60)
    print("  ANALIZA PROJEKTU")
    print("=" * 60)
    print(f"  Projekt:    {result.project_name or path.name}")
    print(f"  Źródło:     {source_method}")
    print(f"  Pliki:      {result.total_files}")
    print(f"  Linie:      {result.total_lines}")
    print(f"  Śr. CC:     {result.avg_cc:.1f}")
    print(f"  Krytyczne:  {result.critical_count}")
    print("=" * 60)

    # Top funkcje wg CC
    func_metrics = sorted(
        [m for m in result.metrics if m.function_name and m.cyclomatic_complexity > 0],
        key=lambda m: m.cyclomatic_complexity,
        reverse=True,
    )
    if func_metrics:
        print("\n  TOP FUNKCJE (CC):")
        for m in func_metrics[:8]:
            tag = "!!!" if m.cyclomatic_complexity > 30 else ("!!" if m.cyclomatic_complexity > 15 else "! ")
            print(f"    {tag} CC={m.cyclomatic_complexity:<4} {m.file_path}::{m.function_name}")

    if result.alerts and not func_metrics:
        print("\n  ALERTY:")
        for alert in result.alerts[:10]:
            sev = alert.get("severity", 0)
            severity = "!!!" if sev >= 3 else ("!!" if sev >= 2 else "! ")
            print(f"    {severity} {alert.get('type', '?')}: {alert.get('name', '?')} CC={alert.get('value', '?')}")

    if result.duplicates:
        print(f"\n  DUPLIKATY: {len(result.duplicates)} grup")
        for dup in result.duplicates[:5]:
            print(f"    {dup.get('type', '?')} {dup.get('name', '?')}: "
                  f"{dup.get('lines', 0)}L x{dup.get('occurrences', 0)} "
                  f"(oszczędność: {dup.get('saved_lines', 0)}L)")

    # Podgląd DSL decisions
    dsl = DSLEngine()
    decisions = dsl.top_decisions(result.to_dsl_contexts(), limit=5)
    if decisions:
        print(f"\n  PLAN ({len(decisions)} akcji):")
        for d in decisions:
            fn = f"::{d.target_function}" if d.target_function else ""
            exists = "✓" if (path / d.target_file).exists() else "?"
            print(f"    [{exists}] {d.action.value:<22} {d.target_file}{fn}  (CC={d.context.get('cyclomatic_complexity',0)}, score={d.score:.2f})")
    print()


def cmd_explain(project_dir: str) -> None:
    """Wyjaśnij decyzje refaktoryzacji bez ich wykonywania."""
    orch = _get_orchestrator()
    path = Path(project_dir)
    explanation = orch.explain_decisions(path)
    print(explanation)


def cmd_refactor(
    project_dir: str,
    dry_run: bool = True,
    auto: bool = False,
    max_actions: int = 5,
    model: str | None = None,
) -> None:
    """Uruchom cykl refaktoryzacji."""
    orch = _get_orchestrator(model)
    orch.refactor_engine.config.dry_run = dry_run
    orch.refactor_engine.config.auto_approve = auto
    path = Path(project_dir)

    print("\n" + "=" * 60)
    print("  CONSCIOUS REFACTOR AGENT")
    print(f"  Model: {orch.config.llm.model}")
    print(f"  Tryb: {'dry-run' if dry_run else 'LIVE'}")
    print(f"  Auto: {auto}")
    print("=" * 60)

    report = orch.run_cycle(path, max_actions=max_actions)

    print(f"\n  Cykl #{report.cycle_number}")
    print(f"  Analiza: {report.analysis_summary}")
    print(f"  Decyzje: {report.decisions_count}")
    print(f"  Wygenerowane: {report.proposals_generated}")
    print(f"  Zastosowane: {report.proposals_applied}")
    print(f"  Odrzucone: {report.proposals_rejected}")

    if report.errors:
        print(f"\n  Błędy ({len(report.errors)}):")
        for err in report.errors:
            print(f"    - {err}")

    stats = orch.get_memory_stats()
    print(f"\n  Pamięć: {stats['memory']}")
    print(f"  Łączne wywołania LLM: {stats['total_llm_calls']}")


def cmd_memory_stats() -> None:
    """Statystyki pamięci agenta."""
    orch = _get_orchestrator()
    stats = orch.get_memory_stats()
    print(json.dumps(stats, indent=2))


def cmd_serve(port: int = 8000, host: str = "0.0.0.0") -> None:
    """Uruchom serwer API."""
    import uvicorn
    uvicorn.run("app.api:app", host=host, port=port, reload=True)


def main() -> None:
    """Główny punkt wejścia CLI."""
    if len(sys.argv) < 2:
        print("Użycie:")
        print("  python -m app.main analyze   --project ./path")
        print("  python -m app.main explain   --project ./path")
        print("  python -m app.main refactor  --project ./path [--dry-run] [--auto]")
        print("  python -m app.main memory-stats")
        print("  python -m app.main serve     [--port 8000]")
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    # Prosty parser argumentów
    def get_arg(name: str, default: str = "") -> str:
        for i, a in enumerate(args):
            if a == f"--{name}" and i + 1 < len(args):
                return args[i + 1]
        return default

    def has_flag(name: str) -> bool:
        return f"--{name}" in args

    if command == "analyze":
        cmd_analyze(get_arg("project", "."))
    elif command == "explain":
        cmd_explain(get_arg("project", "."))
    elif command == "refactor":
        cmd_refactor(
            project_dir=get_arg("project", "."),
            dry_run=not has_flag("live"),
            auto=has_flag("auto"),
            max_actions=int(get_arg("max", "5")),
            model=get_arg("model") or None,
        )
    elif command == "memory-stats":
        cmd_memory_stats()
    elif command == "serve":
        cmd_serve(port=int(get_arg("port", "8000")))
    else:
        print(f"Nieznana komenda: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
