# Orchestrator.py Split Plan

## Current State
- **File**: `redsl/orchestrator.py` (688 lines)
- **Classes**: 2 (CycleReport, RefactorOrchestrator)
- **Max CC**: 11
- **Impact if split**: 7568
- **Risk**: 25 import paths may break

## Proposed Architecture

Split into 4 focused modules under `redsl/orchestrator/`:

```
redsl/orchestrator/
├── __init__.py           # Re-export RefactorOrchestrator for backward compat
├── models.py             # CycleReport dataclass
├── cycle.py              # Cycle execution logic (run_cycle, _new_cycle_report, etc.)
├── decision.py           # Decision execution (_execute_decision, _execute_direct_refactor)
├── reflection.py         # Reflection and learning (_reflect_on_cycle, _auto_learn_rules)
└── utils.py              # Utility methods (_resolve_source_path, _load_source_code)
```

## Module Responsibilities

### 1. `models.py` (30 lines)
- `CycleReport` dataclass
- Pure data structure, no logic

### 2. `cycle.py` (150 lines)
- `CycleExecutor` class
- Methods: `run_cycle()`, `run_from_toon_content()`
- `_analyze_project()`, `_summarize_analysis()`, `_select_decisions()`
- `_snapshot_regix_before()`, `_consult_memory_for_decisions()`, `_execute_decisions()`
- `_validate_with_regix()`

### 3. `decision.py` (180 lines)
- `DecisionExecutor` class
- `_execute_decision()` - main decision execution
- `_execute_direct_refactor()` - direct refactoring without LLM
- `_resolve_source_path()` - file path resolution
- `_load_source_code()` - source loading with SemanticChunker
- `_resolve_target_function()` - function detection
- `_consult_memory()` - memory consultation
- `_remember_decision_result()` - result storage

### 4. `reflection.py` (100 lines)
- `ReflectionEngine` class
- `_reflect_on_cycle()` - cycle-level reflection
- `_auto_learn_rules()` - DSL rule generation from memory

### 5. `utils.py` (50 lines)
- `OrchestratorUtils` class (optional, could be module-level functions)
- Shared helper methods

### 6. `__init__.py` (80 lines)
- Main `RefactorOrchestrator` class (orchestrates the sub-components)
- Public API: `explain_decisions()`, `get_memory_stats()`, `estimate_cycle_cost()`
- `execute_sandboxed()`, `add_custom_rules()`
- Maintains backward compatibility

## Import Migration Strategy

### Current imports that need updating:
```python
# Current (in other files)
from redsl.orchestrator import RefactorOrchestrator
```

### New imports (backward compatible):
```python
# In __init__.py
from .cycle import CycleExecutor
from .decision import DecisionExecutor
from .reflection import ReflectionEngine
from .models import CycleReport

class RefactorOrchestrator:
    def __init__(self, config: AgentConfig | None = None) -> None:
        self._cycle = CycleExecutor(self)
        self._decision = DecisionExecutor(self)
        self._reflection = ReflectionEngine(self)
        # ... existing initialization
```

### Benefits:
1. **No breaking changes** - existing imports continue to work
2. **Testable components** - each module independently testable
3. **Single responsibility** - each module has clear purpose
4. **Reduced CC** - each module will have CC < 10

## Migration Steps (Incremental)

### Phase 1: Create new modules (no behavior change)
1. Create `orchestrator/` directory
2. Move `CycleReport` to `models.py`
3. Extract methods to respective modules
4. Keep `orchestrator.py` as facade that delegates to new modules

### Phase 2: Update internal references
1. Change `orchestrator.py` to import from submodules
2. Maintain all public methods as pass-through calls

### Phase 3: Clean up (optional)
1. Once verified stable, can move `orchestrator.py` to `orchestrator/__init__.py`
2. Update documentation

## Risk Mitigation

1. **25 import paths** - No changes to public API, only internal refactoring
2. **Test coverage** - All 330 existing tests must pass
3. **Gradual rollout** - Can be done incrementally module by module
4. **Backup plan** - Can revert by restoring single `orchestrator.py`

## Estimated Effort: 4 hours

## Impact after completion:
- Max CC per module: < 10
- Total orchestrator lines: 688 → distributed across modules
- God module eliminated
- Easier maintenance and testing
