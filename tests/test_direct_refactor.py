#!/usr/bin/env python3
"""Test direct refactoring on a single project."""

from __future__ import annotations

import logging
from pathlib import Path

from redsl.orchestrator import RefactorOrchestrator
from redsl.config import AgentConfig
from redsl.dsl import RefactorAction
from redsl.execution import _execute_direct_refactor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

def main() -> None:
    """Test direct refactoring."""
    project_path = Path("/home/tom/github/semcod/ats-benchmark")
    
    print(f"Testing direct refactoring on {project_path}")
    
    # Initialize orchestrator
    config = AgentConfig()
    config.refactor.apply_changes = True
    config.refactor.reflection_rounds = 0  # No reflection needed for direct refactors
    
    orchestrator = RefactorOrchestrator(config)
    
    # Get decisions
    from redsl.analyzers import CodeAnalyzer
    analyzer = CodeAnalyzer()
    analysis = analyzer.analyze_project(project_path)
    contexts = analysis.to_dsl_contexts()
    
    # Filter for quality decisions only
    all_decisions = orchestrator.dsl_engine.evaluate(contexts)
    quality_decisions = [d for d in all_decisions if d.action in [
        RefactorAction.REMOVE_UNUSED_IMPORTS,
        RefactorAction.FIX_MODULE_EXECUTION_BLOCK,
        RefactorAction.EXTRACT_CONSTANTS,
        RefactorAction.ADD_RETURN_TYPES,
    ]]
    
    print(f"\nFound {len(quality_decisions)} quality decisions:")
    for d in quality_decisions[:5]:
        print(f"  - {d.action.value} on {d.target_file} (score={d.score:.2f})")
        if d.action == RefactorAction.REMOVE_UNUSED_IMPORTS:
            unused = d.context.get("unused_import_list", [])
            print(f"    Unused imports: {unused}")
    
    # Execute first few quality decisions
    print("\nExecuting first 3 quality decisions:")
    for i, decision in enumerate(quality_decisions[:3]):
        print(f"\n{i+1}. Executing: {decision.action.value} on {decision.target_file}")
        result = _execute_direct_refactor(orchestrator, decision, project_path)
        print(f"   Applied: {result.applied}")
        print(f"   Validated: {result.validated}")
        if result.errors:
            print(f"   Errors: {result.errors}")
    
    # Show applied changes
    changes = orchestrator.direct_refactor.get_applied_changes()
    print(f"\nTotal direct changes applied: {len(changes)}")
    for change in changes:
        print(f"  - {change['action']}: {change['details']}")
    
    # Check TODO.md reduction
    todo_file = project_path / "TODO.md"
    if todo_file.exists():
        content = todo_file.read_text(encoding="utf-8")
        active_issues = sum(1 for line in content.splitlines() if line.startswith("- [ ]"))
        print(f"\nTODO.md active issues: {active_issues}")

if __name__ == "__main__":
    main()
