"""Verdict computation with extracted predicates."""

from __future__ import annotations

from .models import PyqualProjectResult


def _check_analysis_passed(result: PyqualProjectResult) -> tuple[bool, str | None]:
    """Check if analysis stage passed."""
    if not result.config_valid:
        return False, "config"
    return True, None


def _check_gates_passed(result: PyqualProjectResult) -> tuple[bool, str | None]:
    """Check if gates passed."""
    if not result.gates_passed:
        return False, "gates"
    return True, None


def _check_pipeline_requirement(
    result: PyqualProjectResult, require_pipeline: bool
) -> tuple[bool, str | None]:
    """Check pipeline requirement if enabled."""
    if require_pipeline and not result.pipeline_passed:
        return False, "pipeline"
    return True, None


def _check_push_requirement(
    result: PyqualProjectResult, require_push: bool
) -> tuple[bool, str | None]:
    """Check push requirement if enabled."""
    if not require_push:
        return True, None

    if result.dry_run:
        if not result.push_preflight_passed:
            return False, "push-preflight"
        return True, None

    if result.changes_to_commit > 0:
        if not (result.git_committed or result.pipeline_push_passed):
            return False, "commit"
        if not (result.git_pushed or result.pipeline_push_passed):
            return False, "push"
        if result.dirty_after:
            return False, "dirty-after"

    return True, None


def _check_publish_requirement(
    result: PyqualProjectResult, require_publish: bool
) -> tuple[bool, str | None]:
    """Check publish requirement if enabled."""
    if not require_publish:
        return True, None

    if not result.publish_configured:
        return False, "publish-config"

    if not result.dry_run and not result.pipeline_publish_passed:
        return False, "publish"

    return True, None


def _combine_verdicts(checks: list[tuple[bool, str | None]]) -> tuple[str, list[str]]:
    """Combine all check results into final verdict."""
    reasons = [reason for passed, reason in checks if not passed and reason]
    if reasons:
        return "failed", reasons
    return "success", []


def compute_verdict(
    result: PyqualProjectResult,
    require_pipeline: bool = False,
    require_push: bool = False,
    require_publish: bool = False,
) -> tuple[str, list[str]]:
    """Compute final verdict for a project result.

    Returns tuple of (verdict, reasons) where verdict is one of:
    - "success": all checks passed
    - "failed": one or more checks failed
    - "skipped": project was skipped
    - "ready": dry-run with all requirements met
    """
    if result.skipped:
        return "skipped", ([result.skip_reason] if result.skip_reason else [])

    checks = [
        _check_analysis_passed(result),
        _check_gates_passed(result),
        _check_pipeline_requirement(result, require_pipeline),
        _check_push_requirement(result, require_push),
        _check_publish_requirement(result, require_publish),
    ]

    verdict, reasons = _combine_verdicts(checks)

    # Special case: dry-run with requirements but no failures
    if result.dry_run and (require_pipeline or require_push or require_publish) and verdict == "success":
        return "ready", []

    return verdict, reasons
