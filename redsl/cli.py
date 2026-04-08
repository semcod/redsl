"""Command-line interface for reDSL."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Suppress litellm stderr noise before it is imported anywhere
os.environ.setdefault("LITELLM_LOG", "ERROR")

from dotenv import load_dotenv
load_dotenv()

import click

from .orchestrator import RefactorOrchestrator
from .config import AgentConfig
from .dsl import RefactorAction
from .analyzers import CodeAnalyzer
from .commands import batch as batch_commands
from .commands import hybrid as hybrid_commands
from .commands import pyqual as pyqual_commands
from .commands import scan as scan_commands
from .execution import estimate_cycle_cost
from .formatters import (
    format_refactor_plan,
    format_batch_results,
    format_debug_info,
    format_plan_yaml,
    format_cycle_report_yaml,
    _serialize_analysis,
    _serialize_decision,
    _get_timestamp,
)

logger = logging.getLogger(__name__)

_LOG_DIR = Path("logs")


def _setup_logging(project_path: Path, verbose: bool = False) -> Path:
    """Route all logging to a timestamped log file, keep stdout clean."""
    log_dir = project_path / _LOG_DIR if project_path.is_dir() else _LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"redsl_{datetime.now():%Y%m%d_%H%M%S}.log"

    root = logging.getLogger()
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    # Remove any pre-existing handlers (e.g. basicConfig defaults)
    root.handlers.clear()

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG if verbose else logging.INFO)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    root.addHandler(fh)

    # Minimal stderr handler for warnings/errors only
    sh = logging.StreamHandler(sys.stderr)
    sh.setLevel(logging.WARNING)
    sh.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    root.addHandler(sh)

    # Silence litellm's own stderr handler — it logs INFO to stderr directly
    for name in ("LiteLLM", "litellm", "httpx", "httpcore"):
        lib_logger = logging.getLogger(name)
        lib_logger.handlers.clear()
        lib_logger.addHandler(fh)
        lib_logger.propagate = False

    # Suppress litellm's verbose / coloredlogs output that bypasses logging
    try:
        import litellm
        litellm.suppress_debug_info = True
        litellm.set_verbose = False
    except ImportError:
        pass

    return log_file


@click.group()
@click.version_option(version="1.2.0")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """reDSL - Automated code refactoring tool."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


def _build_awareness_manager():
    """Build a lightweight awareness manager using the current environment config."""
    from .awareness import AwarenessManager
    from .memory import AgentMemory

    config = AgentConfig.from_env()
    return AwarenessManager(
        memory=AgentMemory(config.memory.persist_dir),
        analyzer=CodeAnalyzer(),
        default_depth=20,
    )


def _echo_json(payload: Any) -> None:
    click.echo(json.dumps(payload, indent=2, default=str))


# ---------------------------------------------------------------------------
# Awareness commands (delegated to commands/cli_awareness.py)
# ---------------------------------------------------------------------------

from .commands.cli_awareness import register as _register_awareness
_register_awareness(cli, sys.modules[__name__])


