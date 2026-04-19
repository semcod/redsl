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
    """Iterate over planfile todo tasks and run redsl refactor for each file.

    Returns summary dict with keys: attempted, applied, skipped.
    """
    from redsl.execution.cycle import run_cycle

    todo_tasks = get_todo_tasks(project_dir)
    if not todo_tasks:
        logger.info("planfile_updater: no todo tasks in planfile.yaml for %s", project_dir)
        return {"attempted": 0, "applied": 0, "skipped": 0}

    remaining = min(max_actions, len(todo_tasks))
    attempted = applied = skipped = 0

    for task in todo_tasks[:remaining]:
        task_file = task.get("file", "")
        task_id = task.get("id", "?")
        full_path = project_dir / task_file
        if not full_path.exists():
            logger.warning(
                "planfile_updater: task [%s] file not found: %s — skipping",
                task_id, task_file,
            )
            skipped += 1
            continue

        logger.info("planfile_updater: processing task [%s] file=%s", task_id, task_file)
        attempted += 1
        report = run_cycle(
            orchestrator,
            project_dir,
            max_actions=1,
            use_code2llm=use_code2llm,
            validate_regix=validate_regix,
            rollback_on_failure=rollback_on_failure,
            use_sandbox=use_sandbox,
            target_file=task_file,
            run_tests=run_tests,
        )
        if report.proposals_applied > 0:
            applied += 1
            logger.info("planfile_updater: task [%s] applied successfully", task_id)
        else:
            logger.info("planfile_updater: task [%s] no changes applied", task_id)

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
