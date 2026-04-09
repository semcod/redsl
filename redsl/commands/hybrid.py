"""Hybrid quality refactoring commands for reDSL."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

from ..orchestrator import RefactorOrchestrator
from ..config import AgentConfig
from ..dsl import RefactorAction
from ..analyzers import CodeAnalyzer
from ..execution import _execute_direct_refactor
from ..formatters import format_batch_report_markdown

logger = logging.getLogger(__name__)


# Quality actions that don't require LLM
_QUALITY_ACTIONS = [
    RefactorAction.REMOVE_UNUSED_IMPORTS,
    RefactorAction.FIX_MODULE_EXECUTION_BLOCK,
    RefactorAction.EXTRACT_CONSTANTS,
    RefactorAction.ADD_RETURN_TYPES,
]


def _count_todo_issues(todo_file: Path) -> int:
    """Count TODO issues in a project."""
    if not todo_file.exists():
        return 0
    content = todo_file.read_text(encoding="utf-8")
    return sum(1 for line in content.splitlines() if line.startswith("- [ ]"))


def _regenerate_todo(project: Path) -> None:
    """Regenerate TODO.md with prefact."""
    print(f"  Regenerating TODO.md with prefact...")
    result = subprocess.run(
        ["prefact", "-a", "--execute-todos"],
        cwd=project,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.warning(
            "prefact failed for %s: %s",
            project,
            result.stderr.strip() or result.stdout.strip() or "no output",
        )


def _calculate_summary_stats(all_results: list[dict]) -> dict[str, Any]:
    """Calculate summary statistics from all results."""
    total_before = sum(r.get("before_issues", 0) for r in all_results)
    total_after = sum(r.get("after_issues", 0) for r in all_results)
    total_applied = sum(r["changes_applied"] for r in all_results)
    
    type_totals = {action.value: 0 for action in _QUALITY_ACTIONS}
    for r in all_results:
        changes_by_type = r.get("changes_by_type", {})
        for action_type in type_totals:
            type_totals[action_type] += changes_by_type.get(action_type, 0)
    
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
    
    for action_type, count in sorted(stats["type_totals"].items()):
        if count > 0:
            print(f"  - {action_type}: {count}")
    
    if stats["top_improvements"]:
        print(f"\nTop improvements:")
        for r in stats["top_improvements"]:
            reduction = r.get("before_issues", 0) - r.get("after_issues", 0)
            print(f"  {r['project']}: {reduction} fewer TODOs ({r['changes_applied']} changes)")


def _save_results(all_results: list[dict], semcod_root: Path) -> None:
    """Save results to JSON file."""
    results_file = semcod_root / "hybrid_refactor_results.json"
    results_file.write_text(json.dumps(all_results, indent=2))
    print(f"\nResults saved to: {results_file}")


def _save_markdown_report(all_results: list[dict], semcod_root: Path, stats: dict[str, Any]) -> None:
    """Save a human-readable Markdown summary for hybrid batch runs."""
    report_path = semcod_root / "redsl_batch_hybrid_report.md"
    report_payload = {
        "projects_processed": len(all_results),
        "total_before": stats.get("total_before", 0),
        "total_after": stats.get("total_after", 0),
        "total_applied": stats.get("total_applied", 0),
        "total_errors": sum(r.get("errors", 0) for r in all_results),
        "total_decisions": sum(r.get("quality_decisions", 0) for r in all_results),
        "project_details": all_results,
    }
    report_path.write_text(
        format_batch_report_markdown(report_payload, semcod_root, "reDSL Hybrid Batch Report"),
        encoding="utf-8",
    )
    print(f"Markdown report saved to: {report_path}")


def run_hybrid_quality_refactor(project_path: Path, max_changes: int = 50) -> dict[str, Any]:
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
    quality_decisions = [d for d in all_decisions if d.action in _QUALITY_ACTIONS]
    
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
    changes_by_type = {action.value: 0 for action in _QUALITY_ACTIONS}
    
    for file_path, decisions in decisions_by_file.items():
        print(f"\n  Processing {file_path}:")
        
        # Sort by score to apply most important first
        decisions.sort(key=lambda d: d.score, reverse=True)
        
        for decision in decisions:
            if total_applied >= max_changes:
                print(f"  Reached max changes limit ({max_changes})")
                break
                
            result = _execute_direct_refactor(orchestrator, decision, project_path)
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


def _find_projects(semcod_root: Path) -> list[Path]:
    """Find all projects with TODO.md in the semcod root."""
    projects = []
    for item in semcod_root.iterdir():
        if item.is_dir() and (item / "TODO.md").exists():
            projects.append(item)
    return projects


def _process_single_project(
    project: Path,
    max_changes: int
) -> dict[str, Any]:
    """Process a single project and return results."""
    todo_file = project / "TODO.md"
    before_issues = _count_todo_issues(todo_file)
    
    result = run_hybrid_quality_refactor(project, max_changes)
    result["before_issues"] = before_issues
    
    _regenerate_todo(project)
    
    after_issues = _count_todo_issues(todo_file)
    result["after_issues"] = after_issues
    
    reduction = before_issues - after_issues
    if reduction > 0:
        print(f"  TODO reduction: {before_issues} → {after_issues} ({reduction} fewer)")
    
    return result


def run_hybrid_batch(semcod_root: Path, max_changes: int = 30) -> list[dict[str, Any]]:
    """Run hybrid refactoring on all semcod projects."""
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
    _save_markdown_report(all_results, semcod_root, stats)
    
    return all_results
