#!/usr/bin/env python3
"""Test LLM execution path for complex refactoring actions."""

from pathlib import Path

import pytest

from redsl.orchestrator import RefactorOrchestrator
from redsl.config import AgentConfig
from redsl.analyzers import CodeAnalyzer
from redsl.dsl import RefactorAction
from redsl.execution import _execute_decision, get_memory_stats
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture
def project_path() -> Path:
    """Provide a default project path for testing."""
    # Use test_sample_project if available, otherwise skip
    test_project = Path(__file__).parent.parent / "test_sample_project"
    if test_project.exists():
        return test_project
    # Fallback to any Python project in semcod
    semcod_goal = Path("/home/tom/github/semcod/goal")
    if semcod_goal.exists():
        return semcod_goal
    pytest.skip("No suitable test project found")


def test_llm_execution(project_path: Path):
    """Test if LLM-based refactoring actually works."""
    print(f"\n{'='*60}")
    print(f"Testing LLM execution on: {project_path.name}")
    print(f"{'='*60}")
    
    # Initialize with LLM
    config = AgentConfig.from_env()
    config.refactor.apply_changes = True
    config.refactor.reflection_rounds = 1
    config.refactor.dry_run = False
    
    orchestrator = RefactorOrchestrator(config)
    analyzer = CodeAnalyzer()
    
    # Analyze and get decisions
    analysis = analyzer.analyze_project(project_path)
    contexts = analysis.to_dsl_contexts()
    
    # Get top decisions including complex ones
    top_decisions = orchestrator.dsl_engine.top_decisions(contexts, limit=5)
    
    print(f"\nTop {len(top_decisions)} decisions:")
    for i, d in enumerate(top_decisions, 1):
        print(f"{i}. {d.action.value:20s} {d.target_file:40s} score={d.score:.2f} should_execute={d.should_execute}")
    
    # Try to execute the first complex decision
    complex_decision = None
    for d in top_decisions:
        if d.action not in [
            RefactorAction.REMOVE_UNUSED_IMPORTS,
            RefactorAction.FIX_MODULE_EXECUTION_BLOCK,
            RefactorAction.EXTRACT_CONSTANTS,
            RefactorAction.ADD_RETURN_TYPES,
        ]:
            complex_decision = d
            break
    
    if not complex_decision:
        print("\nNo complex decisions found to test!")
        return
    
    print(f"\nExecuting complex decision: {complex_decision.action.value}")
    print(f"Target: {complex_decision.target_file}")
    print(f"Context: {complex_decision.context}")
    
    try:
        result = _execute_decision(orchestrator, complex_decision, project_path)
        print(f"\nResult:")
        print(f"  Applied: {result.applied}")
        print(f"  Validated: {result.validated}")
        print(f"  Errors: {result.errors}")
        if result.proposal:
            print(f"  Proposal summary: {result.proposal.summary}")
            print(f"  Confidence: {result.proposal.confidence}")
    except Exception as e:
        print(f"\nException during execution: {e}")
        import traceback
        traceback.print_exc()
    
    # Check LLM stats
    stats = get_memory_stats(orchestrator)
    print(f"\nLLM calls made: {stats.get('total_llm_calls', 0)}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python test_llm_execution.py <project_path>")
        sys.exit(1)
    
    test_llm_execution(Path(sys.argv[1]))
