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

    @cli.command("autonomy-status")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
    @click.option("--format", "-f", default="text", type=click.Choice(["text", "json"]), help="Output format")
    def autonomy_status_cmd(project_path: Path, format: str) -> None:
        """Check autonomy system status and metrics."""
        from ..autonomy.metrics import collect_autonomy_metrics

        metrics = collect_autonomy_metrics(project_path)

        if format == "json":
            _echo_json(metrics.to_dict())
        else:
            click.echo("=== ReDSL Autonomy Status ===")
            click.echo("")
            click.echo("Quality Gate:")
            click.echo(f"  Installed: {'✅ Yes' if metrics.gate_installed else '❌ No'}")
            if metrics.gate_installed:
                click.echo(f"  Hook path: {metrics.gate_hook_path}")
            click.echo(f"  Blocks last week: {metrics.gate_blocks_last_week}")
            click.echo("")
            click.echo("Growth Control:")
            click.echo(f"  Within budget: {'✅ Yes' if metrics.growth_within_budget else '❌ No'}")
            click.echo(f"  Budget: {metrics.growth_budget_lines} lines/week")
            click.echo(f"  Last week: {metrics.growth_last_week_lines} lines")
            click.echo("")
            click.echo("Scheduler:")
            click.echo(f"  Running: {'✅ Yes' if metrics.scheduler_running else '❌ No'}")
            click.echo("")
            click.echo("Self-Refactoring:")
            click.echo(f"  Last month count: {metrics.self_refactor_count_last_month}")
            if metrics.last_autonomous_pr:
                click.echo(f"  Last activity: {metrics.last_autonomous_pr}")
            click.echo("")
            click.echo("Project Health:")
            click.echo(f"  CC mean: {metrics.cc_mean:.2f}")
            click.echo(f"  Critical functions: {metrics.critical_count}")
            click.echo(f"  God modules (>400L): {metrics.god_modules_count}")
            click.echo("")
            click.echo(f"Collected at: {metrics.collected_at}")

    @cli.command("autonomous-pr")
    @click.argument("git_url", type=str)
    @click.option("--max-actions", "-n", default=3, help="Maximum refactoring actions to apply")
    @click.option("--dry-run", is_flag=True, help="Analyze only without creating PR")
    @click.option("--work-dir", type=click.Path(path_type=Path), default=Path("/tmp/redsl-autonomous"), help="Working directory for cloning")
    @click.option("--branch-name", default="redsl-autonomous-refactor", help="Branch name for PR")
    def autonomous_pr_cmd(git_url: str, max_actions: int, dry_run: bool, work_dir: Path, branch_name: str) -> None:
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
        import subprocess
        import tempfile
        from datetime import datetime

        click.echo(f"=== Autonomous PR Workflow ===")
        click.echo(f"Target: {git_url}")
        click.echo(f"Max actions: {max_actions}")
        click.echo(f"Branch: {branch_name}")
        click.echo("")

        # Step 1: Clone repository
        click.echo("Step 1: Cloning repository...")
        work_dir.mkdir(parents=True, exist_ok=True)

        # Extract repo name from URL
        repo_name = git_url.rstrip('/').split('/')[-1].replace('.git', '')
        clone_path = work_dir / repo_name

        if clone_path.exists():
            click.echo(f"  Repository already cloned at {clone_path}")
        else:
            try:
                subprocess.run(
                    ["git", "clone", git_url, str(clone_path)],
                    check=True,
                    capture_output=True,
                    timeout=60
                )
                click.echo(f"  ✓ Cloned to {clone_path}")
            except subprocess.CalledProcessError as e:
                click.echo(f"  ✗ Failed to clone: {e.stderr.decode()}")
                return
            except subprocess.TimeoutExpired:
                click.echo(f"  ✗ Clone timed out")
                return

        # Step 2: Run reDSL analysis
        click.echo(f"\nStep 2: Running reDSL analysis...")
        click.echo(f"  Analyzing {max_actions} top issues...")

        try:
            result = subprocess.run(
                ["/usr/bin/python3", "-m", "redsl.cli", "refactor", str(clone_path),
                 "--max-actions", str(max_actions), "--dry-run", "--format", "text"],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                click.echo(f"  ✗ Analysis failed: {result.stderr}")
                return

            click.echo(f"  ✓ Analysis complete")
            click.echo(f"\n  Suggestions:")
            for line in result.stdout.split('\n'):
                if line.strip().startswith(str(1) + '.') or line.strip().startswith(str(2) + '.') or line.strip().startswith(str(3) + '.'):
                    click.echo(f"    {line}")

        except subprocess.TimeoutExpired:
            click.echo(f"  ✗ Analysis timed out")
            return
        except Exception as e:
            click.echo(f"  ✗ Analysis error: {e}")
            return

        if dry_run:
            click.echo("\nDry run complete - no PR created")
            return

        # Step 3: Create branch
        click.echo(f"\nStep 3: Creating branch {branch_name}...")
        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=str(clone_path),
                check=True,
                capture_output=True
            )
            click.echo(f"  ✓ Branch created")
        except subprocess.CalledProcessError as e:
            click.echo(f"  ✗ Failed to create branch: {e.stderr.decode()}")
            return

        # Step 4: Apply fixes (manual for now - in future this would be automated)
        click.echo(f"\nStep 4: Applying fixes...")
        click.echo(f"  ⚠ Manual step: Please apply the suggested refactoring from the analysis above")
        click.echo(f"  Then press Enter to continue, or Ctrl+C to abort...")

        try:
            input()
        except KeyboardInterrupt:
            click.echo(f"\n  Aborted by user")
            return

        # Step 5: Commit changes
        click.echo(f"\nStep 5: Committing changes...")
        try:
            # Check for changes
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(clone_path),
                capture_output=True,
                text=True
            )

            if not status.stdout.strip():
                click.echo(f"  No changes to commit")
                return

            subprocess.run(
                ["git", "add", "."],
                cwd=str(clone_path),
                check=True,
                capture_output=True
            )

            commit_msg = f"Autonomous refactoring by ReDSL\n\nApplied {max_actions} top refactoring suggestions automatically."
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=str(clone_path),
                check=True,
                capture_output=True
            )
            click.echo(f"  ✓ Changes committed")
        except subprocess.CalledProcessError as e:
            click.echo(f"  ✗ Failed to commit: {e.stderr.decode()}")
            return

        # Step 6: Push to GitHub
        click.echo(f"\nStep 6: Pushing to GitHub...")
        try:
            subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=str(clone_path),
                check=True,
                capture_output=True
            )
            click.echo(f"  ✓ Pushed successfully")
        except subprocess.CalledProcessError as e:
            click.echo(f"  ✗ Failed to push: {e.stderr.decode()}")
            return

        # Step 7: Create PR using gh CLI
        click.echo(f"\nStep 7: Creating Pull Request...")
        try:
            pr_title = f"Autonomous refactoring by ReDSL"
            pr_body = f"""## Summary

This PR applies autonomous refactoring suggested by ReDSL.

## Analysis

ReDSL analyzed the repository and identified {max_actions} top refactoring opportunities.

## Changes

Applied the following refactoring suggestions:
- See the reDSL analysis output above for details

## Autonomy

This PR was created automatically by the ReDSL autonomous PR workflow:
1. Cloned repository
2. Ran reDSL analysis
3. Applied refactoring suggestions
4. Committed changes
5. Pushed to GitHub
6. Created this PR

---
*Generated by reDSL autonomous-pr command*
"""

            subprocess.run(
                ["gh", "pr", "create", "--title", pr_title, "--body", pr_body],
                cwd=str(clone_path),
                check=True,
                capture_output=True
            )
            click.echo(f"  ✓ PR created successfully")
        except subprocess.CalledProcessError as e:
            click.echo(f"  ✗ Failed to create PR: {e.stderr.decode()}")
            return

        click.echo(f"\n=== Autonomous PR Workflow Complete ===")
        click.echo(f"Repository: {git_url}")
        click.echo(f"Branch: {branch_name}")
        click.echo(f"PR created successfully!")
