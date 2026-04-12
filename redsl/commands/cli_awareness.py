"""CLI commands for the awareness subsystem (history, ecosystem, health, predict, self-assess)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click


def _echo_json(payload: Any) -> None:
    click.echo(json.dumps(payload, indent=2, default=str))


def _init_manager(host_module, project_path: Path, ctx: click.Context):
    """Setup logging and build awareness manager."""
    host_module._setup_logging(project_path, ctx.obj.get("verbose", False))
    return host_module._build_awareness_manager()


def _register_history_command(cli: click.Group, host_module) -> None:
    @cli.command("history")
    @click.option("--project", "project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), required=True, help="Project path to inspect")
    @click.option("--depth", "depth", default=20, show_default=True, help="Number of commits to inspect")
    @click.pass_context
    def history(ctx: click.Context, project_path: Path, depth: int) -> None:
        """Show temporal history for a project."""
        manager = _init_manager(host_module, project_path, ctx)
        summary = manager.history(project_path, depth=depth).to_dict()
        _echo_json({"project_path": str(project_path), "depth": depth, **summary})


def _register_ecosystem_command(cli: click.Group, host_module) -> None:
    @cli.command("ecosystem")
    @click.option("--root", "root_path", type=click.Path(exists=True, file_okay=False, path_type=Path), required=True, help="Semcod root path")
    @click.pass_context
    def ecosystem(ctx: click.Context, root_path: Path) -> None:
        """Inspect the project ecosystem graph."""
        manager = _init_manager(host_module, root_path, ctx)
        _echo_json(manager.ecosystem(root_path).summarize())


def _register_health_command(cli: click.Group, host_module) -> None:
    @cli.command("health")
    @click.option("--project", "project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), required=True, help="Project path to assess")
    @click.option("--depth", "depth", default=20, show_default=True, help="History depth for health assessment")
    @click.pass_context
    def health(ctx: click.Context, project_path: Path, depth: int) -> None:
        """Calculate unified health metrics for a project."""
        manager = _init_manager(host_module, project_path, ctx)
        health_report = manager.health(project_path, depth=depth).to_dict()
        _echo_json({"project_path": str(project_path), "depth": depth, **health_report})


def _register_predict_command(cli: click.Group, host_module) -> None:
    @cli.command("predict")
    @click.option("--project", "project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), required=True, help="Project path to forecast")
    @click.option("--depth", "depth", default=20, show_default=True, help="History depth for forecasting")
    @click.pass_context
    def predict(ctx: click.Context, project_path: Path, depth: int) -> None:
        """Predict future project state based on git timeline."""
        manager = _init_manager(host_module, project_path, ctx)
        _echo_json(manager.predict(project_path, depth=depth))


def _register_self_assess_command(cli: click.Group, host_module) -> None:
    @cli.command("self-assess")
    @click.option("--top-k", "top_k", default=5, show_default=True, help="How many capabilities to show")
    @click.pass_context
    def self_assess(ctx: click.Context, top_k: int) -> None:
        """Inspect the agent self-model and memory statistics."""
        manager = _init_manager(host_module, Path.cwd(), ctx)
        _echo_json(manager.self_assess(top_k=top_k))


def register(cli: click.Group, host_module) -> None:
    """Register all awareness commands on the given Click group."""
    _register_history_command(cli, host_module)
    _register_ecosystem_command(cli, host_module)
    _register_health_command(cli, host_module)
    _register_predict_command(cli, host_module)
    _register_self_assess_command(cli, host_module)
