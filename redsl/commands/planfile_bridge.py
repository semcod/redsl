"""Bridge to planfile — ticket and sprint management integration."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def is_available() -> bool:
    """Return True if planfile CLI is installed and functional."""
    if not shutil.which("planfile"):
        return False
    try:
        proc = subprocess.run(
            ["planfile", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        return proc.returncode == 0 and "version" in proc.stdout.lower()
    except Exception:
        return False


def _build_ticket_cmd(
    title: str,
    description: str,
    priority: str,
    labels: list[str] | None,
) -> list[str]:
    """Build the planfile ticket add command."""
    cmd = [
        "planfile", "ticket", "add",
        "--title", title,
        "--description", description,
        "--priority", priority,
    ]
    if labels:
        for label in labels:
            cmd += ["--label", label]
    return cmd


def _extract_ticket_id(output: str) -> str | None:
    """Extract ticket ID from planfile output."""
    for line in output.splitlines():
        line_s = line.strip()
        # Direct ID at start of line
        if line_s.startswith("#") and len(line_s) > 1:
            return line_s.split()[0]
        # Look for ID in 'created' or 'ticket' lines
        if "created" in line_s.lower() or "ticket" in line_s.lower():
            parts = line_s.split()
            for p in parts:
                if p.startswith("#") or (p.isdigit() and len(p) <= 6):
                    return p
    return None


def create_ticket(
    project_dir: Path,
    title: str,
    description: str,
    priority: str = "medium",
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Create a planfile ticket for a refactoring action.

    Returns:
        Dict with keys: created (bool), ticket_id (str|None), raw (str).
    """
    if not is_available():
        return {"created": False, "ticket_id": None, "available": False}

    cmd = _build_ticket_cmd(title, description, priority, labels)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=15,
            cwd=str(project_dir),
        )
        output = proc.stdout + proc.stderr
        ticket_id = _extract_ticket_id(output)

        return {
            "created": proc.returncode == 0,
            "ticket_id": ticket_id,
            "available": True,
            "raw": output[:300],
        }
    except subprocess.TimeoutExpired:
        logger.warning("planfile ticket add timed out")
        return {"created": False, "ticket_id": None, "available": True, "timed_out": True}
    except Exception as exc:
        logger.warning("planfile create_ticket error: %s", exc)
        return {"created": False, "ticket_id": None, "available": True, "error": str(exc)}


def list_tickets(project_dir: Path, status: str | None = None) -> list[dict[str, Any]]:
    """List planfile tickets, optionally filtered by status.

    Returns:
        List of ticket dicts or empty list on failure.
    """
    if not is_available():
        return []

    cmd = ["planfile", "ticket", "list", "--format", "json"]
    if status:
        cmd += ["--status", status]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=15,
            cwd=str(project_dir),
        )
        if proc.returncode == 0 and proc.stdout.strip():
            raw = proc.stdout.strip()
            start = raw.find("[")
            if start != -1:
                return _safe_json(raw[start:]) or []
        return []
    except Exception as exc:
        logger.warning("planfile list_tickets error: %s", exc)
        return []


def report_refactor_results(
    project_dir: Path,
    decisions_applied: int,
    files_modified: list[str],
    avg_cc_before: float,
    avg_cc_after: float,
) -> dict[str, Any]:
    """Create a summary ticket for a completed refactor cycle.

    Returns:
        Result dict from create_ticket.
    """
    delta = avg_cc_before - avg_cc_after
    description = (
        f"ReDSL refactor cycle completed.\n"
        f"- Decisions applied: {decisions_applied}\n"
        f"- Files modified: {len(files_modified)}\n"
        f"- Avg CC: {avg_cc_before:.1f} → {avg_cc_after:.1f} (Δ {delta:+.1f})\n"
        f"- Changed: {', '.join(files_modified[:5])}"
        + (" ..." if len(files_modified) > 5 else "")
    )
    return create_ticket(
        project_dir=project_dir,
        title=f"ReDSL: {decisions_applied} refactors applied (CC {avg_cc_before:.1f}→{avg_cc_after:.1f})",
        description=description,
        priority="low",
        labels=["refactor", "automated"],
    )


def _safe_json(text: str) -> Any:
    """Parse JSON silently, return None on failure."""
    import json
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None
