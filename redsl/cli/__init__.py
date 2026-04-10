"""Command-line interface for reDSL."""

from __future__ import annotations

import os
import sys

os.environ.setdefault("LITELLM_LOG", "ERROR")

from dotenv import load_dotenv
load_dotenv()

import click

from .logging import setup_logging as _setup_logging
from .refactor import register_refactor, _save_refactor_markdown_report
from .batch import register_batch
from .pyqual import register_pyqual
from .debug import register_debug
from .examples import register_examples
from .scan import scan
from .utils import perf_command, cost_command

# Import for test compatibility
from ..orchestrator import RefactorOrchestrator
from ..commands import batch_pyqual as batch_pyqual_commands
from ..formatters import format_plan_yaml, _serialize_analysis, format_refactor_plan, _serialize_decision, _get_timestamp, format_cycle_report_yaml

# Backward-compatible exports for tests
__all__ = [
    "cli",
    "_setup_logging",
    "_save_refactor_markdown_report",
    "RefactorOrchestrator",
    "batch_pyqual_commands",
    "format_plan_yaml",
    "_serialize_analysis",
    "format_refactor_plan",
    "_serialize_decision",
    "_get_timestamp",
    "format_cycle_report_yaml",
]


@click.group()
@click.version_option(version="1.2.0")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """reDSL - Automated code refactoring tool."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


def _register_all(cli_group: click.Group) -> None:
    cli_group.add_command(scan)
    register_refactor(cli_group)
    register_batch(cli_group)
    register_pyqual(cli_group)
    register_debug(cli_group)
    register_examples(cli_group)
    cli_group.add_command(perf_command)
    cli_group.add_command(cost_command)
    from ..commands.cli_doctor import register as _register_doctor
    from ..commands.cli_autonomy import register as _register_autonomy
    _register_doctor(cli_group)
    _register_autonomy(cli_group, sys.modules[__name__])


_register_all(cli)

if __name__ == "__main__":
    cli()
