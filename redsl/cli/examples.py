"""Example commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import click


@click.group()
def example() -> None:
    """Run built-in examples and demos."""


@example.command("basic-analysis")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_basic_analysis(scenario: str, source: str | None) -> None:
    """Run the basic code-analysis demo."""
    from ..examples.basic_analysis import run_basic_analysis_example
    run_basic_analysis_example(scenario=scenario, source=source)


@example.command("custom-rules")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_custom_rules(scenario: str, source: str | None) -> None:
    """Run the custom DSL rules demo."""
    from ..examples.custom_rules import run_custom_rules_example
    run_custom_rules_example(scenario=scenario, source=source)


@example.command("full-pipeline")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--model", default=None, help="Override LLM model")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_full_pipeline(scenario: str, model: str | None, source: str | None) -> None:
    """Run the full refactoring-pipeline demo (requires LLM key)."""
    from ..examples.full_pipeline import run_full_pipeline_example
    run_full_pipeline_example(scenario=scenario, source=source, model=model)


@example.command("memory-learning")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_memory_learning(scenario: str, source: str | None) -> None:
    """Run the agent-memory demo (episodic / semantic / procedural)."""
    from ..examples.memory_learning import run_memory_learning_example
    run_memory_learning_example(scenario=scenario, source=source)


@example.command("api-integration")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_api_integration(scenario: str, source: str | None) -> None:
    """Show API curl / httpx / WebSocket usage examples."""
    from ..examples.api_integration import run_api_integration_example
    run_api_integration_example(scenario=scenario, source=source)


@example.command("awareness")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_awareness(scenario: str, source: str | None) -> None:
    """Run the awareness / change-pattern detection demo."""
    from ..examples.awareness import run_awareness_example
    run_awareness_example(scenario=scenario, source=source)


@example.command("pyqual")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_pyqual(scenario: str, source: str | None) -> None:
    """Run the PyQual code-quality analysis demo."""
    from ..examples.pyqual_example import run_pyqual_example
    run_pyqual_example(scenario=scenario, source=source)


@example.command("audit")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_audit(scenario: str, source: str | None) -> None:
    """Run One-click Audit - full scan -> grade report -> badge."""
    from ..examples.audit import run_audit_example
    run_audit_example(scenario=scenario, source=source)


@example.command("pr-bot")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_pr_bot(scenario: str, source: str | None) -> None:
    """Run PR Bot - realistic GitHub PR comment preview."""
    from ..examples.pr_bot import run_pr_bot_example
    run_pr_bot_example(scenario=scenario, source=source)


@example.command("badge")
@click.option("--scenario", "-s", default="default", type=click.Choice(["default", "advanced"]), help="Scenario variant")
@click.option("--source", type=click.Path(exists=True), default=None, help="Custom YAML file")
def example_badge(scenario: str, source: str | None) -> None:
    """Run Badge Generator - grade A+ to F with Markdown/HTML code."""
    from ..examples.badge import run_badge_example
    run_badge_example(scenario=scenario, source=source)


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
