"""Git operations for the autonomous PR workflow."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import click

from .models import _CloneResult, _CommitResult, _PushResult


def _https_to_ssh(url: str) -> str:
    """Convert HTTPS GitHub URL to SSH if possible.

    >>> _https_to_ssh('https://github.com/semcod/vallm.git')
    'git@github.com:semcod/vallm.git'
    """
    m = re.match(r'https?://github\.com/(.+)', url)
    if m:
        return f'git@github.com:{m.group(1)}'
    return url


def _gh_available() -> bool:
    """Return True if the GitHub CLI (gh) is installed and authenticated."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True, timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _resolve_branch_name(clone_path: Path, branch_name: str) -> str:
    """Resolve unique branch name if needed."""
    existing_local = subprocess.run(
        ["git", "branch", "--list", branch_name],
        cwd=str(clone_path),
        capture_output=True,
        text=True,
    )
    existing_remote = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", branch_name],
        cwd=str(clone_path),
        capture_output=True,
        text=True,
    )
    if existing_local.stdout.strip() or existing_remote.stdout.strip():
        return f"{branch_name}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    return branch_name


def _step_clone(git_url: str, clone_url: str, work_dir: Path) -> _CloneResult:
    """Clone repository to working directory."""
    repo_name = git_url.rstrip('/').split('/')[-1].replace('.git', '')
    clone_path = work_dir / repo_name

    if clone_path.exists():
        click.echo(f"  Repository already cloned at {clone_path}; refreshing workspace")
        shutil.rmtree(clone_path)

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", clone_url, str(clone_path)],
            check=True,
            capture_output=True,
            timeout=60
        )
        click.echo(f"  ✓ Cloned to {clone_path}")
    except subprocess.CalledProcessError as e:
        return _CloneResult(None, f"Failed to clone: {e.stderr.decode()}")
    except subprocess.TimeoutExpired:
        return _CloneResult(None, "Clone timed out")

    redsl_dir = clone_path / ".redsl"
    if redsl_dir.exists():
        shutil.rmtree(redsl_dir)
        click.echo(f"  ✓ Cleared stale .redsl/ history")

    return _CloneResult(clone_path)


def _step_branch_and_commit(
    clone_path: Path,
    branch_name: str,
    real_changes: list[str],
    max_actions: int,
) -> _CommitResult:
    """Create branch and commit changes."""
    resolved_branch_name = _resolve_branch_name(clone_path, branch_name)

    click.echo(f"\nStep 4: Creating branch {resolved_branch_name}...")
    try:
        subprocess.run(
            ["git", "checkout", "-b", resolved_branch_name],
            cwd=str(clone_path),
            check=True,
            capture_output=True
        )
        click.echo(f"  ✓ Branch created")
    except subprocess.CalledProcessError as e:
        return _CommitResult(resolved_branch_name, False, f"Failed to create branch: {e.stderr.decode()}")

    try:
        subprocess.run(
            ["git", "add", "--", *real_changes],
            cwd=str(clone_path),
            check=True,
            capture_output=True,
        )
        click.echo(f"  ✓ Staged {len(real_changes)} source file(s)")

        click.echo(f"\nStep 5: Committing changes...")
        commit_msg = f"Autonomous refactoring by ReDSL\n\nApplied {max_actions} top refactoring suggestions automatically."
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=str(clone_path),
            check=True,
            capture_output=True
        )
        click.echo(f"  ✓ Changes committed")
    except subprocess.CalledProcessError as e:
        return _CommitResult(resolved_branch_name, False, f"Failed to commit: {e.stderr.decode()}")

    return _CommitResult(resolved_branch_name, True)


def _step_push(clone_path: Path, resolved_branch_name: str, use_gh: bool) -> _PushResult:
    """Push branch to GitHub."""
    click.echo(f"\nStep 6: Pushing to GitHub...")
    try:
        push_cmd = ["git", "push", "-u", "origin", resolved_branch_name]
        env = None
        if not use_gh:
            env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        subprocess.run(
            push_cmd,
            cwd=str(clone_path),
            check=True,
            capture_output=True,
            timeout=120,
            env=env,
        )
        click.echo(f"  ✓ Pushed successfully")
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode() if e.stderr else ""
        return _PushResult(False, f"Failed to push: {stderr}")
    except subprocess.TimeoutExpired:
        return _PushResult(False, "Push timed out")

    return _PushResult(True)


def _step_create_pr(
    clone_path: Path,
    resolved_branch_name: str,
    use_gh: bool,
    real_changes: list[str],
    max_actions: int,
    clone_url: str,
) -> bool:
    """Create Pull Request using gh CLI. Returns True if PR created or skipped gracefully."""
    click.echo(f"\nStep 7: Creating Pull Request...")
    if not use_gh:
        click.echo("  ⚠ GitHub CLI (gh) not available — skipping PR creation")
        click.echo(f"  Push succeeded. Create PR manually for branch: {resolved_branch_name}")
        return True

    pr_title = "Autonomous refactoring by ReDSL"
    changes_list = "\n".join(f"- `{p}`" for p in real_changes)
    pr_body = (
        f"## Summary\n\nAutonomous refactoring by ReDSL.\n\n"
        f"## Changes ({len(real_changes)} file(s))\n\n{changes_list}\n\n"
        f"## Pipeline\n\n| Step | Status |\n|------|--------|\n"
        f"| Clone (SSH) | ✅ |\n| Analysis | ✅ {max_actions} actions |\n"
        f"| Apply | ✅ |\n| Push | ✅ |\n| PR | ✅ |\n\n"
        "---\n*Generated by reDSL autonomous-pr*\n"
    )
    try:
        subprocess.run(
            ["gh", "pr", "create", "--title", pr_title, "--body", pr_body,
             "--head", resolved_branch_name],
            cwd=str(clone_path),
            check=True,
            capture_output=True,
            timeout=30,
        )
        click.echo(f"  ✓ PR created successfully")
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode() if e.stderr else ""
        click.echo(f"  ✗ Failed to create PR: {stderr}")
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        click.echo(f"  ✗ gh CLI error: {e}")
        return False

    return True
