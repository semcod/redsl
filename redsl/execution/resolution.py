"""Path resolution and source code loading utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from redsl.dsl import Decision

if TYPE_CHECKING:
    from redsl.orchestrator import RefactorOrchestrator
    from redsl.refactors import RefactorProposal, RefactorResult

logger = logging.getLogger(__name__)


def _resolve_source_path(
    orchestrator: "RefactorOrchestrator",
    decision: Decision,
    project_dir: Path,
) -> Path:
    """Resolve the source file path from a decision."""
    source_path = project_dir / decision.target_file
    if source_path.exists():
        return source_path

    if not decision.target_file.endswith(".py"):
        candidate = project_dir / f"{decision.target_file}.py"
        if candidate.exists():
            logger.info("Resolved %r → %s", decision.target_file, candidate.name)
            return candidate

    bare_name = Path(decision.target_file).stem
    for py_file in project_dir.rglob(f"{bare_name}.py"):
        if ".venv" not in py_file.parts and "venv" not in py_file.parts:
            logger.info("Resolved %r → %s", decision.target_file, py_file.relative_to(project_dir))
            return py_file

    if decision.target_function:
        resolved = orchestrator.analyzer.resolve_file_path(project_dir, decision.target_function)
        if resolved:
            source_path = project_dir / resolved
            logger.info("Resolved via function %r → %s", decision.target_function, resolved)

    return source_path


def _resolve_target_function(
    orchestrator: "RefactorOrchestrator",
    source_path: Path,
    decision: Decision,
) -> str | None:
    """Resolve the target function for a decision."""
    func_name = decision.target_function
    if not func_name and decision.context.get("cyclomatic_complexity", 0) > 15:
        worst = orchestrator.analyzer.find_worst_function(source_path)
        if worst:
            func_name = worst[0]
            logger.info(
                "Auto-detected worst function in %s: %r (CC=%d)",
                decision.target_file, func_name, worst[1],
            )
    return func_name


def _load_source_code(
    orchestrator: "RefactorOrchestrator",
    source_path: Path,
    decision: Decision,
) -> str:
    """Load source code for a decision, using semantic chunking if applicable."""
    if not source_path.exists():
        logger.warning("Source file not found: %s", source_path)
        return f"# File not found: {decision.target_file}"

    func_name = _resolve_target_function(orchestrator, source_path, decision)
    if func_name:
        chunk = orchestrator._chunker.chunk_function(source_path, func_name)
        if chunk:
            logger.info(
                "SemanticChunk %r: %d lines%s",
                func_name,
                chunk.total_lines,
                " [truncated]" if chunk.truncated else "",
            )
            return chunk.to_llm_prompt()
    return source_path.read_text(encoding="utf-8")


def _consult_memory(
    orchestrator: "RefactorOrchestrator",
    decision: Decision,
) -> None:
    """Consult memory for relevant strategies."""
    strategies = orchestrator.memory.recall_strategies(
        f"{decision.action.value} {decision.context.get('cyclomatic_complexity', 0)}",
        limit=2,
    )
    if strategies:
        logger.info("Found %d relevant strategies in memory", len(strategies))


def _consult_memory_for_decisions(
    orchestrator: "RefactorOrchestrator",
    decisions: list[Decision],
) -> None:
    """Consult memory for all decisions before execution."""
    for decision in decisions:
        similar = orchestrator.memory.recall_similar_actions(
            f"{decision.action.value} {decision.target_file}",
            limit=3,
        )
        if similar:
            logger.info(
                "Memory: found %d similar past actions for %s",
                len(similar), decision.target_file,
            )


def _remember_decision_result(
    orchestrator: "RefactorOrchestrator",
    decision: Decision,
    proposal: "RefactorProposal",
    result: "RefactorResult",
) -> None:
    """Remember the result of a decision in memory."""
    orchestrator.memory.remember_action(
        action=decision.action.value,
        target=f"{decision.target_file}:{decision.target_function or 'module'}",
        result=proposal.summary,
        success=result.validated and len(result.errors) == 0,
        details={
            "confidence": proposal.confidence,
            "score": decision.score,
            "rule": decision.rule_name,
        },
    )
    if result.validated and proposal.confidence > 0.7:
        orchestrator.memory.learn_pattern(
            pattern=f"{decision.action.value} for CC={decision.context.get('cyclomatic_complexity', 0)}",
            context=f"{decision.target_file} — {proposal.summary}",
            effectiveness=proposal.confidence,
        )


__all__ = [
    "_resolve_source_path",
    "_resolve_target_function",
    "_load_source_code",
    "_consult_memory",
    "_consult_memory_for_decisions",
    "_remember_decision_result",
]
