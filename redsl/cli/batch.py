"""Batch commands."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import click

from redsl.commands import autofix as autofix_commands
from redsl.commands import batch as batch_commands
from redsl.commands import batch_pyqual as batch_pyqual_commands
from redsl.commands import hybrid as hybrid_commands
from redsl.formatters import format_batch_results
from redsl.cli.llm_banner import print_llm_banner
from redsl.cli.logging import setup_logging


@click.group()
def batch() -> None:
    """Batch refactoring commands."""


@batch.command("semcod")
@click.argument("semcod_root", type=click.Path(exists=True, path_type=Path))
@click.option("--max-actions", "-n", default=10, help="Maximum actions per project")
@click.option("--format", "-f", default="text", type=click.Choice(["text", "yaml", "json"]), help="Output format")
def batch_semcod(semcod_root: Path, max_actions: int, format: str) -> None:
    """Apply refactoring to semcod projects."""
    print_llm_banner(mode="mixed")
    if format == "text":
        click.echo(f"Batch processing semcod projects in {semcod_root}")
    results = batch_commands.run_semcod_batch(semcod_root, max_actions)

    formatted_results = []
    for detail in results.get("project_details", []):
        formatted_results.append({
            "project_name": detail["name"],
            "status": "success",
            "files_processed": detail.get("files", 0),
            "changes_applied": detail["applied"],
            "todo_reduction": detail.get("todo_reduction", 0)
        })

    formatted_output = format_batch_results(formatted_results, format)
    click.echo(formatted_output)


@batch.command("hybrid")
@click.argument("semcod_root", type=click.Path(exists=True, path_type=Path))
@click.option("--max-changes", "-n", default=30, help="Maximum changes per project")
def batch_hybrid(semcod_root: Path, max_changes: int) -> None:
    """Apply hybrid quality refactorings (no LLM needed)."""
    print_llm_banner(mode="direct")
    hybrid_commands.run_hybrid_batch(semcod_root, max_changes)


@batch.command("autofix")
@click.argument("semcod_root", type=click.Path(exists=True, path_type=Path))
@click.option("--max-changes", "-n", default=30, help="Maximum changes per project")
@click.pass_context
def batch_autofix(ctx: click.Context, semcod_root: Path, max_changes: int) -> None:
    """Auto-fix all packages: scan -> generate TODO.md -> apply hybrid fixes -> gate fix."""
    setup_logging(semcod_root, ctx.obj.get("verbose", False))
    print_llm_banner(mode="direct")
    autofix_commands.run_autofix_batch(semcod_root, max_changes)


@batch.command("pyqual-run")
@click.argument("workspace_root", type=click.Path(exists=True, path_type=Path))
@click.option("--max-fixes", "-n", default=30, help="Maximum ReDSL fixes per project")
@click.option("--limit", "-l", default=0, help="Process only first N projects (0=all)")
@click.option("--include", multiple=True, help="Only run matching repos (glob)")
@click.option("--exclude", multiple=True, help="Skip matching repos (glob)")
@click.option("--profile", default="auto", help="pyqual init profile")
@click.option("--pipeline/--no-pipeline", default=False, help="Run full pyqual pipeline")
@click.option("--push/--no-push", default=False, help="Git commit + push after fixes")
@click.option("--publish/--no-publish", default=False, help="Require publish-capable pyqual pipeline")
@click.option("--fix-config/--no-fix-config", default=False, help="Run pyqual config auto-fix")
@click.option("--dry-run/--no-dry-run", default=False, help="Verify without mutating")
@click.option("--skip-dirty/--allow-dirty", default=False, help="Skip repos with local changes")
@click.option("--fail-fast/--no-fail-fast", default=False, help="Stop batch on first failed project")
@click.pass_context
def batch_pyqual_run(
    ctx: click.Context,
    workspace_root: Path,
    max_fixes: int,
    limit: int,
    include: tuple[str, ...],
    exclude: tuple[str, ...],
    profile: str,
    pipeline: bool,
    push: bool,
    publish: bool,
    fix_config: bool,
    dry_run: bool,
    skip_dirty: bool,
    fail_fast: bool,
) -> None:
    """Multi-project quality pipeline: ReDSL analysis + pyqual gates + optional push."""
    setup_logging(workspace_root, ctx.obj.get("verbose", False))
    print_llm_banner(mode="direct")
    batch_pyqual_commands.run_pyqual_batch(
        workspace_root,
        max_fixes,
        pipeline,
        push,
        limit=limit,
        include=include,
        exclude=exclude,
        profile=profile,
        publish=publish,
        fix_config=fix_config,
        dry_run=dry_run,
        skip_dirty=skip_dirty,
        fail_fast=fail_fast,
    )


def register_batch(cli: click.Group) -> None:
    cli.add_command(batch)
