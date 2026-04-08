"""Sandboxed execution for refactoring decisions."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from redsl.refactors import RefactorResult

if TYPE_CHECKING:
    from redsl.dsl import Decision
    from redsl.orchestrator import RefactorOrchestrator

logger = logging.getLogger(__name__)


def execute_sandboxed(
    orchestrator: "RefactorOrchestrator",
    decision: "Decision",
    project_dir: Path,
) -> RefactorResult:
    """Execute a decision in a sandboxed environment."""
    from redsl.execution.resolution import _consult_memory, _load_source_code, _resolve_source_path, _remember_decision_result
    from redsl.validation.sandbox import DockerNotFoundError, RefactorSandbox

    source_path = _resolve_source_path(orchestrator, decision, project_dir)
    source_code = _load_source_code(orchestrator, source_path, decision)
    _consult_memory(orchestrator, decision)

    proposal = orchestrator.refactor_engine.generate_proposal(decision, source_code)
    if orchestrator.config.refactor.reflection_rounds > 0:
        proposal = orchestrator.refactor_engine.reflect_on_proposal(proposal, source_code)

    try:
        with RefactorSandbox(project_dir) as sb:
            sandbox_result = sb.apply_and_test(proposal)
    except DockerNotFoundError as exc:
        logger.warning("Sandbox unavailable: %s", exc)
        return RefactorResult(
            proposal=proposal,
            applied=False,
            validated=False,
            errors=[str(exc)],
        )

    if sandbox_result["tests_pass"]:
        result = orchestrator.refactor_engine.apply_proposal(proposal, project_dir)
        result.validated = True
        _remember_decision_result(orchestrator, decision, proposal, result)
        return result

    errors = sandbox_result.get("errors", [])
    orchestrator.memory.remember_action(
        action=decision.action.value,
        target=decision.target_file,
        result=f"Sandbox test failed: {errors[:1]}",
        success=False,
        details={"sandbox_output": sandbox_result.get("output", "")[:300]},
    )
    return RefactorResult(
        proposal=proposal,
        applied=False,
        validated=False,
        errors=errors,
    )


__all__ = ["execute_sandboxed"]
