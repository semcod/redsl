"""CLI commands for the autonomy subsystem (gate, review, intent, watch, improve, growth)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click


def _echo_json(payload: Any) -> None:
    click.echo(json.dumps(payload, indent=2, default=str))


def register(cli: click.Group, host_module) -> None:
    """Register all autonomy commands on the given Click group."""

    # -----------------------------------------------------------------------
    # gate group
    # -----------------------------------------------------------------------

    @cli.group()
    def gate() -> None:
        """Quality gate — check and enforce code quality on commits."""

    @gate.command("check")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
    @click.option("--format", "-f", default="text", type=click.Choice(["text", "json"]), help="Output format")
    def gate_check(project_path: Path, format: str) -> None:
        """Run the quality gate against current changes."""
        from ..autonomy.quality_gate import run_quality_gate

        verdict = run_quality_gate(project_path)
        if format == "json":
            _echo_json({
                "passed": verdict.passed,
                "reason": verdict.reason,
                "violations": verdict.violations,
                "metrics_before": verdict.metrics_before,
                "metrics_after": verdict.metrics_after,
            })
        else:
            if verdict.passed:
                click.echo(f"Quality gate PASSED (CC={verdict.metrics_after['cc_mean']:.2f})")
            else:
                click.echo(f"Quality gate FAILED — {verdict.reason}")
                for v in verdict.violations:
                    click.echo(f"  - {v}")

    @gate.command("details")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
    def gate_details(project_path: Path) -> None:
        """Show detailed quality gate metrics and violations."""
        from ..autonomy.quality_gate import run_quality_gate

        verdict = run_quality_gate(project_path)
        click.echo("=== Quality Gate Details ===")
        click.echo(f"Status: {'PASSED' if verdict.passed else 'FAILED'}")
        click.echo(f"\nBefore: CC={verdict.metrics_before.get('cc_mean', 0):.2f}, "
                   f"critical={verdict.metrics_before.get('critical', 0)}, "
                   f"files={verdict.metrics_before.get('total_files', 0)}")
        click.echo(f"After:  CC={verdict.metrics_after.get('cc_mean', 0):.2f}, "
                   f"critical={verdict.metrics_after.get('critical', 0)}, "
                   f"files={verdict.metrics_after.get('total_files', 0)}")
        if verdict.violations:
            click.echo(f"\nViolations ({len(verdict.violations)}):")
            for v in verdict.violations:
                click.echo(f"  - {v}")
        else:
            click.echo("\nNo violations.")

    @gate.command("install-hook")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
    def gate_install_hook(project_path: Path) -> None:
        """Install a git pre-commit hook that runs the quality gate."""
        from ..autonomy.quality_gate import install_pre_commit_hook

        hook = install_pre_commit_hook(project_path)
        click.echo(f"Installed pre-commit hook: {hook}")

    @gate.command("fix")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
    def gate_fix(project_path: Path) -> None:
        """Automatically fix quality gate violations."""
        from ..autonomy.quality_gate import run_quality_gate
        from ..autonomy.auto_fix import auto_fix_violations

        verdict = run_quality_gate(project_path)
        if verdict.passed:
            click.echo("Quality gate already passes — nothing to fix.")
            return

        click.echo(f"Found {len(verdict.violations)} violation(s), attempting auto-fix...")
        result = auto_fix_violations(project_path, verdict.violations)
        click.echo(f"  Fixed:  {len(result.fixed)}")
        click.echo(f"  Manual: {len(result.manual_needed)}")
        for t in result.tickets_created:
            click.echo(f"  Ticket: {t['violation'][:80]} -> {t['suggested_action']}")

    # -----------------------------------------------------------------------
    # Standalone commands
    # -----------------------------------------------------------------------

    @cli.command("review")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
    @click.pass_context
    def review_cmd(ctx: click.Context, project_path: Path) -> None:
        """Review staged changes (like a code reviewer)."""
        host_module._setup_logging(project_path, ctx.obj.get("verbose", False))
        from ..autonomy.review import review_staged_changes

        output = review_staged_changes(project_path)
        click.echo(output)

    @cli.command("intent")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
    def intent_cmd(project_path: Path) -> None:
        """Classify the intent and risk of current changes."""
        from ..autonomy.intent import analyze_commit_intent

        report = analyze_commit_intent(project_path)
        _echo_json(report)

    @cli.command("watch")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
    @click.option("--mode", "-m", default="suggest",
                  type=click.Choice(["watch", "suggest", "autonomous"]),
                  help="Scheduler mode")
    @click.option("--interval", "-i", default=30, help="Check interval in minutes")
    @click.option("--max-actions", "-n", default=3, help="Max actions per cycle")
    @click.pass_context
    def watch_cmd(ctx: click.Context, project_path: Path, mode: str, interval: int, max_actions: int) -> None:
        """Start the periodic self-improvement scheduler."""
        import asyncio
        host_module._setup_logging(project_path, ctx.obj.get("verbose", False))
        from ..autonomy.scheduler import AutonomyMode, Scheduler

        sched = Scheduler(
            project_dir=project_path,
            mode=AutonomyMode(mode),
            check_interval_minutes=interval,
            max_actions_per_cycle=max_actions,
        )
        click.echo(f"Starting scheduler: mode={mode}, interval={interval}min, max_actions={max_actions}")
        click.echo("Press Ctrl+C to stop.")
        try:
            asyncio.run(sched.run())
        except KeyboardInterrupt:
            sched.stop()
            click.echo("\nScheduler stopped.")

    @cli.command("improve")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
    @click.option("--mode", "-m", default="suggest",
                  type=click.Choice(["watch", "suggest", "autonomous"]),
                  help="Execution mode")
    @click.option("--max-actions", "-n", default=3, help="Max actions")
    @click.option("--format", "-f", default="json", type=click.Choice(["text", "json"]), help="Output format")
    @click.pass_context
    def improve_cmd(ctx: click.Context, project_path: Path, mode: str, max_actions: int, format: str) -> None:
        """Run a single self-improvement cycle."""
        host_module._setup_logging(project_path, ctx.obj.get("verbose", False))
        from ..autonomy.scheduler import AutonomyMode, Scheduler

        sched = Scheduler(
            project_dir=project_path,
            mode=AutonomyMode(mode),
            max_actions_per_cycle=max_actions,
        )
        result = sched.run_once()
        if format == "json":
            _echo_json(result)
        else:
            click.echo(f"Cycle {result['cycle']} [{result['mode']}]: {result['analysis_summary']}")
            if result.get("proposals"):
                click.echo(f"  Proposals: {len(result['proposals'])}")
                for p in result["proposals"]:
                    click.echo(f"    - {p['action']} -> {p['target']} (score={p['score']})")
            if result.get("applied"):
                click.echo(f"  Applied: {len(result['applied'])}")

    @cli.command("growth")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
    @click.option("--format", "-f", default="text", type=click.Choice(["text", "json"]), help="Output format")
    def growth_cmd(project_path: Path, format: str) -> None:
        """Check growth budget and suggest consolidation."""
        from ..autonomy.growth_control import GrowthController

        gc = GrowthController()
        warnings = gc.check_growth(project_path)
        suggestions = gc.suggest_consolidation(project_path)

        if format == "json":
            _echo_json({"warnings": warnings, "suggestions": suggestions})
        else:
            if warnings:
                click.echo(f"Growth warnings ({len(warnings)}):")
                for w in warnings:
                    click.echo(f"  - {w}")
            else:
                click.echo("Growth: within budget.")
            if suggestions:
                click.echo(f"\nConsolidation suggestions ({len(suggestions)}):")
                for s in suggestions:
                    click.echo(f"  - {s['action']}: {s['description']}")
