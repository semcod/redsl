"""Refactor command and helpers."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import click

from ..config import AgentConfig
from ..formatters import (
    format_cycle_report_markdown,
    format_cycle_report_yaml,
    format_plan_yaml,
    format_refactor_plan,
    _serialize_analysis,
    _serialize_decision,
    _get_timestamp,
)
from ..orchestrator import RefactorOrchestrator
from .llm_banner import print_llm_banner
from .logging import setup_logging

logger = logging.getLogger(__name__)


def _resolve_cli_export(name: str, fallback: Any) -> Any:
    """Resolve a formatter/helper from `redsl.cli` so tests can monkeypatch it."""
    cli_module = sys.modules.get("redsl.cli")
    if cli_module is not None and hasattr(cli_module, name):
        return getattr(cli_module, name)
    return fallback


@click.command()
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.option("--max-actions", "-n", default=10, help="Maximum number of actions to apply")
@click.option("--dry-run", is_flag=True, help="Show what would be done without applying changes")
@click.option("--format", "-f", default="yaml", type=click.Choice(["text", "yaml", "json"]), help="Output format")
@click.option("--use-code2llm", is_flag=True, help="Use code2llm for PERCEIVE step")
@click.option("--validate-regix", is_flag=True, help="Validate with regix after execution")
@click.option("--rollback", is_flag=True, help="Auto-rollback changes if regix detects regression")
@click.option("--sandbox", is_flag=True, help="Test each refactoring in a Docker sandbox")
@click.option("--target-file", type=str, default=None, help="Restrict decisions to a project-relative file or path prefix")
@click.option("--run-tests", is_flag=True, help="Run project test suite after applying changes; roll back and create planfile task on regression")
@click.option("--from-planfile", is_flag=True, help="Use planfile.yaml todo tasks to guide file-targeted refactoring")
@click.pass_context
def refactor(
    ctx: click.Context,
    project_path: Path,
    max_actions: int,
    dry_run: bool,
    format: str,
    use_code2llm: bool,
    validate_regix: bool,
    rollback: bool,
    sandbox: bool,
    target_file: str | None,
    run_tests: bool,
    from_planfile: bool,
) -> None:
    """Run refactoring on a project."""
    verbose = ctx.obj.get("verbose", False)
    setup_logging_fn = _resolve_cli_export("_setup_logging", setup_logging)
    log_file = setup_logging_fn(project_path, verbose)
    logger.info("reDSL refactor started: %s (max_actions=%d, dry_run=%s)", project_path, max_actions, dry_run)
    print_llm_banner(mode="plan" if dry_run else "mixed")

    if format == "text":
        click.echo(f"Running reDSL on {project_path}", err=True)
        click.echo(f"Log file: {log_file}", err=True)

    config = _build_refactor_config(dry_run, project_path)
    orchestrator_cls = _resolve_cli_export("RefactorOrchestrator", RefactorOrchestrator)
    orchestrator = orchestrator_cls(config)

    analysis, decisions = _collect_refactor_analysis_and_decisions(
        orchestrator,
        project_path,
        max_actions,
        target_file=target_file,
    )

    if dry_run:
        _handle_dry_run(format, decisions, analysis, project_path, log_file)
        return

    if from_planfile:
        _execute_from_planfile(
            orchestrator, project_path, max_actions, use_code2llm,
            validate_regix, rollback, sandbox, run_tests,
        )
        return

    _execute_refactor_cycle(
        orchestrator, project_path, max_actions, use_code2llm,
        validate_regix, rollback, sandbox, target_file,
        decisions, analysis, format, log_file,
        run_tests=run_tests,
    )


def _handle_dry_run(format: str, decisions: list[Any], analysis: Any, project_path: Path, log_file: Path) -> None:
    """Handle dry-run path: emit plan and save markdown + toon reports."""
    _emit_refactor_dry_run(format, decisions, analysis)
    md_report, toon_report = _save_refactor_reports(project_path, None, decisions, analysis, log_file, dry_run=True)
    click.echo(f"Markdown report saved to: {md_report}", err=True)
    click.echo(f"TOON report saved to: {toon_report}", err=True)


def _execute_from_planfile(
    orchestrator: Any,
    project_path: Path,
    max_actions: int,
    use_code2llm: bool,
    validate_regix: bool,
    rollback: bool,
    sandbox: bool,
    run_tests: bool,
) -> None:
    """Execute refactoring cycles guided by planfile.yaml todo tasks."""
    from ..execution.planfile_updater import run_tasks_from_planfile

    click.echo("Running reDSL guided by planfile.yaml tasks...", err=True)
    summary = run_tasks_from_planfile(
        orchestrator,
        project_path,
        max_actions=max_actions,
        use_code2llm=use_code2llm,
        validate_regix=validate_regix,
        rollback_on_failure=rollback,
        use_sandbox=sandbox,
        run_tests=run_tests,
    )
    click.echo(
        f"planfile: attempted={summary['attempted']}, applied={summary['applied']}, skipped={summary['skipped']}",
        err=True,
    )


def _execute_refactor_cycle(
    orchestrator: Any,
    project_path: Path,
    max_actions: int,
    use_code2llm: bool,
    validate_regix: bool,
    rollback: bool,
    sandbox: bool,
    target_file: str | None,
    decisions: list[Any],
    analysis: Any,
    format: str,
    log_file: Path,
    run_tests: bool = False,
) -> None:
    """Execute the refactor cycle (non dry-run path)."""
    if not _prepare_refactor_application(format, sandbox, decisions, analysis):
        return

    report = orchestrator.run_cycle(
        project_path,
        max_actions=max_actions,
        use_code2llm=use_code2llm,
        validate_regix=validate_regix,
        rollback_on_failure=rollback,
        use_sandbox=sandbox,
        target_file=target_file,
        run_tests=run_tests,
    )

    _emit_refactor_live_output(report, decisions, analysis, format)

    md_report, toon_report = _save_refactor_reports(project_path, report, decisions, analysis, log_file, dry_run=False)
    click.echo(f"Markdown report saved to: {md_report}", err=True)
    click.echo(f"TOON report saved to: {toon_report}", err=True)

    logger.info("reDSL refactor complete. Log: %s", log_file)
    click.echo(f"# log: {log_file}", err=True)


def _build_refactor_config(dry_run: bool, project_path: Path | None = None) -> AgentConfig:
    config = AgentConfig.from_env()
    config.refactor.dry_run = dry_run
    if dry_run:
        config.refactor.reflection_rounds = 0
    # Anchor a relative output_dir to the target project so the CLI works
    # regardless of current working directory (avoids PermissionError on '/').
    if project_path is not None:
        output_dir = Path(config.refactor.output_dir)
        if not output_dir.is_absolute():
            config.refactor.output_dir = (Path(project_path).resolve() / output_dir).resolve()
    return config


def _collect_refactor_analysis_and_decisions(
    orchestrator: RefactorOrchestrator,
    project_path: Path,
    max_actions: int,
    target_file: str | None = None,
) -> tuple[Any, list[Any]]:
    logger.info("Starting analysis of %s", project_path)
    analysis = orchestrator.analyzer.analyze_project(project_path)
    contexts = analysis.to_dsl_contexts()
    evaluated = orchestrator.dsl_engine.evaluate(contexts)
    if target_file:
        target_norm = Path(target_file).as_posix().lstrip("./")
        evaluated = [
            decision
            for decision in evaluated
            if _decision_matches_target(decision, target_norm)
        ]

    decisions = sorted(
        evaluated,
        key=lambda decision: getattr(decision, "score", 0),
        reverse=True,
    )[:max_actions]

    if target_file and not decisions:
        from click import ClickException

        raise ClickException(f"No refactoring decisions matched target file: {target_file}")

    return analysis, decisions


def _decision_matches_target(decision: Any, target_norm: str) -> bool:
    decision_target = getattr(decision, "target_file", "")
    if not decision_target:
        return False
    decision_norm = Path(str(decision_target)).as_posix().lstrip("./")
    return decision_norm == target_norm or decision_norm.startswith(f"{target_norm.rstrip('/')}/")


def _emit_refactor_dry_run(format: str, decisions: list[Any], analysis: Any) -> None:
    if format == "text":
        formatter = _resolve_cli_export("format_refactor_plan", format_refactor_plan)
        click.echo(formatter(decisions, "text", analysis))
    elif format == "json":
        click.echo(json.dumps({
            "status": "dry_run",
            "project_metrics": analysis.metrics.to_dict() if hasattr(analysis, "metrics") else {},
            "planned_actions": len(decisions),
        }, indent=2))
    else:
        formatter = _resolve_cli_export("format_plan_yaml", format_plan_yaml)
        click.echo(formatter(decisions, analysis))


def _build_json_report_payload(report: Any, decisions: list[Any], analysis: Any) -> dict:
    """Build the JSON report payload from report, decisions and analysis."""
    serialize_analysis = _resolve_cli_export("_serialize_analysis", _serialize_analysis)
    serialize_decision = _resolve_cli_export("_serialize_decision", _serialize_decision)
    get_timestamp = _resolve_cli_export("_get_timestamp", _get_timestamp)
    return {
        "redsl_report": {
            "timestamp": get_timestamp(),
            "cycle": getattr(report, "cycle_number", 0),
            "analysis": serialize_analysis(analysis) if analysis else {
                "summary": getattr(report, "analysis_summary", ""),
            },
            "decisions": [serialize_decision(d) for d in decisions],
            "plan": {
                "total_decisions": getattr(report, "decisions_count", len(decisions)),
                "decisions": [serialize_decision(d) for d in decisions],
            },
            "execution": {
                "proposals_generated": getattr(report, "proposals_generated", len(getattr(report, "results", []))),
                "proposals_applied": getattr(report, "proposals_applied", len(getattr(report, "applied_changes", []))),
                "proposals_rejected": getattr(report, "proposals_rejected", len(getattr(report, "failed_changes", []))),
            },
            "errors": getattr(report, "errors", []) or [],
        }
    }


def _emit_refactor_live_output(report: Any, decisions: list[Any], analysis: Any, format: str) -> None:
    if format == "text":
        status = getattr(report, "status", None)
        if not status:
            status = "success" if not getattr(report, "errors", []) else "failed"
        click.echo(f"\n=== RESULT: {str(status).upper()} ===")
        click.echo(f"Applied: {getattr(report, 'proposals_applied', len(getattr(report, 'applied_changes', [])))}")
        click.echo(f"Rejected: {getattr(report, 'proposals_rejected', len(getattr(report, 'failed_changes', [])))}")
    elif format == "json":
        payload = _build_json_report_payload(report, decisions, analysis)
        click.echo(json.dumps(payload, indent=2, default=str))
    else:
        formatter = _resolve_cli_export("format_cycle_report_yaml", format_cycle_report_yaml)
        click.echo(formatter(report, decisions, analysis))


def _save_refactor_reports(
    project_path: Path,
    report: Any,
    decisions: list[Any],
    analysis: Any,
    log_file: Path,
    dry_run: bool = False,
) -> tuple[Path, Path]:
    """Save both Markdown and TOON reports.

    Returns:
        Tuple of (markdown_path, toon_path)
    """
    from ..formatters import format_cycle_report_toon

    # Use fixed filenames for test compatibility
    md_name = "redsl_refactor_plan.md" if dry_run else "redsl_refactor_report.md"
    toon_name = "redsl_refactor_plan.toon.yaml" if dry_run else "redsl_refactor_report.toon.yaml"

    md_file = project_path / md_name
    toon_file = project_path / toon_name

    # Markdown report (for humans)
    md_content = format_cycle_report_markdown(
        report=report,
        decisions=decisions,
        project_path=project_path,
        analysis=analysis,
        log_file=log_file,
        dry_run=dry_run,
    )
    md_file.write_text(md_content, encoding="utf-8")

    # TOON report (for planfile integration)
    toon_content = format_cycle_report_toon(
        report=report,
        decisions=decisions,
        project_path=project_path,
        analysis=analysis,
        log_file=log_file,
        dry_run=dry_run,
    )
    toon_file.write_text(toon_content, encoding="utf-8")

    return md_file, toon_file


def _prepare_refactor_application(
    format: str,
    sandbox: bool,
    decisions: list[Any],
    analysis: Any,
) -> bool:
    if format == "text":
        from ..formatters import format_refactor_plan
        click.echo(format_refactor_plan(decisions, "text", analysis), err=True)
        if not click.confirm("\nApply these changes?", err=True):
            return False
        click.echo("\n=== APPLYING REFACTORING ===", err=True)

    if sandbox:
        click.echo("Sandbox mode: each refactoring will be tested in Docker before applying.", err=True)

    return True


def register_refactor(cli: click.Group) -> None:
    cli.add_command(refactor)
