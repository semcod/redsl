"""Main refactoring cycle orchestration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from redsl.analyzers import AnalysisResult
from redsl.analyzers import code2llm_bridge

if TYPE_CHECKING:
    from redsl.orchestrator import CycleReport, RefactorOrchestrator

logger = logging.getLogger(__name__)


def _new_cycle_report(orchestrator: "RefactorOrchestrator") -> "CycleReport":
    from redsl.orchestrator import CycleReport

    return CycleReport(
        cycle_number=orchestrator._cycle_count,
        analysis_summary="",
        decisions_count=0,
        proposals_generated=0,
        proposals_applied=0,
        proposals_rejected=0,
    )


def _analyze_project(
    orchestrator: "RefactorOrchestrator",
    project_dir: Path,
    use_code2llm: bool,
) -> AnalysisResult:
    if use_code2llm:
        return code2llm_bridge.maybe_analyze(project_dir, orchestrator.analyzer) \
            or orchestrator.analyzer.analyze_project(project_dir)
    return orchestrator.analyzer.analyze_project(project_dir)


def _summarize_analysis(analysis: AnalysisResult) -> str:
    return (
        f"{analysis.total_files} files, {analysis.total_lines} lines, "
        f"avg CC={analysis.avg_cc:.1f}, {analysis.critical_count} critical"
    )


def run_cycle(
    orchestrator: "RefactorOrchestrator",
    project_dir: Path,
    max_actions: int = 5,
    use_code2llm: bool = False,
    validate_regix: bool = False,
    rollback_on_failure: bool = False,
    use_sandbox: bool = False,
) -> "CycleReport":
    """Run a complete refactoring cycle."""
    from redsl.execution.decision import _execute_decisions
    from redsl.execution.reflector import _reflect_on_cycle
    from redsl.execution.resolution import _consult_memory_for_decisions
    from redsl.execution.validation import _snapshot_regix_before, _validate_with_regix

    orchestrator._cycle_count += 1
    report = _new_cycle_report(orchestrator)

    try:
        logger.info("=== CYCLE %d: PERCEIVE ===", orchestrator._cycle_count)
        analysis = _analyze_project(orchestrator, project_dir, use_code2llm)
        report.analysis_summary = _summarize_analysis(analysis)

        logger.info("=== CYCLE %d: DECIDE ===", orchestrator._cycle_count)
        from redsl.execution.decision import _select_decisions
        decisions = _select_decisions(orchestrator, analysis, max_actions)
        report.decisions_count = len(decisions)

        if not decisions:
            logger.info("No refactoring decisions — code looks good!")
            return report

        regix_before = _snapshot_regix_before(project_dir, validate_regix)
        _consult_memory_for_decisions(orchestrator, decisions)

        logger.info("=== CYCLE %d: PLAN + EXECUTE ===", orchestrator._cycle_count)
        _execute_decisions(orchestrator, decisions, project_dir, use_sandbox, report)

        if validate_regix and report.proposals_applied > 0:
            logger.info("=== CYCLE %d: VALIDATE (regix) ===", orchestrator._cycle_count)
            _validate_with_regix(project_dir, regix_before, rollback_on_failure, report)

        logger.info("=== CYCLE %d: REFLECT ===", orchestrator._cycle_count)
        _reflect_on_cycle(orchestrator, report)

    except Exception as e:
        logger.error("Cycle %d failed: %s", orchestrator._cycle_count, e)
        report.errors.append(str(e))

    return report


def run_from_toon_content(
    orchestrator: "RefactorOrchestrator",
    project_toon: str = "",
    duplication_toon: str = "",
    validation_toon: str = "",
    source_files: dict[str, str] | None = None,
    max_actions: int = 5,
) -> "CycleReport":
    """Run a cycle from pre-parsed toon content."""
    from redsl.execution.reflector import _reflect_on_cycle
    from redsl.orchestrator import CycleReport

    orchestrator._cycle_count += 1
    report = CycleReport(
        cycle_number=orchestrator._cycle_count,
        analysis_summary="",
        decisions_count=0,
        proposals_generated=0,
        proposals_applied=0,
        proposals_rejected=0,
    )

    analysis = orchestrator.analyzer.analyze_from_toon_content(
        project_toon=project_toon,
        duplication_toon=duplication_toon,
        validation_toon=validation_toon,
    )
    report.analysis_summary = (
        f"{analysis.total_files} files, {analysis.total_lines} lines"
    )

    contexts = analysis.to_dsl_contexts()
    from redsl.execution.decision import _select_decisions
    decisions = orchestrator.dsl_engine.top_decisions(contexts, limit=max_actions)
    report.decisions_count = len(decisions)

    for decision in decisions:
        if not decision.should_execute:
            continue

        source = (source_files or {}).get(decision.target_file, "# source not provided")

        try:
            proposal = orchestrator.refactor_engine.generate_proposal(decision, source)
            proposal = orchestrator.refactor_engine.reflect_on_proposal(proposal, source)
            result = orchestrator.refactor_engine.validate_proposal(proposal, project_dir=project_dir)
            report.results.append(result)
            report.proposals_generated += 1

            if result.validated:
                orchestrator.refactor_engine._save_proposal(proposal)

        except Exception as e:
            logger.error("Failed: %s", e)
            report.errors.append(str(e))

    _reflect_on_cycle(orchestrator, report)

    return report


__all__ = ["_new_cycle_report", "_analyze_project", "_summarize_analysis", "run_cycle", "run_from_toon_content"]
