"""Utility commands for CLI."""

from __future__ import annotations

from pathlib import Path

import click

from redsl.config import AgentConfig
from redsl.execution import estimate_cycle_cost
from redsl.orchestrator import RefactorOrchestrator
from redsl.cli.logging import setup_logging


@click.command()
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.pass_context
def perf_command(ctx: click.Context, project_path: Path) -> None:
    """Profile a refactoring cycle and report performance bottlenecks."""
    setup_logging(project_path, ctx.obj.get("verbose", False))
    from redsl.diagnostics.perf_bridge import generate_optimization_report
    click.echo(generate_optimization_report(project_path))


@click.command()
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.option("--max-actions", "-n", default=10, help="Number of actions to estimate")
@click.pass_context
def cost_command(ctx: click.Context, project_path: Path, max_actions: int) -> None:
    """Estimate LLM cost for the next refactoring cycle without running it."""
    setup_logging(project_path, ctx.obj.get("verbose", False))
    config = AgentConfig.from_env()
    orchestrator = RefactorOrchestrator(config)
    items = estimate_cycle_cost(orchestrator, project_path, max_actions=max_actions)

    click.echo(f"Planned refactoring cost estimate ({len(items)} actions):")
    total = 0.0
    for i, item in enumerate(items, 1):
        cost_str = f"${item['cost_usd']:.4f}" if item["cost_usd"] > 0 else "$0.000 (direct)"
        click.echo(
            f"  [{i}] {item['action']} -> {item['target_file']}"
            f" Model: {item['model']} | Est. tokens: {item['tokens']} | Cost: {cost_str}"
        )
        total += item["cost_usd"]
    click.echo(f"\n  Total: ~${total:.4f} for {len(items)} actions")
