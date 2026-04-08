"""Validation utilities for refactoring cycles."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from redsl.validation import regix_bridge

if TYPE_CHECKING:
    from redsl.orchestrator import CycleReport

logger = logging.getLogger(__name__)


def _snapshot_regix_before(project_dir: Path, validate_regix: bool) -> dict | None:
    """Take a regix snapshot before the cycle if validation is enabled."""
    if not validate_regix:
        return None

    regix_before = regix_bridge.snapshot(project_dir, ref="HEAD")
    if regix_before:
        logger.info("regix: snapshot taken before cycle")
    return regix_before


def _validate_with_regix(
    project_dir: Path,
    before_snapshot: dict | None,
    rollback_on_regression: bool,
    report: "CycleReport",
) -> None:
    """Validate changes with regix and update report."""
    passed, regix_report = regix_bridge.validate_working_tree(
        project_dir,
        before_snapshot=before_snapshot,
        rollback_on_failure=rollback_on_regression,
    )
    if not passed:
        regressions = regix_report.get("regressions", [])
        report.errors.append(
            f"regix: regression detected — {len(regressions)} metric(s) degraded"
        )
        if rollback_on_regression:
            report.errors.append("regix: changes rolled back")
            report.proposals_applied = 0
    else:
        logger.info("regix: no regressions detected")

    gates = regix_bridge.check_gates(project_dir)
    if gates and not gates["passed"]:
        for failure in gates.get("failures", []):
            logger.warning("regix gate failure: %s", failure)


__all__ = ["_snapshot_regix_before", "_validate_with_regix"]
