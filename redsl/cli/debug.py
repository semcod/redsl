"""Debug commands."""

from __future__ import annotations

from pathlib import Path

import click


@click.group()
def debug() -> None:
    """Debug utilities for development."""


@debug.command("ast")
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.option("--file", help="Show AST for specific file")
def debug_ast(project_path: Path, file: str) -> None:
    """Show AST analysis for debugging."""
    from ..analyzers import CodeAnalyzer
    if file:
        file_path = project_path / file
        if not file_path.exists():
            click.echo(f"File not found: {file_path}")
            return
        analyzer = CodeAnalyzer(project_path)
        analysis = analyzer.analyze_file(file_path)
        click.echo(f"AST for {file}:")
        click.echo(analysis)
    else:
        analyzer = CodeAnalyzer(project_path)
        analysis = analyzer.analyze_project(project_path)
        click.echo(f"Project AST summary for {project_path}:")
        click.echo(f"Files: {len(analysis.file_analyses)}")


@debug.command("llm")
@click.argument("prompt")
@click.option("--model", default="gpt-4o", help="LLM model to use")
def debug_llm(prompt: str, model: str) -> None:
    """Test LLM with a simple prompt."""
    from ..llm.provider import LLMProvider
    provider = LLMProvider(model=model)
    response = provider.generate(prompt)
    click.echo(f"Response from {model}:")
    click.echo(response)


@debug.command("metrics")
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
def debug_metrics(project_path: Path) -> None:
    """Show project metrics for debugging."""
    from ..autonomy.metrics import collect_autonomy_metrics
    metrics = collect_autonomy_metrics(project_path)
    click.echo(f"Metrics for {project_path}:")
    click.echo(metrics.to_dict())


def register_debug(cli: click.Group) -> None:
    cli.add_command(debug)
