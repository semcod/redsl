"""Decision selection and execution logic."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from redsl.dsl import Decision, RefactorAction
from redsl.llm import ModelRejectedError
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
    target_file: str | None = None,
) -> list[Decision]:
    """Select top decisions from analysis, optionally filtered to a target file."""
    contexts = analysis.to_dsl_contexts()
    decisions = orchestrator.dsl_engine.top_decisions(contexts, limit=max_actions * 3 if target_file else max_actions)
    if target_file:
        target_norm = Path(target_file).as_posix().lstrip("./")
        decisions = [
            d for d in decisions
            if _decision_matches_target(d, target_norm)
        ][:max_actions]
    return decisions


def _decision_matches_target(decision: Decision, target_norm: str) -> bool:
    """Check if a decision's target file matches the given normalized path."""
    decision_target = getattr(decision, "target_file", "")
    if not decision_target:
        return False
    decision_norm = Path(str(decision_target)).as_posix().lstrip("./")
    return decision_norm == target_norm or decision_norm.startswith(f"{target_norm.rstrip('/')}/")


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


def _check_time_window_duplicate(
    orchestrator: "RefactorOrchestrator",
    decision: Decision,
    project_dir: Path,
) -> RefactorResult | None:
    """Check if a similar proposal was recently made (time-window guard)."""
    from redsl.history import HistoryReader

    reader = HistoryReader(project_dir)
    if not reader.has_recent_proposal(decision.target_file, decision.action.value):
        return None

    reason = (
        f"Duplicate proposal blocked (time-window): {decision.action.value} on "
        f"{decision.target_file} was already proposed in the last 24h"
    )
    logger.info(reason)
    orchestrator.history.record_event(
        "proposal_skipped_duplicate",
        cycle_number=orchestrator._cycle_count,
        decision_rule=decision.rule_name,
        target_file=decision.target_file,
        action=decision.action.value,
        status="blocked",
        reason=reason,
        thought=(
            f"Checked .redsl/history.jsonl — found recent proposal for "
            f"{decision.action.value} on {decision.target_file}. Skipping to save LLM cost."
        ),
        outcome_reason=reason,
    )
    return RefactorResult(
        proposal=None,  # type: ignore[arg-type]
        applied=False,
        validated=False,
        errors=[reason],
        warnings=[],
    )


def _check_signature_duplicate(
    orchestrator: "RefactorOrchestrator",
    decision: Decision,
) -> RefactorResult | None:
    """Check if an exact signature match exists in recent history."""
    signature = orchestrator.history.decision_signature(
        rule=decision.rule_name,
        target_file=decision.target_file,
        action=decision.action.value,
        context=decision.context,
    )
    if not orchestrator.history.has_recent_signature(signature):
        return None

    reason = (
        f"Duplicate decision blocked (signature): {decision.rule_name} on {decision.target_file} "
        f"({decision.action.value}) already recorded in .redsl/history.jsonl"
    )
    logger.info(reason)
    orchestrator.history.record_event(
        "decision_blocked_duplicate",
        cycle_number=orchestrator._cycle_count,
        decision_rule=decision.rule_name,
        target_file=decision.target_file,
        action=decision.action.value,
        status="blocked",
        reason=reason,
        thought=f"Exact context hash matched a previous decision. Signature: {signature[:16]}…",
        outcome_reason=reason,
        details={"signature": signature},
    )
    return RefactorResult(
        proposal=None,  # type: ignore[arg-type]
        applied=False,
        validated=False,
        errors=[reason],
        warnings=[],
    )


