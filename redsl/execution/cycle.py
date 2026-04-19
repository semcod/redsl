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


def _run_perceive_phase(
    orchestrator: "RefactorOrchestrator",
    project_dir: Path,
    use_code2llm: bool,
    report: "CycleReport",
) -> "AnalysisResult":
    """Run PERCEIVE phase: analyze project and enrich data."""
    logger.info("=== CYCLE %d: PERCEIVE ===", orchestrator._cycle_count)
    analysis = _analyze_project(orchestrator, project_dir, use_code2llm)

    from redsl.analyzers import redup_bridge
    if redup_bridge.is_available():
        analysis = redup_bridge.enrich_analysis(analysis, project_dir)
        dup_count = len(analysis.duplicates)
        if dup_count:
            logger.info("redup: enriched analysis with %d duplicate groups", dup_count)

    report.analysis_summary = _summarize_analysis(analysis)
    return analysis


def _run_decide_phase(
    orchestrator: "RefactorOrchestrator",
    analysis: "AnalysisResult",
    max_actions: int,
    target_file: str | None,
    validate_regix: bool,
    run_tests: bool,
    project_dir: Path,
) -> tuple[list, "Any", "Any"]:
    """Run DECIDE phase: select decisions and prepare validation snapshots."""
    from redsl.execution.decision import _select_decisions
    from redsl.execution.resolution import _consult_memory_for_decisions
    from redsl.execution.test_validation import run_tests_baseline
    from redsl.execution.validation import _snapshot_regix_before

    logger.info("=== CYCLE %d: DECIDE ===", orchestrator._cycle_count)
    decisions = _select_decisions(orchestrator, analysis, max_actions, target_file=target_file)

    if not decisions:
        logger.info("No refactoring decisions — code looks good!")
        return [], None, None

    regix_before = _snapshot_regix_before(project_dir, validate_regix)
    _consult_memory_for_decisions(orchestrator, decisions)
    tests_baseline = run_tests_baseline(project_dir) if run_tests else None

    return decisions, regix_before, tests_baseline


def _run_execute_phase(
    orchestrator: "RefactorOrchestrator",
    decisions: list,
    project_dir: Path,
    use_sandbox: bool,
    report: "CycleReport",
) -> None:
    """Run PLAN + EXECUTE phase: apply decisions."""
    from redsl.execution.decision import _execute_decisions
    logger.info("=== CYCLE %d: PLAN + EXECUTE ===", orchestrator._cycle_count)
    _execute_decisions(orchestrator, decisions, project_dir, use_sandbox, report)


def _run_validate_phase(
    orchestrator: "RefactorOrchestrator",
    project_dir: Path,
    regix_before: "Any",
    rollback_on_failure: bool,
    validate_regix: bool,
    report: "CycleReport",
) -> None:
    """Run VALIDATE phase: check regix compliance."""
    from redsl.execution.validation import _validate_with_regix
    if validate_regix and report.proposals_applied > 0:
        logger.info("=== CYCLE %d: VALIDATE (regix) ===", orchestrator._cycle_count)
        _validate_with_regix(project_dir, regix_before, rollback_on_failure, report)


def _get_applied_files(report: "CycleReport") -> list[str]:
    """Extract list of applied file paths from report results."""
    return [
        ch.file_path
        for r in report.results
        if r.applied and r.proposal
        for ch in r.proposal.changes
    ]


def _run_update_planfile_phase(
    orchestrator: "RefactorOrchestrator",
    project_dir: Path,
    report: "CycleReport",
) -> None:
    """Run UPDATE PLANFILE phase: mark completed tasks."""
    if report.proposals_applied > 0:
        logger.info("=== CYCLE %d: UPDATE PLANFILE ===", orchestrator._cycle_count)
        from redsl.execution.planfile_updater import mark_applied_tasks_done
        applied_files = _get_applied_files(report)
        updated = mark_applied_tasks_done(project_dir, applied_files)
        if updated:
            logger.info("planfile: marked %d task(s) done", updated)


def _run_test_validation_phase(
    orchestrator: "RefactorOrchestrator",
    project_dir: Path,
    tests_baseline: "Any",
    run_tests: bool,
    report: "CycleReport",
) -> None:
    """Run VALIDATE (tests) phase."""
    from redsl.execution.test_validation import validate_with_tests
    if run_tests and report.proposals_applied > 0:
        logger.info("=== CYCLE %d: VALIDATE (tests) ===", orchestrator._cycle_count)
        applied_files = _get_applied_files(report)
        validate_with_tests(project_dir, tests_baseline, applied_files, report)


def _run_reflect_phase(
    orchestrator: "RefactorOrchestrator",
    report: "CycleReport",
) -> None:
    """Run REFLECT phase: learn from cycle results."""
    from redsl.execution.reflector import _reflect_on_cycle
    logger.info("=== CYCLE %d: REFLECT ===", orchestrator._cycle_count)
    _reflect_on_cycle(orchestrator, report)


def run_cycle(
    orchestrator: "RefactorOrchestrator",
    project_dir: Path,
    max_actions: int = 5,
    use_code2llm: bool = False,
    validate_regix: bool = False,
    rollback_on_failure: bool = False,
    use_sandbox: bool = False,
    target_file: str | None = None,
    run_tests: bool = False,
) -> "CycleReport":
    """Run a complete refactoring cycle."""
    orchestrator._cycle_count += 1
    report = _new_cycle_report(orchestrator)

    try:
        analysis = _run_perceive_phase(orchestrator, project_dir, use_code2llm, report)

        decisions, regix_before, tests_baseline = _run_decide_phase(
            orchestrator, analysis, max_actions, target_file, validate_regix, run_tests, project_dir
        )
        report.decisions_count = len(decisions)

        if not decisions:
            return report

        _run_execute_phase(orchestrator, decisions, project_dir, use_sandbox, report)
        _run_validate_phase(orchestrator, project_dir, regix_before, rollback_on_failure, validate_regix, report)
        _run_update_planfile_phase(orchestrator, project_dir, report)
        _run_test_validation_phase(orchestrator, project_dir, tests_baseline, run_tests, report)
        _run_reflect_phase(orchestrator, report)

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