@cli.command("scan")
@click.argument("folder", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--output", "-o", "output_path", type=click.Path(path_type=Path), default=None, help="Save markdown report to file (default: <folder>/redsl_scan_report.md)")
@click.option("--quiet", "-q", is_flag=True, default=False, help="Suppress progress output")
@click.pass_context
def scan(ctx: click.Context, folder: Path, output_path: Path | None, quiet: bool) -> None:
    """Scan a folder of projects and produce a markdown priority report."""
    _setup_logging(folder, ctx.obj.get("verbose", False))
    click.echo(f"\nScanning projects in: {folder}")
    click.echo("─" * 60)
    results = scan_commands.scan_folder(folder, progress=not quiet)
    report_md = scan_commands.render_markdown(results, folder)

    if output_path is None:
        output_path = folder / "redsl_scan_report.md"
    output_path.write_text(report_md, encoding="utf-8")

    ok = sum(1 for r in results if r.is_ok())
    from .commands.scan import _TIER_CRITICAL, _TIER_HIGH, _TIER_MEDIUM, _TIER_LOW
    tier_counts = {t: sum(1 for r in results if r.tier == t) for t in [_TIER_CRITICAL, _TIER_HIGH, _TIER_MEDIUM, _TIER_LOW]}
    click.echo("─" * 60)
    click.echo(f"\nProjects analysed: {ok}/{len(results)}")
    click.echo(f"  🔴 Critical: {tier_counts[_TIER_CRITICAL]}  🟠 High: {tier_counts[_TIER_HIGH]}  🟡 Medium: {tier_counts[_TIER_MEDIUM]}  🟢 Low: {tier_counts[_TIER_LOW]}")
    click.echo(f"\n📄 Report saved to: {output_path}")


def _build_refactor_config(dry_run: bool) -> AgentConfig:
    config = AgentConfig.from_env()
    if dry_run:
        config.refactor.dry_run = True
        config.refactor.reflection_rounds = 0
    else:
        config.refactor.dry_run = False
    return config


def _collect_refactor_analysis_and_decisions(
    orchestrator: RefactorOrchestrator,
    project_path: Path,
    max_actions: int,
) -> tuple[Any, list[Any]]:
    analysis = orchestrator.analyzer.analyze_project(project_path)
    contexts = analysis.to_dsl_contexts()
    decisions = orchestrator.dsl_engine.evaluate(contexts)
    decisions = sorted(decisions, key=lambda d: d.score, reverse=True)[:max_actions]
    return analysis, decisions


def _emit_refactor_dry_run(format: str, decisions: list[Any], analysis: Any) -> None:
    if format == "yaml":
        click.echo(format_plan_yaml(decisions, analysis))
    else:
        click.echo(format_refactor_plan(decisions, format, analysis))


def _build_refactor_report_payload(report: Any, decisions: list[Any], analysis: Any) -> dict[str, Any]:
    return {
        "redsl_report": {
            "timestamp": _get_timestamp(),
            "cycle": report.cycle_number,
            "analysis": _serialize_analysis(analysis),
            "decisions": [_serialize_decision(d) for d in decisions],
            "execution": {
                "proposals_generated": report.proposals_generated,
                "proposals_applied": report.proposals_applied,
                "proposals_rejected": report.proposals_rejected,
            },
            "errors": report.errors,
        }
    }


def _emit_refactor_text_summary(report: Any) -> None:
    click.echo(f"\n=== RESULTS ===", err=True)
    click.echo(f"Cycle {report.cycle_number} complete", err=True)
    click.echo(f"Analysis: {report.analysis_summary}", err=True)
    click.echo(f"Decisions: {report.decisions_count}", err=True)
    click.echo(f"Proposals generated: {report.proposals_generated}", err=True)
    click.echo(f"Applied: {report.proposals_applied}", err=True)
    click.echo(f"Rejected: {report.proposals_rejected}", err=True)
    if report.errors:
        click.echo(f"\nErrors:", err=True)
        for error in report.errors[:5]:
            click.echo(f"  - {error}", err=True)


def _emit_refactor_live_output(
    report: Any,
    decisions: list[Any],
    analysis: Any,
    format: str,
) -> None:
    if format == "yaml":
        click.echo(format_cycle_report_yaml(report, decisions, analysis))
    elif format == "json":
        click.echo(json.dumps(_build_refactor_report_payload(report, decisions, analysis), indent=2, default=str))
    else:
        _emit_refactor_text_summary(report)
        click.echo(format_cycle_report_yaml(report, decisions, analysis))


def _prepare_refactor_application(
    format: str,
    sandbox: bool,
    decisions: list[Any],
    analysis: Any,
) -> bool:
    if format == "text":
        click.echo(format_refactor_plan(decisions, "text", analysis), err=True)
        if not click.confirm("\nApply these changes?", err=True):
            return False
        click.echo("\n=== APPLYING REFACTORING ===", err=True)

    if sandbox:
        click.echo("Sandbox mode: each refactoring will be tested in Docker before applying.", err=True)

    return True


@cli.command()
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.option("--max-actions", "-n", default=10, help="Maximum number of actions to apply")
@click.option("--dry-run", is_flag=True, help="Show what would be done without applying changes")
@click.option("--format", "-f", default="yaml", type=click.Choice(["text", "yaml", "json"]), help="Output format")
@click.option("--use-code2llm", is_flag=True, help="Use code2llm for PERCEIVE step (multi-language, call graph)")
@click.option("--validate-regix", is_flag=True, help="Validate with regix after execution (regression detection)")
@click.option("--rollback", is_flag=True, help="Auto-rollback changes if regix detects regression (requires --validate-regix)")
@click.option("--sandbox", is_flag=True, help="Test each refactoring in a Docker sandbox before applying (requires Docker)")
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
    log_file = _setup_logging(project_path, verbose)
    logger.info("reDSL refactor started: %s (max_actions=%d, dry_run=%s)", project_path, max_actions, dry_run)

    if format == "text":
        click.echo(f"Running reDSL on {project_path}", err=True)
        click.echo(f"Log file: {log_file}", err=True)

    config = _build_refactor_config(dry_run)

    orchestrator = RefactorOrchestrator(config)

    analysis, decisions = _collect_refactor_analysis_and_decisions(orchestrator, project_path, max_actions)

    if dry_run:
        _emit_refactor_dry_run(format, decisions, analysis)
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

    logger.info("reDSL refactor complete. Log: %s", log_file)
    click.echo(f"# log: {log_file}", err=True)


@cli.group()
def batch() -> None:
    """Batch refactoring commands."""


@batch.command("semcod")
@click.argument("semcod_root", type=click.Path(exists=True, path_type=Path))
@click.option("--max-actions", "-n", default=10, help="Maximum actions per project")
@click.option("--format", "-f", default="text", type=click.Choice(["text", "yaml", "json"]), help="Output format")
def batch_semcod(semcod_root: Path, max_actions: int, format: str) -> None:
    """Apply refactoring to semcod projects."""
    if format == "text":
        click.echo(f"Batch processing semcod projects in {semcod_root}")
    results = batch_commands.run_semcod_batch(semcod_root, max_actions)
    
    # Convert results to format expected by formatter
    formatted_results = []
    for detail in results.get("project_details", []):
        formatted_results.append({
            "project_name": detail["name"],
            "status": "success",
            "files_processed": detail.get("files", 0),
            "changes_applied": detail["applied"],
            "todo_reduction": detail.get("todo_reduction", 0)
        })
    
    # Format and output results
    formatted_output = format_batch_results(formatted_results, format)
    click.echo(formatted_output)


@batch.command("hybrid")
@click.argument("semcod_root", type=click.Path(exists=True, path_type=Path))
@click.option("--max-changes", "-n", default=30, help="Maximum changes per project")
def batch_hybrid(semcod_root: Path, max_changes: int) -> None:
    """Apply hybrid quality refactorings (no LLM needed)."""
    hybrid_commands.run_hybrid_batch(semcod_root, max_changes)


@cli.group()
def pyqual() -> None:
    """Python code quality analysis commands."""


@pyqual.command("analyze")
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.option("--config", "-c", type=click.Path(exists=True, path_type=Path), help="Path to pyqual.yaml config")
@click.option("--format", "-f", default="yaml", type=click.Choice(["yaml", "json"]), help="Output format")
def pyqual_analyze(project_path: Path, config: Path, format: str) -> None:
    """Analyze Python code quality."""
    pyqual_commands.run_pyqual_analysis(project_path, config, format)


@pyqual.command("fix")
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.option("--config", "-c", type=click.Path(exists=True, path_type=Path), help="Path to pyqual.yaml config")
def pyqual_fix(project_path: Path, config: Path) -> None:
    """Apply automatic quality fixes."""
    pyqual_commands.run_pyqual_fix(project_path, config)


@cli.group()
def debug() -> None:
    """Debug and diagnostic commands."""


@debug.command("config")
@click.option("--show-env", is_flag=True, help="Show environment variables")
def debug_config(show_env: bool) -> None:
    """Debug configuration loading."""
    config = AgentConfig.from_env()
    
    click.echo("=== reDSL Configuration ===")
    click.echo(f"LLM Model: {config.llm.model}")
    click.echo(f"Temperature: {config.llm.temperature}")
    click.echo(f"Max Tokens: {config.llm.max_tokens}")
    click.echo(f"Reflection Model: {config.llm.reflection_model}")
    click.echo(f"Provider Key: {'***' + config.llm.provider_key[-4:] if config.llm.provider_key else 'Not set'}")
    
    if show_env:
        import os
        click.echo("\n=== Environment Variables ===")
        for key in ["OPENAI_API_KEY", "OPENROUTER_API_KEY", "LLM_MODEL", "REFACTOR_LLM_MODEL"]:
            value = os.getenv(key)
            click.echo(f"{key}: {'***' + value[-4:] if value and 'KEY' in key else value or 'Not set'}")


@debug.command("decisions")
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.option("--limit", "-n", default=20, help="Number of decisions to show")
def debug_decisions(project_path: Path, limit: int) -> None:
    """Debug DSL decision making."""
    analyzer = CodeAnalyzer()
    analysis = analyzer.analyze_project(project_path)
    contexts = analysis.to_dsl_contexts()
    
    orchestrator = RefactorOrchestrator(AgentConfig())
    decisions = orchestrator.dsl_engine.evaluate(contexts)
    
    click.echo(f"=== DSL Decisions for {project_path.name} ===")
    click.echo(f"Total decisions: {len(decisions)}")
    click.echo()
    
    for i, decision in enumerate(decisions[:limit]):
        click.echo(f"{i+1}. {decision.action.value} on {decision.target_file}")
        click.echo(f"   Score: {decision.score:.2f}")
        click.echo(f"   Rule: {decision.rule_name}")
        click.echo(f"   Rationale: {decision.rationale}")
        click.echo()


@cli.command()
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.pass_context
def perf(ctx: click.Context, project_path: Path) -> None:
    """Profile a refactoring cycle and report performance bottlenecks."""
    _setup_logging(project_path, ctx.obj.get("verbose", False))
    from redsl.diagnostics.perf_bridge import generate_optimization_report
    click.echo(generate_optimization_report(project_path))


@cli.command()
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.option("--max-actions", "-n", default=10, help="Number of actions to estimate")
@click.pass_context
def cost(ctx: click.Context, project_path: Path, max_actions: int) -> None:
    """Estimate LLM cost for the next refactoring cycle without running it."""
    _setup_logging(project_path, ctx.obj.get("verbose", False))
    config = AgentConfig.from_env()
    orchestrator = RefactorOrchestrator(config)
    items = estimate_cycle_cost(orchestrator, project_path, max_actions=max_actions)

    click.echo(f"Planned refactoring cost estimate ({len(items)} actions):")
    total = 0.0
    for i, item in enumerate(items, 1):
        cost_str = f"${item['cost_usd']:.4f}" if item["cost_usd"] > 0 else "$0.000 (direct)"
        click.echo(
            f"  [{i}] {item['action']} \u2192 {item['target_file']}\n"
            f"      Model: {item['model']} | Est. tokens: {item['tokens']} | Cost: {cost_str}"
        )
        total += item["cost_usd"]
    click.echo(f"\n  Total: ~${total:.4f} for {len(items)} actions")


# ---------------------------------------------------------------------------
# Doctor commands (delegated to commands/cli_doctor.py)
# ---------------------------------------------------------------------------

from .commands.cli_doctor import register as _register_doctor
_register_doctor(cli)


# ---------------------------------------------------------------------------
# Autonomy commands (delegated to commands/cli_autonomy.py)
# ---------------------------------------------------------------------------

from .commands.cli_autonomy import register as _register_autonomy
_register_autonomy(cli, sys.modules[__name__])


if __name__ == "__main__":
    cli()
