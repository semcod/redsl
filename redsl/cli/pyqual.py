"""Pyqual commands."""

from __future__ import annotations

from pathlib import Path

import click

from redsl.commands import pyqual as pyqual_commands
from redsl.cli.llm_banner import print_llm_banner


@click.group()
def pyqual() -> None:
    """Python code quality analysis commands."""


@pyqual.command("analyze")
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.option("--config", "-c", type=click.Path(exists=True, path_type=Path), help="Path to pyqual.yaml config")
@click.option("--format", "-f", default="yaml", type=click.Choice(["yaml", "json"]), help="Output format")
def pyqual_analyze(project_path: Path, config: Path, format: str) -> None:
    """Analyze Python code quality."""
    print_llm_banner(mode="plan")
    pyqual_commands.run_pyqual_analysis(project_path, config, format)


@pyqual.command("fix")
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.option("--config", "-c", type=click.Path(exists=True, path_type=Path), help="Path to pyqual.yaml config")
def pyqual_fix(project_path: Path, config: Path) -> None:
    """Apply automatic quality fixes."""
    print_llm_banner(mode="direct")
    pyqual_commands.run_pyqual_fix(project_path, config)


def register_pyqual(cli: click.Group) -> None:
    cli.add_command(pyqual)
