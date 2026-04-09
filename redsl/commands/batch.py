"""Batch refactoring commands for reDSL."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from ..orchestrator import RefactorOrchestrator
from ..config import AgentConfig
from .hybrid import _regenerate_todo

logger = logging.getLogger(__name__)


def run_semcod_batch(semcod_root: Path, max_actions: int = 10) -> dict[str, Any]:
    """Run batch refactoring on semcod projects."""
    # Find all projects with TODO.md
    projects = []
    for item in semcod_root.iterdir():
        if item.is_dir() and (item / "TODO.md").exists():
            projects.append(item)
    
    print(f"\nFound {len(projects)} projects with TODO.md")
    
    # Process each project
    total_results = {
        "projects_processed": 0,
        "total_decisions": 0,
        "total_applied": 0,
        "total_errors": 0,
        "project_details": []
    }
    
    for project in sorted(projects):
        print(f"\n{'='*60}")
        print(f"Processing: {project.name}")
        print(f"{'='*60}")
        
        # Measure before
        todo_file = project / "TODO.md"
        before = measure_todo_reduction(project)
        print(f"TODO.md: {before['active_issues']} active issues")
        
        # Apply refactoring
        try:
            report = apply_refactor(project, max_actions)
            
            print(f"\nResults:")
            print(f"  Decisions: {report.decisions_count}")
            print(f"  Proposals generated: {report.proposals_generated}")
            print(f"  Applied: {report.proposals_applied}")
            print(f"  Rejected: {report.proposals_rejected}")
            
            if report.errors:
                print(f"  Errors: {len(report.errors)}")
                for error in report.errors[:3]:
                    print(f"    - {error}")

            _regenerate_todo(project)
            
            # Measure after
            after = measure_todo_reduction(project)
            reduction = before['active_issues'] - after['active_issues']
            
            print(f"\nTODO.md change: {before['active_issues']} → {after['active_issues']} (reduction: {reduction})")
            
            # Collect results
            total_results["projects_processed"] += 1
            total_results["total_decisions"] += report.decisions_count
            total_results["total_applied"] += report.proposals_applied
            total_results["total_errors"] += len(report.errors)
            
            total_results["project_details"].append({
                "name": project.name,
                "decisions": report.decisions_count,
                "applied": report.proposals_applied,
                "errors": len(report.errors),
                "todo_reduction": reduction
            })
            
        except Exception as e:
            logger.error(f"Failed to process {project}: {e}")
            total_results["total_errors"] += 1
    
    return total_results


def apply_refactor(project_path: Path, max_actions: int = 10) -> Any:
    """Apply reDSL to a project and return the report."""
    logger.info(f"Starting reDSL on {project_path}")
    
    # Initialize orchestrator with LLM config from .env
    config = AgentConfig.from_env()
    config.refactor.dry_run = False
    config.refactor.reflection_rounds = 1  # Keep some reflection for quality
    
    orchestrator = RefactorOrchestrator(config)
    
    # Run the refactoring cycle
    report = orchestrator.run_cycle(project_path, max_actions=max_actions)
    
    return report


def measure_todo_reduction(project_path: Path) -> dict[str, Any]:
    """Measure TODO.md before and after refactoring."""
    todo_file = project_path / "TODO.md"
    if not todo_file.exists():
        return {"before": 0, "after": 0, "reduction": 0}
    
    content = todo_file.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    # Count active issues (lines starting with - [ ])
    active_issues = sum(1 for line in lines if line.startswith("- [ ]"))
    
    return {"active_issues": active_issues, "total_lines": len(lines)}
