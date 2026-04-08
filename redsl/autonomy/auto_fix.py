"""Auto-fix pipeline — automatically repair quality gate violations.

Attempts to fix violations from the quality gate. If a fix cannot be
applied automatically it creates a ticket / issue description for manual
resolution.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AutoFixResult:
    """Outcome of the auto-fix pipeline."""

    fixed: list[str] = field(default_factory=list)
    manual_needed: list[str] = field(default_factory=list)
    tickets_created: list[dict[str, Any]] = field(default_factory=list)


def auto_fix_violations(project_dir: Path, violations: list[str]) -> AutoFixResult:
    """Try to automatically fix each violation; create ticket on failure."""
    project_dir = Path(project_dir).resolve()
    result = AutoFixResult()

    for violation in violations:
        fix = _attempt_fix(project_dir, violation)

        if fix["fixed"]:
            result.fixed.append(violation)
        else:
            result.manual_needed.append(violation)
            ticket = _create_fix_ticket(project_dir, violation, fix.get("reason", ""))
            result.tickets_created.append(ticket)

    return result


# ---------------------------------------------------------------------------
# Fix strategies
# ---------------------------------------------------------------------------

_FILE_PATH_RE = re.compile(r"(?:file |New file |^)([^\s]+\.py)", re.MULTILINE)
_FUNC_NAME_RE = re.compile(r"function (\w+)")
_CC_VALUE_RE = re.compile(r"CC=(\d+)")


def _extract_file_path(violation: str) -> str | None:
    m = _FILE_PATH_RE.search(violation)
    return m.group(1) if m else None


def _extract_function_name(violation: str) -> str | None:
    m = _FUNC_NAME_RE.search(violation)
    return m.group(1) if m else None


def _attempt_fix(project_dir: Path, violation: str) -> dict:
    """Route violation to the best available fix strategy."""

    if "exceeded" in violation or "New file" in violation and "limit" in violation:
        file_path = _extract_file_path(violation)
        if file_path:
            return _auto_split_module(project_dir, file_path)

    if "CC=" in violation and "limit" in violation:
        func_name = _extract_function_name(violation)
        file_path = _extract_file_path(violation)
        if func_name and file_path:
            return _auto_extract_functions(project_dir, file_path, func_name)

    if "CC mean increased" in violation:
        return _auto_reduce_cc_mean(project_dir)

    if "Critical count increased" in violation:
        return _auto_fix_criticals(project_dir)

    return {"fixed": False, "reason": "Unknown violation type"}


def _auto_split_module(project_dir: Path, file_path: str) -> dict:
    """Request the orchestrator to split a module."""
    try:
        from redsl.orchestrator import RefactorOrchestrator
        from redsl.config import AgentConfig
        from redsl.dsl import Decision, RefactorAction

        config = AgentConfig.from_env()
        config.refactor.dry_run = False
        config.refactor.reflection_rounds = 2

        orch = RefactorOrchestrator(config)
        decision = Decision(
            rule_name="auto_gate_split",
            action=RefactorAction.SPLIT_MODULE,
            score=10.0,
            target_file=file_path,
            rationale="Quality gate: file exceeds size limit",
        )

        from redsl.execution import _execute_decision
        result = _execute_decision(orch, decision, project_dir)
        applied = getattr(result, "applied", False) and getattr(result, "validated", True)
        errors = getattr(result, "errors", [])
        return {"fixed": applied, "reason": "; ".join(errors) if errors else "OK"}
    except Exception as exc:
        logger.warning("auto_split_module failed: %s", exc)
        return {"fixed": False, "reason": str(exc)}


def _auto_extract_functions(project_dir: Path, file_path: str, func_name: str) -> dict:
    """Request the orchestrator to extract functions."""
    try:
        from redsl.orchestrator import RefactorOrchestrator
        from redsl.config import AgentConfig
        from redsl.dsl import Decision, RefactorAction

        config = AgentConfig.from_env()
        config.refactor.dry_run = False

        orch = RefactorOrchestrator(config)
        decision = Decision(
            rule_name="auto_gate_extract",
            action=RefactorAction.EXTRACT_FUNCTIONS,
            score=10.0,
            target_file=file_path,
            target_function=func_name,
            rationale=f"Quality gate: {func_name} CC exceeds limit",
        )

        from redsl.execution import _execute_decision
        result = _execute_decision(orch, decision, project_dir)
        applied = getattr(result, "applied", False) and getattr(result, "validated", True)
        errors = getattr(result, "errors", [])
        return {"fixed": applied, "reason": "; ".join(errors) if errors else "OK"}
    except Exception as exc:
        logger.warning("auto_extract_functions failed: %s", exc)
        return {"fixed": False, "reason": str(exc)}


def _auto_reduce_cc_mean(project_dir: Path) -> dict:
    """Try to reduce CC mean by refactoring the worst functions."""
    try:
        from redsl.orchestrator import RefactorOrchestrator
        from redsl.config import AgentConfig

        config = AgentConfig.from_env()
        config.refactor.dry_run = False
        orch = RefactorOrchestrator(config)
        report = orch.run_cycle(project_dir, max_actions=3)
        return {
            "fixed": report.proposals_applied > 0,
            "reason": f"Applied {report.proposals_applied} refactorings" if report.proposals_applied else "No fixes applied",
        }
    except Exception as exc:
        logger.warning("auto_reduce_cc_mean failed: %s", exc)
        return {"fixed": False, "reason": str(exc)}


def _auto_fix_criticals(project_dir: Path) -> dict:
    """Try to fix new critical-complexity functions."""
    return _auto_reduce_cc_mean(project_dir)


# ---------------------------------------------------------------------------
# Ticket creation (lightweight)
# ---------------------------------------------------------------------------

def _create_fix_ticket(project_dir: Path, violation: str, reason: str) -> dict:
    """Create a lightweight ticket descriptor for manual resolution."""
    return {
        "project": project_dir.name,
        "violation": violation,
        "auto_fix_reason": reason,
        "suggested_action": _suggest_manual_action(violation),
    }


def _suggest_manual_action(violation: str) -> str:
    if "exceeded" in violation or "New file" in violation:
        return "Split the module into smaller files (<400L each)."
    if "CC=" in violation:
        return "Extract helper functions to reduce cyclomatic complexity."
    if "CC mean" in violation:
        return "Review recent changes and simplify complex functions."
    if "Critical" in violation:
        return "Refactor critical-complexity functions (CC > 15)."
    return "Review the violation and apply a targeted fix."
