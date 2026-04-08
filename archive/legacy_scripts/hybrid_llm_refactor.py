#!/usr/bin/env python3
"""Hybrid quality refactoring with LLM supervision - applies quality changes with optional LLM validation."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from app.orchestrator import RefactorOrchestrator
from app.config import AgentConfig
from app.dsl import RefactorAction
from app.analyzers import CodeAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


_QUALITY_ACTIONS = {
    RefactorAction.REMOVE_UNUSED_IMPORTS,
    RefactorAction.FIX_MODULE_EXECUTION_BLOCK,
    RefactorAction.EXTRACT_CONSTANTS,
    RefactorAction.ADD_RETURN_TYPES,
}


def _build_config(enable_llm: bool) -> AgentConfig:
    if enable_llm:
        config = AgentConfig.from_env()  # Load LLM config from .env

        # Override model from .env if specified
        if os.getenv("LLM_MODEL"):
            config.llm.model = os.getenv("LLM_MODEL")
        elif os.getenv("REFACTOR_LLM_MODEL"):
            config.llm.model = os.getenv("REFACTOR_LLM_MODEL")

        config.refactor.apply_changes = True
        config.refactor.reflection_rounds = 1  # Enable reflection
        config.refactor.dry_run = False  # Ensure we apply changes
        print(f"  Using LLM model: {config.llm.model}")
        print(f"  API key configured: {bool(config.llm.api_key)}")
        return config

    config = AgentConfig()
    config.refactor.apply_changes = True
    config.refactor.reflection_rounds = 0
    config.refactor.dry_run = False
    return config


def _select_decisions(
    orchestrator: RefactorOrchestrator,
    analysis: Any,
    enable_llm: bool,
    max_changes: int,
) -> list[Any]:
    contexts = analysis.to_dsl_contexts()

    if enable_llm:
        return orchestrator.dsl_engine.top_decisions(contexts, limit=max_changes * 2)

    decisions = orchestrator.dsl_engine.evaluate(contexts)
    return [decision for decision in decisions if decision.action in _QUALITY_ACTIONS]


def _group_decisions_by_file(decisions: list[Any]) -> dict[str, list[Any]]:
    decisions_by_file: dict[str, list[Any]] = {}
    for decision in decisions:
        decisions_by_file.setdefault(decision.target_file, []).append(decision)
    return decisions_by_file


def _build_changes_by_type() -> dict[str, int]:
    return {
        "remove_unused_imports": 0,
        "fix_module_execution_block": 0,
        "extract_constants": 0,
        "add_return_types": 0,
        "extract_method": 0,
        "simplify_conditionals": 0,
        "reduce_complexity": 0,
        "other": 0,
    }


def _apply_decision(
    orchestrator: RefactorOrchestrator,
    decision: Any,
    project_path: Path,
    changes_by_type: dict[str, int],
) -> tuple[int, int]:
    try:
        result = orchestrator._execute_decision(decision, project_path)

        if result.applied:
            action_key = decision.action.value.replace("-", "_")
            if action_key in changes_by_type:
                changes_by_type[action_key] += 1
            else:
                changes_by_type["other"] += 1
            print(f"    ✓ {decision.action.value}")
            return 1, 0

        if result.errors:
            print(f"    ✗ {decision.action.value}: {result.errors[0]}")
        return 0, 1

    except Exception as e:
        print(f"    ✗ {decision.action.value}: {str(e)[:100]}")
        return 0, 1


def _process_decisions_for_file(
    orchestrator: RefactorOrchestrator,
    file_path: str,
    decisions: list[Any],
    project_path: Path,
    max_changes: int,
    total_applied: int,
    total_errors: int,
    changes_by_type: dict[str, int],
) -> tuple[int, int]:
    print(f"\n  Processing {file_path}:")

    decisions.sort(key=lambda d: d.score, reverse=True)

    for decision in decisions:
        if total_applied >= max_changes:
            print(f"  Reached max changes limit ({max_changes})")
            break

        applied, errors = _apply_decision(orchestrator, decision, project_path, changes_by_type)
        total_applied += applied
        total_errors += errors

    return total_applied, total_errors


def apply_changes_with_llm_supervision(
    project_path: Path, 
    max_changes: int = 50,
    enable_llm: bool = True,
    validate_direct_changes: bool = True
) -> dict[str, Any]:
    """Apply refactorings with optional LLM supervision."""
    print(f"\n{'='*60}")
    print(f"Processing: {project_path.name}")
    print(f"LLM enabled: {enable_llm}")
    print(f"{'='*60}")

    # Initialize orchestrator
    config = _build_config(enable_llm)
    orchestrator = RefactorOrchestrator(config)
    analyzer = CodeAnalyzer()

    # Get all decisions
    analysis = analyzer.analyze_project(project_path)
    all_decisions = _select_decisions(orchestrator, analysis, enable_llm, max_changes)
    
    print(f"Found {len(all_decisions)} decisions")
    
    # Group by file and apply changes
    decisions_by_file = _group_decisions_by_file(all_decisions)
    
    # Execute decisions
    total_applied = 0
    total_errors = 0
    changes_by_type = _build_changes_by_type()

    for file_path, decisions in decisions_by_file.items():
        total_applied, total_errors = _process_decisions_for_file(
            orchestrator,
            file_path,
            decisions,
            project_path,
            max_changes,
            total_applied,
            total_errors,
            changes_by_type,
        )
    
    # Get detailed changes from direct refactor
    changes = orchestrator.direct_refactor.get_applied_changes()
    
    return {
        "project": project_path.name,
        "decisions": len(all_decisions),
        "changes_applied": total_applied,
        "errors": total_errors,
        "changes_by_type": changes_by_type,
        "changes": changes,
        "llm_enabled": enable_llm,
    }


def _parse_args() -> tuple[Path, int, bool, bool]:
    """Parse command line arguments."""
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help", "help"]:
        print("Usage: python hybrid_llm_refactor.py <semcod_root> [--max-changes N] [--no-llm] [--no-validation]")
        print("")
        print("Arguments:")
        print("  semcod_root    Path to semcod directory containing projects")
        print("  --max-changes N Maximum changes per project (default: 50)")
        print("  --no-llm       Disable LLM entirely (same as hybrid_quality_refactor.py)")
        print("  --no-validation Skip LLM validation of direct changes")
        print("")
        print("Examples:")
        print("  python hybrid_llm_refactor.py /home/tom/github/semcod --max-changes 30")
        print("  python hybrid_llm_refactor.py /home/tom/github/semcod --no-llm")
        sys.exit(0 if len(sys.argv) >= 2 and sys.argv[1] in ["-h", "--help", "help"] else 1)
    
    semcod_root = Path(sys.argv[1])
    max_changes = 50
    enable_llm = True
    validate_direct = True
    
    if "--max-changes" in sys.argv:
        idx = sys.argv.index("--max-changes")
        if idx + 1 < len(sys.argv):
            max_changes = int(sys.argv[idx + 1])
    
    if "--no-llm" in sys.argv:
        enable_llm = False
    
    if "--no-validation" in sys.argv:
        validate_direct = False
    
    return semcod_root, max_changes, enable_llm, validate_direct


def _find_projects(semcod_root: Path) -> list[Path]:
    """Find all projects with TODO.md in the semcod root."""
    # Special case: if semcod_root itself is a project with TODO.md
    if (semcod_root / "TODO.md").exists():
        return [semcod_root]
    
    projects = []
    for item in semcod_root.iterdir():
        if item.is_dir() and (item / "TODO.md").exists():
            projects.append(item)
    return projects


def _count_todo_issues(todo_file: Path) -> int:
    """Count TODO issues in a project."""
    if not todo_file.exists():
        return 0
    content = todo_file.read_text(encoding="utf-8")
    return sum(1 for line in content.splitlines() if line.startswith("- [ ]"))


def _regenerate_todo(project: Path) -> None:
    """Regenerate TODO.md with prefact."""
    print(f"  Regenerating TODO.md with prefact...")
    import subprocess
    subprocess.run(["prefact", "-a"], cwd=project, capture_output=True, text=True)


def _process_single_project(
    project: Path,
    max_changes: int,
    enable_llm: bool,
    validate_direct: bool
) -> dict[str, Any]:
    """Process a single project and return results."""
    todo_file = project / "TODO.md"
    before_issues = _count_todo_issues(todo_file)
    
    result = apply_changes_with_llm_supervision(
        project, max_changes, enable_llm, validate_direct
    )
    result["before_issues"] = before_issues
    
    _regenerate_todo(project)
    
    after_issues = _count_todo_issues(todo_file)
    result["after_issues"] = after_issues
    
    reduction = before_issues - after_issues
    if reduction > 0:
        print(f"  TODO reduction: {before_issues} → {after_issues} ({reduction} fewer)")
    
    return result


def _calculate_summary_stats(all_results: list[dict], enable_llm: bool) -> dict[str, Any]:
    """Calculate summary statistics from all results."""
    total_before = sum(r["before_issues"] for r in all_results)
    total_after = sum(r.get("after_issues", 0) for r in all_results)
    total_applied = sum(r["changes_applied"] for r in all_results)
    
    # Collect all change types
    all_types = set()
    for r in all_results:
        all_types.update(r["changes_by_type"].keys())
    
    type_counts = {}
    for change_type in all_types:
        count = sum(r["changes_by_type"].get(change_type, 0) for r in all_results)
        if count > 0:
            type_counts[change_type] = count
    
    # Find top improvements
    sorted_results = sorted(
        all_results,
        key=lambda r: r.get("before_issues", 0) - r.get("after_issues", 0),
        reverse=True
    )
    top_improvements = [
        r for r in sorted_results[:5]
        if r.get("before_issues", 0) - r.get("after_issues", 0) > 0
    ]
    
    return {
        "total_before": total_before,
        "total_after": total_after,
        "total_reduction": total_before - total_after,
        "total_applied": total_applied,
        "type_counts": type_counts,
        "top_improvements": top_improvements,
    }


def _print_summary(stats: dict[str, Any], all_results: list[dict], enable_llm: bool) -> None:
    """Print the refactoring summary."""
    print(f"\n{'='*60}")
    print(f"HYBRID REFACTORING SUMMARY (LLM: {enable_llm})")
    print(f"{'='*60}")
    
    print(f"Total projects: {len(all_results)}")
    print(f"Total issues before: {stats['total_before']}")
    print(f"Total issues after: {stats['total_after']}")
    print(f"Total reduction: {stats['total_reduction']}")
    print(f"\nTotal changes applied: {stats['total_applied']}")
    
    for change_type, count in sorted(stats["type_counts"].items()):
        print(f"  - {change_type}: {count}")
    
    if stats["top_improvements"]:
        print(f"\nTop improvements:")
        for r in stats["top_improvements"]:
            reduction = r.get("before_issues", 0) - r.get("after_issues", 0)
            print(f"  {r['project']}: {reduction} fewer TODOs ({r['changes_applied']} changes)")


def _save_results(all_results: list[dict], semcod_root: Path, enable_llm: bool) -> None:
    """Save results to JSON file."""
    import json
    results_file = semcod_root / f"hybrid_llm_refactor_results_{('llm' if enable_llm else 'direct')}.json"
    results_file.write_text(json.dumps(all_results, indent=2))
    print(f"\nResults saved to: {results_file}")


def main() -> None:
    """Process semcod projects with hybrid refactoring."""
    semcod_root, max_changes, enable_llm, validate_direct = _parse_args()
    
    projects = _find_projects(semcod_root)
    print(f"Found {len(projects)} projects with TODO.md")
    print(f"Max changes per project: {max_changes}")
    
    all_results = []
    
    for project in sorted(projects):
        result = _process_single_project(
            project, max_changes, enable_llm, validate_direct
        )
        all_results.append(result)
    
    stats = _calculate_summary_stats(all_results, enable_llm)
    _print_summary(stats, all_results, enable_llm)
    _save_results(all_results, semcod_root, enable_llm)


if __name__ == "__main__":
    main()
