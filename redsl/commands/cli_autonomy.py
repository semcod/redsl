"""CLI commands for the autonomy subsystem (gate, review, intent, watch, improve, growth)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click

from redsl.cli.llm_banner import print_llm_banner


def _echo_json(payload: Any) -> None:
    click.echo(json.dumps(payload, indent=2, default=str))


def _format_gate_details(verdict: Any) -> str:
    """Format quality gate details as text."""
    lines = [
        "=== Quality Gate Details ===",
        f"Status: {'PASSED' if verdict.passed else 'FAILED'}",
        f"\nBefore: CC={verdict.metrics_before.get('cc_mean', 0):.2f}, "
        f"critical={verdict.metrics_before.get('critical', 0)}, "
        f"files={verdict.metrics_before.get('total_files', 0)}",
        f"After:  CC={verdict.metrics_after.get('cc_mean', 0):.2f}, "
        f"critical={verdict.metrics_after.get('critical', 0)}, "
        f"files={verdict.metrics_after.get('total_files', 0)}",
    ]
    if verdict.violations:
        lines.append(f"\nViolations ({len(verdict.violations)}):")
        for v in verdict.violations:
            lines.append(f"  - {v}")
    else:
        lines.append("\nNo violations.")
    return "\n".join(lines)


def _format_gate_fix_result(verdict: Any, result: Any) -> str:
    """Format gate fix result as text."""
    if verdict.passed:
        return "Quality gate already passes — nothing to fix."
    lines = [f"Found {len(verdict.violations)} violation(s), attempting auto-fix..."]
    lines.append(f"  Fixed:  {len(result.fixed)}")
    lines.append(f"  Manual: {len(result.manual_needed)}")
    for t in result.tickets_created:
        lines.append(f"  Ticket: {t['violation'][:80]} -> {t['suggested_action']}")
    return "\n".join(lines)


def _register_gate_check(gate_grp: click.Group) -> None:
    @gate_grp.command("check")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
    @click.option("--format", "-f", default="text", type=click.Choice(["text", "json"]), help="Output format")
    def gate_check(project_path: Path, format: str) -> None:
        """Run the quality gate against current changes."""
        from redsl.autonomy.quality_gate import run_quality_gate
        verdict = run_quality_gate(project_path)
        if format == "json":
            _echo_json({
                "passed": verdict.passed, "reason": verdict.reason,
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


def _register_gate_details(gate_grp: click.Group) -> None:
    @gate_grp.command("details")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
    def gate_details(project_path: Path) -> None:
        """Show detailed quality gate metrics and violations."""
        from redsl.autonomy.quality_gate import run_quality_gate
        verdict = run_quality_gate(project_path)
        click.echo(_format_gate_details(verdict))


def _register_gate_install_hook(gate_grp: click.Group) -> None:
    @gate_grp.command("install-hook")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
    def gate_install_hook(project_path: Path) -> None:
        """Install a git pre-commit hook that runs the quality gate."""
        from redsl.autonomy.quality_gate import install_pre_commit_hook
        hook = install_pre_commit_hook(project_path)
        click.echo(f"Installed pre-commit hook: {hook}")


def _register_gate_fix(gate_grp: click.Group) -> None:
    @gate_grp.command("fix")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
    def gate_fix(project_path: Path) -> None:
        """Automatically fix quality gate violations."""
        from redsl.autonomy.quality_gate import run_quality_gate
        from redsl.autonomy.auto_fix import auto_fix_violations
        verdict = run_quality_gate(project_path)
        if verdict.passed:
            click.echo("Quality gate already passes — nothing to fix.")
            return
        result = auto_fix_violations(project_path, verdict.violations)
        click.echo(_format_gate_fix_result(verdict, result))


def _register_gate_commands(cli: click.Group) -> None:
    """Register gate sub-group with check/details/install-hook/fix commands."""

    @cli.group()
    def gate() -> None:
        """Quality gate — check and enforce code quality on commits."""

    _register_gate_check(gate)
    _register_gate_details(gate)
    _register_gate_install_hook(gate)
    _register_gate_fix(gate)


def _register_review_commands(cli: click.Group, host_module: Any) -> None:
    """Register review and intent commands."""

    @cli.command("review")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
    @click.pass_context
    def review_cmd(ctx: click.Context, project_path: Path) -> None:
        """Review staged changes (like a code reviewer)."""
        host_module._setup_logging(project_path, ctx.obj.get("verbose", False))
        print_llm_banner(mode="llm")
        from redsl.autonomy.review import review_staged_changes

        output = review_staged_changes(project_path)
        click.echo(output)

    @cli.command("intent")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
    def intent_cmd(project_path: Path) -> None:
        """Classify the intent and risk of current changes."""
        from redsl.autonomy.intent import analyze_commit_intent

        report = analyze_commit_intent(project_path)
        _echo_json(report)


def _register_watch_cmd(cli: click.Group, host_module: Any) -> None:
    """Register watch command."""
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
        print_llm_banner(mode="mixed")
        from redsl.autonomy.scheduler import AutonomyMode, Scheduler

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


def _format_improve_result(result: dict) -> str:
    """Format improve cycle result as text."""
    lines = [f"Cycle {result['cycle']} [{result['mode']}]: {result['analysis_summary']}"]
    if result.get("proposals"):
        lines.append(f"  Proposals: {len(result['proposals'])}")
        for p in result["proposals"]:
            lines.append(f"    - {p['action']} -> {p['target']} (score={p['score']})")
    if result.get("applied"):
        lines.append(f"  Applied: {len(result['applied'])}")
    return "\n".join(lines)


def _register_improve_cmd(cli: click.Group, host_module: Any) -> None:
    """Register improve command."""
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
        print_llm_banner(mode="mixed")
        from redsl.autonomy.scheduler import AutonomyMode, Scheduler

        sched = Scheduler(
            project_dir=project_path,
            mode=AutonomyMode(mode),
            max_actions_per_cycle=max_actions,
        )
        result = sched.run_once()
        if format == "json":
            _echo_json(result)
        else:
            click.echo(_format_improve_result(result))


def _register_watch_commands(cli: click.Group, host_module: Any) -> None:
    """Register watch and improve commands."""
    _register_watch_cmd(cli, host_module)
    _register_improve_cmd(cli, host_module)


def _format_autonomy_status(metrics: Any) -> str:
    """Format autonomy metrics as human-readable text."""
    lines = [
        "=== ReDSL Autonomy Status ===",
        "",
        "Quality Gate:",
        f"  Installed: {'✅ Yes' if metrics.gate_installed else '❌ No'}",
    ]
    if metrics.gate_installed:
        lines.append(f"  Hook path: {metrics.gate_hook_path}")
    lines += [
        f"  Blocks last week: {metrics.gate_blocks_last_week}",
        "",
        "Growth Control:",
        f"  Within budget: {'✅ Yes' if metrics.growth_within_budget else '❌ No'}",
        f"  Budget: {metrics.growth_budget_lines} lines/week",
        f"  Last week: {metrics.growth_last_week_lines} lines",
        "",
        "Scheduler:",
        f"  Running: {'✅ Yes' if metrics.scheduler_running else '❌ No'}",
        "",
        "Self-Refactoring:",
        f"  Last month count: {metrics.self_refactor_count_last_month}",
    ]
    if metrics.last_autonomous_pr:
        lines.append(f"  Last activity: {metrics.last_autonomous_pr}")
    lines += [
        "",
        "Project Health:",
        f"  CC mean: {metrics.cc_mean:.2f}",
        f"  Critical functions: {metrics.critical_count}",
        f"  God modules (>400L): {metrics.god_modules_count}",
        "",
        f"Collected at: {metrics.collected_at}",
    ]
    return "\n".join(lines)


def _format_growth_report(warnings: list, suggestions: list) -> str:
    """Format growth check result as text."""
    lines = []
    if warnings:
        lines.append(f"Growth warnings ({len(warnings)}):")
        for w in warnings:
            lines.append(f"  - {w}")
    else:
        lines.append("Growth: within budget.")
    if suggestions:
        lines.append(f"\nConsolidation suggestions ({len(suggestions)}):")
        for s in suggestions:
            lines.append(f"  - {s['action']}: {s['description']}")
    return "\n".join(lines)


def _register_growth_cmd(cli: click.Group) -> None:
    """Register growth command."""
    @cli.command("growth")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
    @click.option("--format", "-f", default="text", type=click.Choice(["text", "json"]), help="Output format")
    def growth_cmd(project_path: Path, format: str) -> None:
        """Check growth budget and suggest consolidation."""
        from redsl.autonomy.growth_control import GrowthController
        gc = GrowthController()
        warnings = gc.check_growth(project_path)
        suggestions = gc.suggest_consolidation(project_path)
        if format == "json":
            _echo_json({"warnings": warnings, "suggestions": suggestions})
        else:
            click.echo(_format_growth_report(warnings, suggestions))


def _register_autonomy_status_cmd(cli: click.Group) -> None:
    """Register autonomy-status command."""
    @cli.command("autonomy-status")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
    @click.option("--format", "-f", default="text", type=click.Choice(["text", "json"]), help="Output format")
    def autonomy_status_cmd(project_path: Path, format: str) -> None:
        """Check autonomy system status and metrics."""
        from redsl.autonomy.metrics import collect_autonomy_metrics
        metrics = collect_autonomy_metrics(project_path)
        if format == "json":
            _echo_json(metrics.to_dict())
        else:
            click.echo(_format_autonomy_status(metrics))


def _register_growth_and_status_commands(cli: click.Group) -> None:
    """Register growth and autonomy-status commands."""
    _register_growth_cmd(cli)
    _register_autonomy_status_cmd(cli)


def _register_pr_commands(cli: click.Group) -> None:
    """Register autonomous-pr command."""

    @cli.command("autonomous-pr")
    @click.argument("git_url", type=str)
    @click.option("--max-actions", "-n", default=3, help="Maximum refactoring actions to apply")
    @click.option("--dry-run", is_flag=True, help="Analyze only without creating PR")
    @click.option("--auto-apply", is_flag=True, help="Automatically apply fixes without manual confirmation")
    @click.option("--target-file", type=str, default=None, help="Restrict refactoring to a project-relative file or path prefix")
    @click.option("--work-dir", type=click.Path(path_type=Path), default=Path("/tmp/redsl-autonomous"), help="Working directory for cloning")
    @click.option("--branch-name", default="redsl-autonomous-refactor", help="Branch name for PR")
    @click.option("--format", "-f", default="text", type=click.Choice(["text", "json"]), help="Output format")
    def autonomous_pr_cmd(git_url: str, max_actions: int, dry_run: bool, auto_apply: bool, target_file: str | None, work_dir: Path, branch_name: str, format: str) -> None:
        """Create autonomous PR for a Git repository.

        This command:
        1. Clones the repository
        2. Runs reDSL analysis
        3. Applies refactoring suggestions
        4. Creates a branch
        5. Commits changes
        6. Pushes to GitHub
        7. Creates a Pull Request

        Example:
            redsl autonomous-pr https://github.com/semcod/vallm.git
        """
        print_llm_banner(mode="plan" if dry_run else "mixed")
        from redsl.commands.autonomy_pr import run_autonomous_pr
        run_autonomous_pr(git_url, max_actions, dry_run, auto_apply, target_file, work_dir, branch_name, fmt=format)


def register(cli: click.Group, host_module: Any) -> None:
    """Register all autonomy commands on the given Click group."""
    _register_gate_commands(cli)
    _register_review_commands(cli, host_module)
    _register_watch_commands(cli, host_module)
    _register_growth_and_status_commands(cli)
    _register_pr_commands(cli)