def _generate_proposal_with_reflection(
    orchestrator: "RefactorOrchestrator",
    decision: Decision,
    source_code: str,
    signature: str,
) -> "Proposal":
    """Generate proposal with optional reflection rounds."""
    selection = select_model(decision.action, decision.context)
    reflection_model = select_reflection_model(use_local=True)

    configured_model = orchestrator.config.llm.model
    model = apply_provider_prefix(selection.model, configured_model)
    refl_model = apply_provider_prefix(reflection_model, configured_model)

    # Check model against age policy
    from redsl.llm import check_model_policy
    try:
        policy_result = check_model_policy(model)
        if not policy_result["allowed"]:
            logger.warning("Model %s rejected by policy: %s", model, policy_result["reason"])
            # Fall back to configured model if policy rejects
            model = configured_model
            policy_result = check_model_policy(model)
            if not policy_result["allowed"]:
                raise ModelRejectedError(f"Both router model and fallback rejected: {policy_result['reason']}")
    except ModelRejectedError as e:
        logger.error("Model policy rejection: %s", e)
        raise

    logger.info(
        "llx_router: %s → model=%s est_cost=$%.4f (policy: %s)",
        selection.reason,
        model,
        selection.estimated_cost,
        policy_result.get("reason", "ok"),
    )
    orchestrator._total_llm_cost += selection.estimated_cost

    proposal = orchestrator.refactor_engine.generate_proposal(
        decision,
        source_code,
        model_override=model,
    )
    orchestrator.history.record_event(
        "proposal_generated",
        cycle_number=orchestrator._cycle_count,
        decision_rule=decision.rule_name,
        target_file=decision.target_file,
        action=proposal.refactor_type,
        details={
            "confidence": proposal.confidence,
            "summary": proposal.summary,
            "changes": [ch.file_path for ch in proposal.changes],
            "signature": signature,
        },
    )

    if orchestrator.config.refactor.reflection_rounds > 0:
        proposal = orchestrator.refactor_engine.reflect_on_proposal(
            proposal,
            source_code,
            model_override=refl_model,
        )
        orchestrator.history.record_event(
            "proposal_reflected",
            cycle_number=orchestrator._cycle_count,
            decision_rule=decision.rule_name,
            target_file=decision.target_file,
            action=proposal.refactor_type,
            reflection=proposal.reflection_notes[-1000:],
            details={"reflection_notes": proposal.reflection_notes[-1000:]},
        )

    return proposal


def _apply_and_record_result(
    orchestrator: "RefactorOrchestrator",
    decision: Decision,
    proposal: "Proposal",
    project_dir: Path,
) -> RefactorResult:
    """Apply proposal and record the outcome."""
    from redsl.execution.resolution import _remember_decision_result

    result = orchestrator.refactor_engine.apply_proposal(proposal, project_dir)
    outcome_reason = None
    if not result.applied:
        outcome_reason = f"Rejected: {'; '.join(result.errors)}" if result.errors else "Rejected: validation failed"

    orchestrator.history.record_event(
        "proposal_applied" if result.applied else "proposal_rejected",
        cycle_number=orchestrator._cycle_count,
        decision_rule=decision.rule_name,
        target_file=decision.target_file,
        action=proposal.refactor_type,
        status="applied" if result.applied else "rejected",
        reason="; ".join(result.errors) if result.errors else None,
        outcome_reason=outcome_reason,
        details={"validated": result.validated, "warnings": result.warnings},
    )
    _remember_decision_result(orchestrator, decision, proposal, result)
    return result


def _execute_decision(
    orchestrator: "RefactorOrchestrator",
    decision: Decision,
    project_dir: Path,
) -> RefactorResult:
    """Execute a single decision (direct or LLM-based)."""
    from redsl.execution.resolution import _consult_memory, _load_source_code, _resolve_source_path

    logger.info(
        "Executing: %s on %s (score=%.2f)",
        decision.action.value,
        decision.target_file,
        decision.score,
    )
    orchestrator.history.record_event(
        "decision_started",
        cycle_number=orchestrator._cycle_count,
        decision_rule=decision.rule_name,
        target_file=decision.target_file,
        action=decision.action.value,
        thought=(
            f"Rule '{decision.rule_name}' matched with score={decision.score:.2f}. "
            f"Rationale: {decision.rationale}"
        ),
        details={"score": decision.score, "should_execute": decision.should_execute},
    )

    if decision.action in _DIRECT_REFACTOR_ACTIONS:
        return _execute_direct_refactor(orchestrator, decision, project_dir)

    # Dedup guards
    if dup_result := _check_time_window_duplicate(orchestrator, decision, project_dir):
        return dup_result

    source_path = _resolve_source_path(orchestrator, decision, project_dir)
    source_code = _load_source_code(orchestrator, source_path, decision)
    _consult_memory(orchestrator, decision)

    if dup_result := _check_signature_duplicate(orchestrator, decision):
        return dup_result

    signature = orchestrator.history.decision_signature(
        rule=decision.rule_name,
        target_file=decision.target_file,
        action=decision.action.value,
        context=decision.context,
    )
    proposal = _generate_proposal_with_reflection(orchestrator, decision, source_code, signature)
    return _apply_and_record_result(orchestrator, decision, proposal, project_dir)


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
