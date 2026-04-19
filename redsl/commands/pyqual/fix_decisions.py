"""Build direct-refactor Decisions from pyqual analyzer output.

The DSL engine's default rules do not emit the direct-refactor actions
(`REMOVE_UNUSED_IMPORTS`, `EXTRACT_CONSTANTS`, `FIX_MODULE_EXECUTION_BLOCK`,
`ADD_RETURN_TYPES`), so `redsl pyqual fix` synthesises decisions directly
from ``pyqual.analyze_project()['issues']`` grouped by file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from ...dsl import Decision, RefactorAction


def _relative_to(path_str: str, project_abs: Path) -> str:
    p = Path(path_str)
    try:
        return str(p.resolve().relative_to(project_abs))
    except ValueError:
        return path_str


def _unused_import_decisions(
    items: list[dict],
    project_abs: Path,
) -> list[Decision]:
    by_file: dict[str, list[str]] = {}
    for item in items or []:
        by_file.setdefault(_relative_to(item["file"], project_abs), []).append(item["name"])
    return [
        Decision(
            rule_name="pyqual.unused_imports",
            action=RefactorAction.REMOVE_UNUSED_IMPORTS,
            target_file=rel,
            score=1.0,
            rationale=f"Remove {len(names)} unused imports",
            context={"unused_import_list": names},
        )
        for rel, names in by_file.items()
    ]


def _magic_number_decisions(
    items: list[dict],
    project_abs: Path,
) -> list[Decision]:
    by_file: dict[str, list[tuple[int, Any]]] = {}
    for item in items or []:
        by_file.setdefault(_relative_to(item["file"], project_abs), []).append(
            (item["line"], item["value"])
        )
    return [
        Decision(
            rule_name="pyqual.magic_numbers",
            action=RefactorAction.EXTRACT_CONSTANTS,
            target_file=rel,
            score=0.8,
            rationale=f"Extract {len(values)} magic numbers",
            context={"magic_number_list": values},
        )
        for rel, values in by_file.items()
    ]


def _module_execution_decisions(
    items: list[dict],
    project_abs: Path,
) -> list[Decision]:
    decisions: list[Decision] = []
    seen: set[str] = set()
    for item in items or []:
        rel = _relative_to(item["file"], project_abs)
        if rel in seen:
            continue
        seen.add(rel)
        decisions.append(
            Decision(
                rule_name="pyqual.module_execution",
                action=RefactorAction.FIX_MODULE_EXECUTION_BLOCK,
                target_file=rel,
                score=0.7,
                rationale="Wrap module-level execution in __main__ guard",
                context={},
            )
        )
    return decisions


def build_pyqual_fix_decisions(
    issues: Dict[str, Any],
    project_path: Path,
) -> List[Decision]:
    """Build direct-refactor Decisions grouped by file from pyqual issues."""
    project_abs = project_path.resolve()
    return (
        _unused_import_decisions(issues.get("unused_imports", []), project_abs)
        + _magic_number_decisions(issues.get("magic_numbers", []), project_abs)
        + _module_execution_decisions(issues.get("print_statements", []), project_abs)
    )


__all__ = ["build_pyqual_fix_decisions"]
