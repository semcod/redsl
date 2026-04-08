"""Reporting helpers for the refactoring orchestrator."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from redsl.llm.llx_router import estimate_cycle_cost as _estimate_cycle_cost
from redsl.refactors import RefactorEngine

if TYPE_CHECKING:
    from redsl.orchestrator import RefactorOrchestrator


def explain_decisions(orchestrator: "RefactorOrchestrator", project_dir: Path, limit: int = 10) -> str:
    """Explain refactoring decisions without executing them."""
    analysis = orchestrator.analyzer.analyze_project(project_dir)
    contexts = analysis.to_dsl_contexts()
    decisions = orchestrator.dsl_engine.top_decisions(contexts, limit=limit)

    if not decisions:
        return "Brak decyzji refaktoryzacji — kod wygląda dobrze."

    lines = [f"Top {len(decisions)} decyzji refaktoryzacji:\n"]
    for i, d in enumerate(decisions, 1):
        confidence = RefactorEngine.estimate_confidence(d)
        lines.extend([
            f"{i}. Action: {d.action.value}",
            f"   Rule: {d.rule_name}",
            f"   Target: {d.target_file}",
            f"   Target function: {d.target_function or '-'}",
            f"   Score: {d.score:.2f}",
            f"   Confidence (metric): {confidence:.2f}",
            f"   Rationale: {d.rationale}",
        ])

        src_path = project_dir / d.target_file
        if not src_path.exists() and d.target_function:
            resolved = orchestrator.analyzer.resolve_file_path(project_dir, d.target_function)
            if resolved:
                src_path = project_dir / resolved
        if src_path.exists():
            func = d.target_function
            if not func:
                worst = orchestrator.analyzer.find_worst_function(src_path)
                func = worst[0] if worst else None
            if func:
                src = orchestrator.analyzer.extract_function_source(src_path, func)
                preview = src[:400].rstrip()
                if len(src) > 400:
                    preview += f"\n    ... (+{len(src)-400} chars)"
                lines.append(f"Źródło ({src_path.name}::{func}):\n{preview}")
        lines.append("")

    return "\n".join(lines)


def get_memory_stats(orchestrator: "RefactorOrchestrator") -> dict[str, Any]:
    """Return memory and runtime statistics for the orchestrator."""
    return {
        "memory": orchestrator.memory.stats(),
        "total_cycles": orchestrator._cycle_count,
        "total_llm_calls": orchestrator.llm.total_calls,
        "total_llm_cost_usd": round(orchestrator._total_llm_cost, 6),
    }


def estimate_cycle_cost(orchestrator: "RefactorOrchestrator", project_dir: Path, max_actions: int = 10) -> list[dict]:
    """Estimate the cost of the next cycle without executing it."""
    analysis = orchestrator.analyzer.analyze_project(project_dir)
    contexts = analysis.to_dsl_contexts()
    decisions = orchestrator.dsl_engine.top_decisions(contexts, limit=max_actions)
    return _estimate_cycle_cost(decisions, [d.context for d in decisions])
