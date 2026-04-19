"""Task extractors for different TOON sources."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from .models import PlanTask
from .parsers import get_toon_patterns
from .utils import make_id_generator

logger = logging.getLogger(__name__)


def extract_refactor_decisions(
    toon_content: str, source: str, _next_id: object = None
) -> list[PlanTask]:
    """Extract tasks from refactor cycle TOON (DECISIONS[] section)."""
    if _next_id is None:
        _next_id = make_id_generator()
        
    patterns = get_toon_patterns()
    tasks: list[PlanTask] = []
    why_lines = [(m.start(), m.group(1)) for m in patterns["why"].finditer(toon_content)]

    for m in patterns["decision"].finditer(toon_content):
        idx, action, target = m.groups()
        pos = m.end()
        rationale = next((why for why_pos, why in why_lines if why_pos > pos), "")
        effort = "high" if action in ("split_module", "split_class") else "medium"
        tasks.append(PlanTask(
            id=_next_id("R"),
            title=f"{action}: {Path(target).name}",
            description=rationale.strip() or f"{action} → {target}",
            file=target,
            action=action,
            priority=3,
            effort=effort,
            status="todo",
            labels=["refactor", action.replace("_", "-")],
            source=source,
        ))
    return tasks


def _build_dir_entries(toon_content: str) -> list[tuple[int, int, str]]:
    """Build a map of position -> (indent_level, dir_name) for all directory lines."""
    dir_entries = []
    for m in re.finditer(r"^(\s*)(?:│\s*)*(\S+/)\s+CC", toon_content, re.MULTILINE):
        indent = len(m.group(1)) + m.group(0).count("│")
        dir_name = m.group(2)
        dir_entries.append((m.start(), indent, dir_name))
    return dir_entries


def _build_file_path(module: str, pos: int, dir_entries: list[tuple[int, int, str]]) -> str:
    """Build full path by tracking directory hierarchy based on indentation."""
    dirs_before = [(d_pos, d_indent, d_name) for d_pos, d_indent, d_name in dir_entries if d_pos < pos]
    if not dirs_before:
        return f"{module}.py"

    dirs_before.sort(key=lambda x: x[0])
    path_components = []
    for _, d_indent, d_name in dirs_before:
        while path_components and path_components[-1][0] >= d_indent:
            path_components.pop()
        path_components.append((d_indent, d_name))
    return "".join(d[1] for d in path_components) + f"{module}.py"


def _verify_file_path(file_path: str, module: str, project_path: Path | None) -> str:
    """Verify path exists; if not, search project for the actual file."""
    if project_path is None or (project_path / file_path).exists():
        return file_path

    _EXCLUDE_DIRS = {"venv", ".venv", "node_modules", ".git", "__pycache__", "site-packages", ".tox", "dist", "build"}
    matches = [
        p for p in project_path.rglob(f"{module}.py")
        if not any(part in _EXCLUDE_DIRS for part in p.parts)
    ]
    if matches:
        return str(matches[0].relative_to(project_path))
    return file_path


def _create_complexity_task(
    module: str, loc: str, complexity_count: str, cc_int: int,
    file_path: str, source: str, _next_id
) -> PlanTask:
    """Create a PlanTask for a complexity layer."""
    priority = 1 if cc_int >= 20 else (2 if cc_int >= 15 else 3)
    return PlanTask(
        id=_next_id("Q"),
        title=f"reduce_complexity: {module} (CC={cc_int})",
        description=(
            f"Module {module!r} has cyclomatic complexity CC={cc_int} "
            f"({loc} lines, {complexity_count} complex functions). "
            "Apply guard clauses, extract helpers, reduce nesting."
        ),
        file=file_path,
        action="reduce_complexity",
        priority=priority,
        effort="medium" if cc_int < 15 else "high",
        status="todo",
        labels=["refactor", "complexity", f"cc-{cc_int}"],
        source=source,
    )


def extract_complexity_layers(
    toon_content: str, source: str, _next_id: object = None, project_path: Path | None = None
) -> list[PlanTask]:
    """Extract tasks from code analysis TOON (LAYERS with high CC)."""
    if _next_id is None:
        _next_id = make_id_generator()

    patterns = get_toon_patterns()
    tasks: list[PlanTask] = []
    dir_entries = _build_dir_entries(toon_content)

    for m in patterns["layer"].finditer(toon_content):
        module, loc, complexity_count, cc = m.groups()
        cc_int = int(cc)
        if cc_int < 10:
            continue

        file_path = _build_file_path(module, m.start(), dir_entries)
        file_path = _verify_file_path(file_path, module, project_path)

        tasks.append(_create_complexity_task(
            module, loc, complexity_count, cc_int, file_path, source, _next_id
        ))
    return tasks


def extract_duplications(
    toon_content: str, source: str, _next_id: object = None
) -> list[PlanTask]:
    """Extract tasks from Duplication TOON (DUPLICATES section)."""
    if _next_id is None:
        _next_id = make_id_generator()
        
    patterns = get_toon_patterns()
    tasks: list[PlanTask] = []
    dup_file_positions = [(m.start(), m.group(1)) for m in patterns["dup_file"].finditer(toon_content)]

    for m in patterns["dup_group"].finditer(toon_content):
        func_name, loc, count, saved = m.groups()
        saved_int = int(saved)
        if saved_int < 10:
            continue
        pos = m.end()
        next_group_match = patterns["dup_group"].search(toon_content, pos)
        end_pos = next_group_match.start() if next_group_match else len(toon_content)
        group_files = [fp for fp_pos, fp in dup_file_positions if pos <= fp_pos < end_pos]
        primary_file = group_files[0] if group_files else ""
        priority = 2 if saved_int >= 30 else 3
        tasks.append(PlanTask(
            id=_next_id("D"),
            title=f"extract_function: {func_name} (saves {saved_int}L)",
            description=(
                f"Duplicated {func_name!r}: {count} occurrences, {loc} lines each, "
                f"saves {saved_int} lines. Files: {', '.join(group_files[:3])}"
            ),
            file=primary_file,
            action="extract_function",
            priority=priority,
            effort="low" if saved_int >= 20 else "medium",
            status="todo",
            labels=["refactor", "duplication", "extract-function"],
            source=source,
        ))
    return tasks


def _map_status(raw: dict) -> str:
    """Map raw status string to normalized status."""
    status_raw = str(raw.get("status", "")).lower()
    if "done" in status_raw:
        return "done"
    if "in_progress" in status_raw or "in-progress" in status_raw:
        return "in_progress"
    return "todo"


def _extract_target(raw: dict) -> str:
    """Extract target file from raw task data."""
    target = raw.get("file", raw.get("target", ""))
    locations = raw.get("locations", [])
    if not target and locations:
        # Extract file path from first location (format: "path.py:line-line")
        return locations[0].split(":")[0]
    return target


def _parse_priority(raw: dict) -> int:
    """Parse priority from raw task data."""
    priority_raw = raw.get("priority", 3)
    try:
        return int(priority_raw)
    except (TypeError, ValueError):
        return 3


def _compute_effort(raw: dict, phase_name: str) -> str:
    """Compute effort level from phase name and saved lines."""
    effort_map = {"low": "low", "quick_wins": "low", "structural": "medium"}
    effort = effort_map.get(phase_name, "medium")
    if raw.get("saved_lines", 0) >= 20:
        effort = "low"  # mechanical dedup = easy
    return effort


def _build_labels(raw: dict, phase_name: str, action: str) -> list[str]:
    """Build labels list for task."""
    labels = ["refactor", phase_name.replace("_", "-")]
    if action:
        labels.append(action.replace("_", "-"))
    return labels


def _create_task_from_raw(
    raw: dict, phase_name: str, source: str, task_index: int
) -> PlanTask | None:
    """Create a PlanTask from raw YAML data."""
    if not isinstance(raw, dict):
        return None

    status = _map_status(raw)
    action = raw.get("type", raw.get("pattern", "refactor"))
    target = _extract_target(raw)

    action_text = raw.get("action", "")
    if hasattr(action_text, "strip"):
        action_text = action_text.strip()

    priority = _parse_priority(raw)
    effort = _compute_effort(raw, phase_name)
    labels = _build_labels(raw, phase_name, action)
    task_id = str(raw.get("id", "")) or f"{phase_name[:1].upper()}{task_index}"

    return PlanTask(
        id=task_id,
        title=f"{action}: {Path(target).name}" if target else action,
        description=action_text or f"{action} in {target}",
        file=target,
        action=action,
        priority=priority,
        effort=effort,
        status=status,
        labels=labels,
        source=source,
    )


def refactor_plan_to_tasks(yaml_content: str, source: str = "") -> list[PlanTask]:
    """Convert a redsl ``refactor_plan.yaml`` to PlanTask list.

    The format is a multi-document YAML (``---`` separated) where each
    document is either a ``meta`` block or a ``phase`` block with ``tasks``.
    """
    import yaml

    tasks: list[PlanTask] = []
    docs = list(yaml.safe_load_all(yaml_content))

    for doc in docs:
        if not isinstance(doc, dict):
            continue
        phase_tasks = doc.get("tasks", [])
        phase_name = doc.get("name", "")
        for idx, raw in enumerate(phase_tasks, 1):
            task = _create_task_from_raw(raw, phase_name, source, idx)
            if task:
                tasks.append(task)

    return tasks


def toon_to_tasks(
    toon_content: str,
    source: str = "",
    project_path: Path | None = None
) -> list[PlanTask]:
    """Extract PlanTask list from TOON-format content.

    Handles two TOON subtypes:
    - refactor cycle TOON (DECISIONS[] section) → direct action tasks
    - code analysis TOON (REFACTOR[], LAYERS section) → quality tasks
    """
    _next_id = make_id_generator()

    tasks: list[PlanTask] = []
    tasks.extend(extract_refactor_decisions(toon_content, source, _next_id))
    tasks.extend(extract_complexity_layers(toon_content, source, _next_id, project_path))
    tasks.extend(extract_duplications(toon_content, source, _next_id))

    return tasks
