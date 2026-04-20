"""Update planfile.yaml task status after successful refactor applies.

Supports both schema formats:
- Old: ``schema: '1.0'``, flat ``tasks:`` list
- New: ``apiVersion: redsl.plan/v1``, ``spec.tasks:``
"""

from __future__ import annotations

import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_PLANFILE_NAME = "planfile.yaml"


def _load_yaml_module() -> Any:
    """Import yaml module with error handling."""
    try:
        import yaml  # type: ignore[import]
        return yaml
    except ImportError:
        logger.warning("planfile_updater: PyYAML not available, skipping planfile update")
        return None


def _load_planfile_data(planfile_path: Path, yaml_mod: Any) -> dict | None:
    """Load and parse planfile.yaml."""
    if not planfile_path.exists():
        logger.debug("planfile_updater: no planfile.yaml in %s, skipping", planfile_path.parent)
        return None
    try:
        return yaml_mod.safe_load(planfile_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        logger.warning("planfile_updater: failed to parse %s: %s", planfile_path, exc)
        return None


def _normalize_applied_files(applied_files: list[str], project_dir: Path) -> set[str]:
    """Normalize applied files to relative paths for matching."""
    norm_applied = set()
    for f in applied_files:
        p = Path(f)
        if p.is_absolute():
            try:
                p = p.relative_to(project_dir)
            except ValueError:
                pass
        norm_applied.add(str(p))
        norm_applied.add(p.name)
    return norm_applied


def _match_and_update_task(
    task: dict, norm_applied: set[str], now_iso: str
) -> bool:
    """Check if task matches applied files and update if so."""
    if task.get("status") == "done":
        return False
    task_file = str(task.get("file", ""))
    task_file_name = Path(task_file).name if task_file else ""
    if task_file not in norm_applied and task_file_name not in norm_applied:
        return False

    task["status"] = "done"
    task["completed_at"] = now_iso
    logger.info(
        "planfile_updater: marked task [%s] done (%s)",
        task.get("id", "?"),
        task_file,
    )
    return True


def _save_planfile_changes(
    planfile_path: Path, data: dict, yaml_mod: Any, updated: int
) -> int:
    """Save changes atomically to planfile."""
    try:
        _atomic_write_yaml(planfile_path, data, yaml_mod)
        logger.info("planfile_updater: updated %d task(s) in %s", updated, planfile_path)
        return updated
    except Exception as exc:
        logger.warning("planfile_updater: failed to write %s: %s", planfile_path, exc)
        return 0


def mark_applied_tasks_done(
    project_dir: Path,
    applied_files: list[str],
) -> int:
    """Mark planfile tasks whose ``file:`` matches applied files as done.

    Returns the number of tasks updated.
    """
    if not applied_files:
        return 0

    yaml_mod = _load_yaml_module()
    if yaml_mod is None:
        return 0

    planfile_path = project_dir / _PLANFILE_NAME
    data = _load_planfile_data(planfile_path, yaml_mod)
    if data is None:
        return 0

    tasks = _get_tasks(data)
    if not tasks:
        return 0

    norm_applied = _normalize_applied_files(applied_files, project_dir)
    now_iso = datetime.now(timezone.utc).isoformat()
    updated = sum(
        _match_and_update_task(task, norm_applied, now_iso) for task in tasks
    )

    if updated:
        _update_stats(data)
        return _save_planfile_changes(planfile_path, data, yaml_mod, updated)

    return updated


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

def _get_tasks(data: dict) -> list:
    """Return the mutable task list regardless of schema version."""
    api = data.get("apiVersion", "")
    if api.startswith("redsl.plan"):
        return data.get("spec", {}).get("tasks", [])
    # Old schema: top-level tasks:
    return data.get("tasks", [])


def _update_stats(data: dict) -> None:
    """Recompute stats section for old-schema planfiles."""
    tasks = data.get("tasks")
    if tasks is None:
        return  # new schema — no stats to update
    done = sum(1 for t in tasks if t.get("status") == "done")
    total = len(tasks)
    todo = total - done
    stats = data.setdefault("stats", {})
    stats["total"] = total
    stats["done"] = done
    stats["todo"] = todo


def get_todo_tasks(project_dir: Path) -> list[dict]:
    """Return list of todo tasks from planfile.yaml, sorted by priority (ascending)."""
    yaml_mod = _load_yaml_module()
    if yaml_mod is None:
        return []
    planfile_path = project_dir / _PLANFILE_NAME
    data = _load_planfile_data(planfile_path, yaml_mod)
    if data is None:
        return []
    tasks = _get_tasks(data)
    todo_tasks = [t for t in tasks if t.get("status") == "todo" and t.get("file")]
    # Sort by priority ascending (lower number = higher priority)
    todo_tasks.sort(key=lambda t: (t.get("priority", 99), t.get("id", "")))
    return todo_tasks


_PLANFILE_ACTION_MAP: dict[str, str] = {
    "reduce_complexity": "extract_functions",
    "extract_functions": "extract_functions",
    "split_module": "split_module",
    "deduplicate": "deduplicate",
    "rename_variables": "rename_variables",
    "add_type_hints": "add_type_hints",
    "remove_dead_code": "remove_dead_code",
    "simplify_conditionals": "simplify_conditionals",
    "extract_class": "extract_class",
    "remove_unused_imports": "remove_unused_imports",
}


def _planfile_action_to_refactor_action(action_str: str) -> "Any":
    """Map planfile action string to RefactorAction enum value."""
    from redsl.dsl.engine import RefactorAction
    mapped = _PLANFILE_ACTION_MAP.get(action_str, "extract_functions")
    try:
        return RefactorAction(mapped)
    except ValueError:
        return RefactorAction.EXTRACT_FUNCTIONS


def _run_direct_refactor_for_task(
    orchestrator: "Any",
    project_dir: Path,
    task_file: str,
    task_action: str,
    validate_regix: bool = False,
    rollback_on_failure: bool = False,
    use_sandbox: bool = False,
    run_tests: bool = False,
) -> "Any":
    """Force-execute a refactor action for a specific file from a planfile task.

    Bypasses DSL scoring — creates a Decision directly from the task data.
    """
    from redsl.dsl.engine import Decision
    from redsl.execution.cycle import (
        _get_applied_files,
        _new_cycle_report,
        _run_execute_phase,
        _run_project_validators_phase,
        _run_reflect_phase,
        _run_test_validation_phase,
        _run_update_planfile_phase,
        _run_validate_phase,
    )
    from redsl.execution.resolution import _consult_memory_for_decisions
    from redsl.execution.test_validation import run_tests_baseline
    from redsl.execution.validation import _snapshot_regix_before

    orchestrator._cycle_count += 1
    report = _new_cycle_report(orchestrator)

    refactor_action = _planfile_action_to_refactor_action(task_action)
    decision = Decision(
        rule_name=f"planfile:{task_action}",
        action=refactor_action,
        score=1.0,
        target_file=task_file,
        rationale=f"planfile task: {task_action} on {task_file}",
    )

    decisions = [decision]
    report.decisions_count = 1

    regix_before = _snapshot_regix_before(project_dir, validate_regix)
    _consult_memory_for_decisions(orchestrator, decisions)
    tests_baseline = run_tests_baseline(project_dir) if run_tests else None

    _run_execute_phase(orchestrator, decisions, project_dir, use_sandbox, report)
    _run_validate_phase(orchestrator, project_dir, regix_before, rollback_on_failure, validate_regix, report)
    _run_update_planfile_phase(orchestrator, project_dir, report)
    _run_project_validators_phase(project_dir, report)
    _run_test_validation_phase(orchestrator, project_dir, tests_baseline, run_tests, report)
    _run_reflect_phase(orchestrator, report)

    return report


def run_tasks_from_planfile(
    orchestrator: Any,
    project_dir: Path,
    max_actions: int = 5,
    use_code2llm: bool = False,
    validate_regix: bool = False,
    rollback_on_failure: bool = False,
    use_sandbox: bool = False,
    run_tests: bool = False,
) -> dict:
    """Iterate over planfile todo tasks and run refactor for each file directly.

    Uses ``_run_direct_refactor_for_task`` to bypass DSL scoring and force the
    action specified in the planfile task.

    Returns summary dict with keys: attempted, applied, skipped.
    """
    todo_tasks = get_todo_tasks(project_dir)
    if not todo_tasks:
        logger.info("planfile_updater: no todo tasks in planfile.yaml for %s", project_dir)
        return {"attempted": 0, "applied": 0, "skipped": 0}

    remaining = min(max_actions, len(todo_tasks))
    attempted = applied = skipped = 0

    for task in todo_tasks[:remaining]:
        task_file = task.get("file", "")
        task_action = task.get("action", "reduce_complexity")
        task_id = task.get("id", "?")
        full_path = project_dir / task_file
        if not full_path.exists():
            logger.warning(
                "planfile_updater: task [%s] file not found: %s — skipping",
                task_id, task_file,
            )
            skipped += 1
            continue

        logger.info("planfile_updater: processing task [%s] action=%s file=%s", task_id, task_action, task_file)
        attempted += 1
        report = _run_direct_refactor_for_task(
            orchestrator,
            project_dir,
            task_file=task_file,
            task_action=task_action,
            validate_regix=validate_regix,
            rollback_on_failure=rollback_on_failure,
            use_sandbox=use_sandbox,
            run_tests=run_tests,
        )
        if report.proposals_applied > 0:
            applied += 1
            logger.info("planfile_updater: task [%s] applied successfully", task_id)
        else:
            logger.info("planfile_updater: task [%s] no changes applied (proposals_applied=0)", task_id)

    return {"attempted": attempted, "applied": applied, "skipped": skipped}


def _atomic_write_yaml(path: Path, data: dict, yaml_mod) -> None:
    """Write YAML atomically via temp file rename."""
    content = yaml_mod.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
    dir_ = path.parent
    fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
