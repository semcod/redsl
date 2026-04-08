#!/usr/bin/env python3
"""Hybrid quality refactoring - applies all quality changes without LLM dependency."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from app.orchestrator import RefactorOrchestrator
from app.config import AgentConfig
from app.dsl import RefactorAction
from app.analyzers import CodeAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce log noise for batch processing
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def apply_all_quality_changes(project_path: Path, max_changes: int = 50) -> dict[str, Any]:
    """Apply ALL quality refactorings to a project without LLM."""
    print(f"\n{'='*60}")
    print(f"Processing: {project_path.name}")
    print(f"{'='*60}")
    
    # Initialize orchestrator with no LLM dependency
    config = AgentConfig()
    config.refactor.apply_changes = True
    config.refactor.reflection_rounds = 0
    
    orchestrator = RefactorOrchestrator(config)
    analyzer = CodeAnalyzer()
    
    # Get all decisions
    analysis = analyzer.analyze_project(project_path)
    contexts = analysis.to_dsl_contexts()
    all_decisions = orchestrator.dsl_engine.evaluate(contexts)
    
    # Filter for quality decisions ONLY (no LLM needed)
    quality_decisions = [d for d in all_decisions if d.action in [
        RefactorAction.REMOVE_UNUSED_IMPORTS,
        RefactorAction.FIX_MODULE_EXECUTION_BLOCK,
        RefactorAction.EXTRACT_CONSTANTS,
        RefactorAction.ADD_RETURN_TYPES,
    ]]
    
    print(f"Found {len(quality_decisions)} quality decisions")
    
    # Group by file and apply all changes per file
    decisions_by_file: dict[str, list[Any]] = {}
    for d in quality_decisions:
        if d.target_file not in decisions_by_file:
            decisions_by_file[d.target_file] = []
        decisions_by_file[d.target_file].append(d)
    
    # Execute decisions file by file
    total_applied = 0
    total_errors = 0
    changes_by_type = {
        "remove_unused_imports": 0,
        "fix_module_execution_block": 0,
        "extract_constants": 0,
        "add_return_types": 0,
    }
    
    for file_path, decisions in decisions_by_file.items():
        print(f"\n  Processing {file_path}:")
        
        # Sort by score to apply most important first
        decisions.sort(key=lambda d: d.score, reverse=True)
        
        for decision in decisions:
            if total_applied >= max_changes:
                print(f"  Reached max changes limit ({max_changes})")
                break
                
            result = orchestrator._execute_direct_refactor(decision, project_path)
            if result.applied:
                total_applied += 1
                changes_by_type[decision.action.value] += 1
                print(f"    ✓ {decision.action.value}")
            else:
                total_errors += 1
                if result.errors:
                    print(f"    ✗ {decision.action.value}: {result.errors[0]}")
    
    # Get detailed changes
    changes = orchestrator.direct_refactor.get_applied_changes()
    
    return {
        "project": project_path.name,
        "quality_decisions": len(quality_decisions),
        "changes_applied": total_applied,
        "errors": total_errors,
        "changes_by_type": changes_by_type,
        "changes": changes,
    }


def _parse_args() -> tuple[Path, int]:
    """Parse command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python hybrid_quality_refactor.py <semcod_root> [--max-changes N]")
        sys.exit(1)
    
    semcod_root = Path(sys.argv[1])
    max_changes = 50
    
    if "--max-changes" in sys.argv:
        idx = sys.argv.index("--max-changes")
        if idx + 1 < len(sys.argv):
            max_changes = int(sys.argv[idx + 1])
    
    return semcod_root, max_changes


def _find_projects(semcod_root: Path) -> list[Path]:
    """Find all projects with TODO.md in the semcod root."""
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
    max_changes: int
) -> dict[str, Any]:
    """Process a single project and return results."""
    todo_file = project / "TODO.md"
    before_issues = _count_todo_issues(todo_file)
    
    result = apply_all_quality_changes(project, max_changes)
    result["before_issues"] = before_issues
    
    _regenerate_todo(project)
    
    after_issues = _count_todo_issues(todo_file)
    result["after_issues"] = after_issues
    
    reduction = before_issues - after_issues
    if reduction > 0:
        print(f"  TODO reduction: {before_issues} → {after_issues} ({reduction} fewer)")
    
    return result


def _calculate_summary_stats(all_results: list[dict]) -> dict[str, Any]:
    """Calculate summary statistics from all results."""
    total_before = sum(r["before_issues"] for r in all_results)
    total_after = sum(r.get("after_issues", 0) for r in all_results)
    total_applied = sum(r["changes_applied"] for r in all_results)
    
    type_totals = {
        "remove_unused_imports": 0,
        "extract_constants": 0,
        "fix_module_execution_block": 0,
        "add_return_types": 0,
    }
    for key in type_totals:
        type_totals[key] = sum(r["changes_by_type"][key] for r in all_results)
    
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
        "total_applied": total_applied,
        "type_totals": type_totals,
        "top_improvements": top_improvements,
    }


def _print_summary(stats: dict[str, Any], all_results: list[dict]) -> None:
    """Print the refactoring summary."""
    print(f"\n{'='*60}")
    print("HYBRID QUALITY REFACTORING SUMMARY")
    print(f"{'='*60}")
    
    print(f"Total projects: {len(all_results)}")
    print(f"Total issues before: {stats['total_before']}")
    print(f"Total issues after: {stats['total_after']}")
    print(f"Total reduction: {stats['total_before'] - stats['total_after']}")
    print(f"\nTotal changes applied: {stats['total_applied']}")
    print(f"  - Unused imports removed: {stats['type_totals']['remove_unused_imports']}")
    print(f"  - Constants extracted: {stats['type_totals']['extract_constants']}")
    print(f"  - Module blocks fixed: {stats['type_totals']['fix_module_execution_block']}")
    print(f"  - Return types added: {stats['type_totals']['add_return_types']}")
    
    if stats["top_improvements"]:
        print(f"\nTop improvements:")
        for r in stats["top_improvements"]:
            reduction = r.get("before_issues", 0) - r.get("after_issues", 0)
            print(f"  {r['project']}: {reduction} fewer TODOs ({r['changes_applied']} changes)")


def _save_results(all_results: list[dict], semcod_root: Path) -> None:
    """Save results to JSON file."""
    import json
    results_file = semcod_root / "hybrid_refactor_results.json"
    results_file.write_text(json.dumps(all_results, indent=2))
    print(f"\nResults saved to: {results_file}")


def main() -> None:
    """Process semcod projects with hybrid refactoring."""
    semcod_root, max_changes = _parse_args()
    
    projects = _find_projects(semcod_root)
    print(f"Found {len(projects)} projects with TODO.md")
    print(f"Max changes per project: {max_changes}")
    
    all_results = []
    
    for project in sorted(projects):
        result = _process_single_project(project, max_changes)
        all_results.append(result)
    
    stats = _calculate_summary_stats(all_results)
    _print_summary(stats, all_results)
    _save_results(all_results, semcod_root)


if __name__ == "__main__":
    main()
