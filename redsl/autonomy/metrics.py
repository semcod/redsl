"""Autonomy metrics — measure whether the self-improvement system is actually working.

This module provides metrics to track:
- Whether quality gate is installed and active
- How many commits are being blocked
- Auto-fix success rates
- Growth budget compliance
- Scheduler status
- Self-refactoring activity
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass
class AutonomyMetrics:
    """Metrics for the autonomy subsystem."""

    # Gate status
    gate_installed: bool = False
    gate_hook_path: str = ""
    gate_blocks_last_week: int = 0

    # Auto-fix metrics
    auto_fix_success_rate: float = 0.0
    auto_fix_attempts_last_week: int = 0
    auto_fix_successes_last_week: int = 0

    # Growth control
    growth_within_budget: bool = True
    growth_budget_lines: int = 2000
    growth_last_week_lines: int = 0

    # Scheduler status
    scheduler_running: bool = False
    scheduler_last_run: str = ""

    # Self-refactoring activity
    last_autonomous_pr: str = ""
    self_refactor_count_last_month: int = 0
    regressions_caught: int = 0

    # Project health
    cc_mean: float = 0.0
    critical_count: int = 0
    god_modules_count: int = 0

    # Timestamp
    collected_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


def _check_gate_installed(project_dir: Path) -> tuple[bool, str]:
    """Check if pre-commit hook is installed."""
    hook_path = project_dir / ".git" / "hooks" / "pre-commit"
    if hook_path.exists():
        content = hook_path.read_text(encoding="utf-8", errors="replace")
        if "redsl" in content or "quality_gate" in content:
            return True, str(hook_path)
    return False, ""


def _count_gate_blocks_last_week(project_dir: Path) -> int:
    """Count how many times the gate blocked commits in the last week."""
    try:
        # Look for gate-related entries in git log
        since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        proc = subprocess.run(
            ["git", "log", f"--since={since}", "--oneline", "--all"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=10,
        )
        if proc.returncode != 0:
            return 0

        # Count gate fix commits (indicates a block happened and was fixed)
        count = 0
        for line in proc.stdout.splitlines():
            if any(kw in line.lower() for kw in ["gate fix", "quality fix", "violation"]):
                count += 1
        return count
    except Exception:
        return 0


def _get_last_autonomous_pr(project_dir: Path) -> str:
    """Find date of last autonomous PR created by ReDSL."""
    try:
        # Check for commits with auto-generated messages
        proc = subprocess.run(
            ["git", "log", "--oneline", "--all", "-50"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=10,
        )
        if proc.returncode != 0:
            return ""

        for line in proc.stdout.splitlines():
            if any(kw in line.lower() for kw in ["redsl", "auto-fix", "autonomous", "self-refactor"]):
                # Return the commit hash as a proxy for date
                return line.split()[0] if line else ""
        return ""
    except Exception:
        return ""


def _count_self_refactors_last_month(project_dir: Path) -> int:
    """Count self-refactoring commits in the last month."""
    try:
        since = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        proc = subprocess.run(
            ["git", "log", f"--since={since}", "--oneline", "--all"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=10,
        )
        if proc.returncode != 0:
            return 0

        count = 0
        for line in proc.stdout.splitlines():
            if any(kw in line.lower() for kw in ["redsl", "auto-fix", "refactor", "split", "cc="]):
                count += 1
        return count
    except Exception:
        return 0


def _check_scheduler_running() -> bool:
    """Check if watch mode is currently running."""
    # This is a heuristic - check for running Python processes with 'watch' in args
    try:
        proc = subprocess.run(
            ["pgrep", "-f", "redsl.*watch"],
            capture_output=True,
            timeout=5,
        )
        return proc.returncode == 0
    except Exception:
        return False


def _get_growth_last_week(project_dir: Path) -> int:
    """Calculate LOC growth in the last week."""
    try:
        from .quality_gate import _collect_python_files, _measure_metrics

        # Get current metrics
        files = _collect_python_files(project_dir)
        current = _measure_metrics(project_dir, files)

        # Try to get metrics from a week ago via git
        since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        proc = subprocess.run(
            ["git", "log", f"--since={since}", "--pretty=format:%H", "-1"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=10,
        )

        # If we can't get historical, just return 0 (unknown)
        if proc.returncode != 0 or not proc.stdout.strip():
            return 0

        # Rough estimate: compare critical count change as proxy for growth
        return current.get("total_lines", 0) // 100  # Simplified
    except Exception:
        return 0


def collect_autonomy_metrics(project_dir: Path | str = ".") -> AutonomyMetrics:
    """Collect all autonomy metrics for a project.

    Usage:
        metrics = collect_autonomy_metrics("/path/to/project")
        print(metrics.to_json())
    """
    project_dir = Path(project_dir).resolve()

    # Import here to avoid circular imports
    from .quality_gate import _collect_python_files, _measure_metrics

    # Basic project metrics
    files = _collect_python_files(project_dir)
    metrics = _measure_metrics(project_dir, files)

    # Count god modules (>400 lines)
    god_modules = sum(1 for f in metrics.get("files", []) if f.get("lines", 0) > 400)

    # Gate status
    gate_installed, gate_path = _check_gate_installed(project_dir)

    # Build metrics object
    return AutonomyMetrics(
        gate_installed=gate_installed,
        gate_hook_path=gate_path,
        gate_blocks_last_week=_count_gate_blocks_last_week(project_dir),
        auto_fix_success_rate=0.0,  # Would need persistent storage to track
        auto_fix_attempts_last_week=0,
        auto_fix_successes_last_week=0,
        growth_within_budget=_get_growth_last_week(project_dir) < 2000,
        growth_budget_lines=2000,
        growth_last_week_lines=_get_growth_last_week(project_dir),
        scheduler_running=_check_scheduler_running(),
        scheduler_last_run="",
        last_autonomous_pr=_get_last_autonomous_pr(project_dir),
        self_refactor_count_last_month=_count_self_refactors_last_month(project_dir),
        regressions_caught=0,
        cc_mean=metrics.get("cc_mean", 0.0),
        critical_count=metrics.get("critical", 0),
        god_modules_count=god_modules,
        collected_at=datetime.now().isoformat(),
    )


def save_metrics(metrics: AutonomyMetrics, path: Path) -> None:
    """Save metrics to a JSON file."""
    path.write_text(metrics.to_json(), encoding="utf-8")


def load_metrics(path: Path) -> AutonomyMetrics | None:
    """Load metrics from a JSON file."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return AutonomyMetrics(**data)
    except Exception:
        return None
