"""Refactor command and helpers."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import click

from ..config import AgentConfig
from ..formatters import (
    format_cycle_report_markdown,
    format_cycle_report_yaml,
    format_refactor_plan,
    _get_timestamp,
)
from ..orchestrator import RefactorOrchestrator
from .logging import setup_logging

logger = logging.getLogger(__name__)


@click.command()
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.option("--max-actions", "-n", default=10, help="Maximum number of actions to apply")
@click.option("--dry-run", is_flag=True, help="Show what would be done without applying changes")
@click.option("--format", "-f", default="yaml", type=click.Choice(["text", "yaml", "json"]), help="Output format")
@click.option("--use-code2llm", is_flag=True, help="Use code2llm for PERCEIVE step")
@click.option("--validate-regix", is_flag=True, help="Validate with regix after execution")
@click.option("--rollback", is_flag=True, help="Auto-rollback changes if regix detects regression")
@click.option("--sandbox", is_flag=True, help="Test each refactoring in a Docker sandbox")
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
) -> None:
    """Run refactoring on a project."""
    verbose = ctx.obj.get("verbose", False)
    log_file = setup_logging(project_path, verbose)
    logger.info("reDSL refactor started: %s (max_actions=%d, dry_run=%s)", project_path, max_actions, dry_run)

    if format == "text":
        click.echo(f"Running reDSL on {project_path}", err=True)
        click.echo(f"Log file: {log_file}", err=True)

    config = _build_refactor_config(dry_run)
    orchestrator = RefactorOrchestrator(config)

    analysis, decisions = _collect_refactor_analysis_and_decisions(orchestrator, project_path, max_actions)

    if dry_run:
        _emit_refactor_dry_run(format, decisions, analysis)
        markdown_report = _save_refactor_markdown_report(project_path, None, decisions, analysis, log_file, dry_run=True)
        click.echo(f"Markdown report saved to: {markdown_report}", err=True)
        return

    if not _prepare_refactor_application(format, sandbox, decisions, analysis):
        return

    report = orchestrator.run_cycle(
        project_path,
        max_actions=max_actions,
        use_code2llm=use_code2llm,
        validate_regix=validate_regix,
        rollback_on_failure=rollback,
        use_sandbox=sandbox,
    )

    _emit_refactor_live_output(report, decisions, analysis, format)

    markdown_report = _save_refactor_markdown_report(project_path, report, decisions, analysis, log_file, dry_run=False)
    click.echo(f"Markdown report saved to: {markdown_report}", err=True)

    logger.info("reDSL refactor complete. Log: %s", log_file)
    click.echo(f"# log: {log_file}", err=True)


def _build_refactor_config(dry_run: bool) -> AgentConfig:
    config = AgentConfig.from_env()
    config.refactor.dry_run = dry_run
    if dry_run:
        config.refactor.reflection_rounds = 0
    return config


def _collect_refactor_analysis_and_decisions(
    orchestrator: RefactorOrchestrator,
    project_path: Path,
    max_actions: int,
) -> tuple[Any, list[Any]]:
    logger.info("Starting analysis of %s", project_path)
    analysis = orchestrator.analyzer.analyze_project(project_path)
    contexts = analysis.to_dsl_contexts()
    decisions = orchestrator.dsl_engine.evaluate(contexts)[:max_actions]
    return analysis, decisions


def _emit_refactor_dry_run(format: str, decisions: list[Any], analysis: Any) -> None:
    if format == "text":
        click.echo("DRY RUN - Planned actions:")
        for i, decision in enumerate(decisions, 1):
            click.echo(f"  {i}. {decision.action.value} on {decision.target_file}")
    elif format == "json":
        click.echo(json.dumps({
            "status": "dry_run",
            "project_metrics": analysis.metrics.to_dict() if hasattr(analysis, "metrics") else {},
            "planned_actions": len(decisions),
        }, indent=2))
    else:
        click.echo(format_refactor_plan(decisions, "yaml", analysis))


def _emit_refactor_live_output(report: Any, decisions: list[Any], analysis: Any, format: str) -> None:
    if format == "text":
        click.echo(f"\n=== RESULT: {report.status.upper()} ===")
        click.echo(f"Applied: {len(report.applied_changes)}")
        click.echo(f"Failed: {len(report.failed_changes)}")
    elif format == "json":
        click.echo(json.dumps({
            "status": report.status,
            "applied": len(report.applied_changes),
            "failed": len(report.failed_changes),
            "metrics": report.metrics.to_dict() if hasattr(report, "metrics") else {},
        }, indent=2))
    else:
        click.echo(format_cycle_report_yaml(report))


def _save_refactor_markdown_report(
    project_path: Path,
    report: Any,
    decisions: list[Any],
    analysis: Any,
    log_file: Path,
    dry_run: bool = False,
) -> Path:
    # Use fixed filenames for test compatibility
    report_name = "redsl_refactor_plan.md" if dry_run else "redsl_refactor_report.md"
    report_file = project_path / report_name

    content = format_cycle_report_markdown(
        report=report,
        decisions=decisions,
        project_path=project_path,
        analysis=analysis,
        log_file=log_file,
        dry_run=dry_run,
    )

    report_file.write_text(content, encoding="utf-8")
    return report_file


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
