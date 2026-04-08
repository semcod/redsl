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
from collections.abc import Callable
from pathlib import Path

from redsl.config import AgentConfig
from redsl.execution import explain_decisions, get_memory_stats
from redsl.orchestrator import RefactorOrchestrator

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


def _analysis_source_method(orch: RefactorOrchestrator, path: Path) -> str:
    toon_files = orch.analyzer._find_toon_files(path)
    return f"toon ({', '.join(toon_files.keys())})" if toon_files else "AST fallback"


def _analysis_function_metrics(result) -> list:
    return sorted(
        [m for m in result.metrics if m.function_name and m.cyclomatic_complexity > 0],
        key=lambda m: m.cyclomatic_complexity,
        reverse=True,
    )


def _print_analysis_summary(result, path: Path, source_method: str) -> None:
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


def _print_top_functions(func_metrics) -> None:
    if not func_metrics:
        return

    print("\n  TOP FUNKCJE (CC):")
    for m in func_metrics[:8]:
        tag = "!!!" if m.cyclomatic_complexity > 30 else ("!!" if m.cyclomatic_complexity > 15 else "! ")
        print(f"    {tag} CC={m.cyclomatic_complexity:<4} {m.file_path}::{m.function_name}")


def _print_alerts(result, func_metrics) -> None:
    if result.alerts and not func_metrics:
        print("\n  ALERTY:")
        for alert in result.alerts[:10]:
            sev = alert.get("severity", 0)
            severity = "!!!" if sev >= 3 else ("!!" if sev >= 2 else "! ")
            print(f"    {severity} {alert.get('type', '?')}: {alert.get('name', '?')} CC={alert.get('value', '?')}")


def _print_duplicates(result) -> None:
    if result.duplicates:
        print(f"\n  DUPLIKATY: {len(result.duplicates)} grup")
        for dup in result.duplicates[:5]:
            print(f"    {dup.get('type', '?')} {dup.get('name', '?')}: "
                  f"{dup.get('lines', 0)}L x{dup.get('occurrences', 0)} "
                  f"(oszczędność: {dup.get('saved_lines', 0)}L)")


def _print_analysis_plan(result, path: Path) -> None:
    from redsl.dsl.engine import DSLEngine

    dsl = DSLEngine()
    decisions = dsl.top_decisions(result.to_dsl_contexts(), limit=5)
    if decisions:
        print(f"\n  PLAN ({len(decisions)} akcji):")
        for d in decisions:
            fn = f"::{d.target_function}" if d.target_function else ""
            exists = "✓" if (path / d.target_file).exists() else "?"
            print(f"    [{exists}] {d.action.value:<22} {d.target_file}{fn}  (CC={d.context.get('cyclomatic_complexity',0)}, score={d.score:.2f})")
    print()


def cmd_analyze(project_dir: str) -> None:
    """Analiza projektu — wyświetl metryki i alerty."""
    orch = _get_orchestrator()
    path = Path(project_dir)

    if not path.exists():
        print(f"Katalog nie istnieje: {path}")
        sys.exit(1)

    result = orch.analyzer.analyze_project(path)
    source_method = _analysis_source_method(orch, path)
    func_metrics = _analysis_function_metrics(result)

    _print_analysis_summary(result, path, source_method)
    _print_top_functions(func_metrics)
    _print_alerts(result, func_metrics)
    _print_duplicates(result)
    _print_analysis_plan(result, path)


def cmd_explain(project_dir: str) -> None:
    """Wyjaśnij decyzje refaktoryzacji bez ich wykonywania."""
    orch = _get_orchestrator()
    path = Path(project_dir)
    explanation = explain_decisions(orch, path)
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

    stats = get_memory_stats(orch)
    print(f"\n  Pamięć: {stats['memory']}")
    print(f"  Łączne wywołania LLM: {stats['total_llm_calls']}")


def cmd_memory_stats() -> None:
    """Statystyki pamięci agenta."""
    orch = _get_orchestrator()
    stats = get_memory_stats(orch)
    print(json.dumps(stats, indent=2))


def cmd_serve(port: int = 8000, host: str = "0.0.0.0") -> None:
    """Uruchom serwer API."""
    import uvicorn
    uvicorn.run("app.api:app", host=host, port=port, reload=True)


def _print_usage() -> None:
    """Wyświetl pomoc użycia."""
    print("Użycie:")
    print("  python -m app.main analyze   --project ./path")
    print("  python -m app.main explain   --project ./path")
    print("  python -m app.main refactor  --project ./path [--dry-run] [--auto]")
    print("  python -m app.main memory-stats")
    print("  python -m app.main serve     [--port 8000]")


def _get_arg(args: list[str], name: str, default: str = "") -> str:
    """Pobierz wartość argumentu z listy args."""
    for i, a in enumerate(args):
        if a == f"--{name}" and i + 1 < len(args):
            return args[i + 1]
    return default


def _has_flag(args: list[str], name: str) -> bool:
    """Sprawdź czy flaga jest obecna w args."""
    return f"--{name}" in args


def _dispatch_analyze(args: list[str]) -> None:
    """Wykonaj komendę analyze."""
    cmd_analyze(_get_arg(args, "project", "."))


def _dispatch_explain(args: list[str]) -> None:
    """Wykonaj komendę explain."""
    cmd_explain(_get_arg(args, "project", "."))


def _dispatch_refactor(args: list[str]) -> None:
    """Wykonaj komendę refactor."""
    cmd_refactor(
        project_dir=_get_arg(args, "project", "."),
        dry_run=not _has_flag(args, "live"),
        auto=_has_flag(args, "auto"),
        max_actions=int(_get_arg(args, "max", "5")),
        model=_get_arg(args, "model") or None,
    )


def _dispatch_memory_stats(args: list[str]) -> None:
    """Wykonaj komendę memory-stats."""
    cmd_memory_stats()


def _dispatch_serve(args: list[str]) -> None:
    """Wykonaj komendę serve."""
    cmd_serve(port=int(_get_arg(args, "port", "8000")))


def main() -> None:
    """Główny punkt wejścia CLI."""
    if len(sys.argv) < 2:
        _print_usage()
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    # Dispatch table dla komend
    dispatch: dict[str, Callable[[list[str]], None]] = {
        "analyze": _dispatch_analyze,
        "explain": _dispatch_explain,
        "refactor": _dispatch_refactor,
        "memory-stats": _dispatch_memory_stats,
        "serve": _dispatch_serve,
    }

    handler = dispatch.get(command)
    if handler:
        handler(args)
    else:
        print(f"Nieznana komenda: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
