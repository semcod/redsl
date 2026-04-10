"""Hybrid quality fixes (no LLM) for autofix package."""

from __future__ import annotations

import logging
from pathlib import Path

from ...analyzers import CodeAnalyzer
from ...config import AgentConfig
from ...dsl import RefactorAction
from ...execution import _execute_direct_refactor
from ...orchestrator import RefactorOrchestrator

logger = logging.getLogger(__name__)


def _run_hybrid_fix(project: Path, max_changes: int = 30) -> tuple[int, int]:
    """Apply hybrid quality refactorings. Returns (applied, errors)."""
    try:
        quality_actions = [
            RefactorAction.REMOVE_UNUSED_IMPORTS,
            RefactorAction.FIX_MODULE_EXECUTION_BLOCK,
            RefactorAction.EXTRACT_CONSTANTS,
            RefactorAction.ADD_RETURN_TYPES,
        ]

        config = AgentConfig()
        config.refactor.apply_changes = True
        config.refactor.reflection_rounds = 0

        orchestrator = RefactorOrchestrator(config)
        analyzer = CodeAnalyzer()

        analysis = analyzer.analyze_project(project)
        contexts = analysis.to_dsl_contexts()
        all_decisions = orchestrator.dsl_engine.evaluate(contexts)

        quality_decisions = [d for d in all_decisions if d.action in quality_actions]
        quality_decisions.sort(key=lambda d: d.score, reverse=True)

        applied = 0
        errors = 0
        for decision in quality_decisions[:max_changes]:
            try:
                result = _execute_direct_refactor(orchestrator, decision, project)
                if result.applied:
                    applied += 1
                else:
                    errors += 1
            except Exception as exc:
                logger.debug("Fix failed for %s: %s", decision.target_file, exc)
                errors += 1

        return applied, errors
    except Exception as exc:
        logger.warning("Hybrid fix failed for %s: %s", project.name, exc)
        return 0, 1
