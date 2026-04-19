"""Example commands."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import click


def _run_example(module: str, fn: str, **kwargs: Any) -> None:
    """Import *module* from ``redsl.examples`` and call *fn* with *kwargs*."""
    mod = importlib.import_module(f"redsl.examples.{module}")
    getattr(mod, fn)(**kwargs)


@click.group()
def example() -> None:
    """Run built-in examples and demos."""


@example.command("basic-analysis")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_basic_analysis(scenario: str, source: str | None) -> None:
    """Run the basic code-analysis demo."""
    _run_example("basic_analysis", "run_basic_analysis_example", scenario=scenario, source=source)


@example.command("custom-rules")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_custom_rules(scenario: str, source: str | None) -> None:
    """Run the custom DSL rules demo."""
    _run_example("custom_rules", "run_custom_rules_example", scenario=scenario, source=source)


@example.command("full-pipeline")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--model", default=None, help="Override LLM model")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_full_pipeline(scenario: str, model: str | None, source: str | None) -> None:
    """Run the full refactoring-pipeline demo (requires LLM key)."""
    _run_example("full_pipeline", "run_full_pipeline_example", scenario=scenario, source=source, model=model)


@example.command("memory-learning")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_memory_learning(scenario: str, source: str | None) -> None:
    """Run the agent-memory demo (episodic / semantic / procedural)."""
    _run_example("memory_learning", "run_memory_learning_example", scenario=scenario, source=source)


@example.command("api-integration")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_api_integration(scenario: str, source: str | None) -> None:
    """Show API curl / httpx / WebSocket usage examples."""
    _run_example("api_integration", "run_api_integration_example", scenario=scenario, source=source)


@example.command("awareness")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_awareness(scenario: str, source: str | None) -> None:
    """Run the awareness / change-pattern detection demo."""
    _run_example("awareness", "run_awareness_example", scenario=scenario, source=source)


@example.command("pyqual")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_pyqual(scenario: str, source: str | None) -> None:
    """Run the PyQual code-quality analysis demo."""
    _run_example("pyqual_example", "run_pyqual_example", scenario=scenario, source=source)


@example.command("audit")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_audit(scenario: str, source: str | None) -> None:
    """Run One-click Audit - full scan -> grade report -> badge."""
    _run_example("audit", "run_audit_example", scenario=scenario, source=source)


@example.command("pr-bot")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_pr_bot(scenario: str, source: str | None) -> None:
    """Run PR Bot - realistic GitHub PR comment preview."""
    _run_example("pr_bot", "run_pr_bot_example", scenario=scenario, source=source)


@example.command("badge")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_badge(scenario: str, source: str | None) -> None:
    """Run Badge Generator - grade A+ to F with Markdown/HTML code."""
    _run_example("badge", "run_badge_example", scenario=scenario, source=source)


@example.command("list")
def example_list() -> None:
    """List available example scenarios."""
    from ..examples._common import list_available_examples
    items = list_available_examples()
    if not items:
        click.echo("  (no examples found - check REDSL_EXAMPLES_DIR or repo layout)")
        return
    for item in items:
        advanced = "v" if item["has_advanced"] else " "
        click.echo(f"  {item['name'].replace('_', '-'):25s} {item['title']}  [advanced: {advanced}]")


def register_examples(cli: click.Group) -> None:
    cli.add_command(example)
