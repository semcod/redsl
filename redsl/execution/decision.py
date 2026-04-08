"""Decision selection and execution logic."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from redsl.dsl import Decision, RefactorAction
from redsl.llm.llx_router import apply_provider_prefix, select_model, select_reflection_model
from redsl.refactors import RefactorResult

if TYPE_CHECKING:
    from redsl.orchestrator import CycleReport, RefactorOrchestrator

logger = logging.getLogger(__name__)

_DIRECT_REFACTOR_ACTIONS = {
    RefactorAction.REMOVE_UNUSED_IMPORTS,
    RefactorAction.FIX_MODULE_EXECUTION_BLOCK,
    RefactorAction.EXTRACT_CONSTANTS,
    RefactorAction.ADD_RETURN_TYPES,
}


def _select_decisions(
    orchestrator: "RefactorOrchestrator",
    analysis: "AnalysisResult",
    max_actions: int,
) -> list[Decision]:
    """Select top decisions from analysis."""
    contexts = analysis.to_dsl_contexts()
    return orchestrator.dsl_engine.top_decisions(contexts, limit=max_actions)


def _execute_direct_refactor(
    orchestrator: "RefactorOrchestrator",
    decision: Decision,
    project_dir: Path,
) -> RefactorResult:
    """Execute a direct (non-LLM) refactoring action."""
    source_path = project_dir / decision.target_file

    if not source_path.exists():
        return RefactorResult(
            proposal=None,
            applied=False,
            validated=False,
            errors=[f"File not found: {source_path}"],
        )

    success = False
    errors: list[str] = []

    try:
        if decision.action == RefactorAction.REMOVE_UNUSED_IMPORTS:
            unused_imports = decision.context.get("unused_import_list", [])
            success = orchestrator.direct_refactor.remove_unused_imports(source_path, unused_imports)

        elif decision.action == RefactorAction.FIX_MODULE_EXECUTION_BLOCK:
            success = orchestrator.direct_refactor.fix_module_execution_block(source_path)

        elif decision.action == RefactorAction.EXTRACT_CONSTANTS:
            magic_numbers = decision.context.get("magic_number_list", [])
            success = orchestrator.direct_refactor.extract_constants(source_path, magic_numbers)

        elif decision.action == RefactorAction.ADD_RETURN_TYPES:
            functions_missing_return = decision.context.get("functions_missing_return", [])
            success = orchestrator.direct_refactor.add_return_types(source_path, functions_missing_return)

        if success:
            orchestrator.memory.remember_action(
                action=decision.action.value,
                target=str(source_path),
                result=f"Direct refactor applied: {decision.action.value}",
                success=True,
                details={"score": decision.score, "rule": decision.rule_name},
            )

            return RefactorResult(
                proposal=None,
                applied=True,
                validated=True,
                errors=[],
            )

        errors.append(f"Direct refactor failed: {decision.action.value}")

    except Exception as e:
        errors.append(str(e))
        logger.error("Direct refactor error: %s", e)

    return RefactorResult(
        proposal=None,
        applied=False,
        validated=False,
        errors=errors,
    )


def _execute_decision(
    orchestrator: "RefactorOrchestrator",
    decision: Decision,
    project_dir: Path,
) -> RefactorResult:
    """Execute a single decision (direct or LLM-based)."""
    from redsl.execution.resolution import _consult_memory, _load_source_code, _resolve_source_path, _remember_decision_result

    logger.info(
        "Executing: %s on %s (score=%.2f)",
        decision.action.value,
        decision.target_file,
        decision.score,
    )

    if decision.action in _DIRECT_REFACTOR_ACTIONS:
        return _execute_direct_refactor(orchestrator, decision, project_dir)

    source_path = _resolve_source_path(orchestrator, decision, project_dir)
    source_code = _load_source_code(orchestrator, source_path, decision)

    _consult_memory(orchestrator, decision)

    selection = select_model(decision.action, decision.context)
    reflection_model = select_reflection_model(use_local=True)

    configured_model = orchestrator.config.llm.model
    model = apply_provider_prefix(selection.model, configured_model)
    refl_model = apply_provider_prefix(reflection_model, configured_model)

    logger.info(
        "llx_router: %s → model=%s est_cost=$%.4f",
        selection.reason,
        model,
        selection.estimated_cost,
    )
    orchestrator._total_llm_cost += selection.estimated_cost

    proposal = orchestrator.refactor_engine.generate_proposal(
        decision,
        source_code,
        model_override=model,
    )
    if orchestrator.config.refactor.reflection_rounds > 0:
        proposal = orchestrator.refactor_engine.reflect_on_proposal(
            proposal,
            source_code,
            model_override=refl_model,
        )

    result = orchestrator.refactor_engine.apply_proposal(proposal, project_dir)
    _remember_decision_result(orchestrator, decision, proposal, result)
    return result


def _execute_decisions(
    orchestrator: "RefactorOrchestrator",
    decisions: list[Decision],
    project_dir: Path,
    use_sandbox: bool,
    report: "CycleReport",
) -> None:
    """Execute all decisions and update the report."""
    from redsl.execution.sandbox_execution import execute_sandboxed

    for decision in decisions:
        if not decision.should_execute:
            continue

        try:
            if use_sandbox:
                result = execute_sandboxed(orchestrator, decision, project_dir)
            else:
                result = _execute_decision(orchestrator, decision, project_dir)
            report.results.append(result)

            if result.applied or result.validated:
                report.proposals_generated += 1
                if result.applied:
                    report.proposals_applied += 1
            else:
                report.proposals_rejected += 1
                report.errors.extend(result.errors)

        except Exception as e:
            logger.error("Failed to execute decision %s: %s", decision.rule_name, e)
            report.errors.append(f"{decision.rule_name}: {e}")


__all__ = ["_select_decisions", "_execute_decision", "_execute_decisions", "_execute_direct_refactor"]
