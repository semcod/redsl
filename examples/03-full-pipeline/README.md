# ReDSL Example 03: Full Refactoring Pipeline

This example demonstrates the complete refactoring cycle: PERCEIVE → DECIDE → PLAN → EXECUTE → REFLECT → REMEMBER.

## The Pipeline

```
PERCEIVE  → Analyze code and toon.yaml metrics
DECIDE    → DSL engine selects refactoring actions
PLAN      → LLM generates refactoring proposals
EXECUTE   → Apply changes (dry-run mode)
REFLECT   → Validate results
REMEMBER  → Store outcomes in agent memory
```

## Prerequisites

- **OPENAI_API_KEY** environment variable (or other LLM provider)
- Python 3.10+
- ReDSL installed with all dependencies

## Running the Example

```bash
# With OpenAI (default: gpt-5.4-mini)
export OPENAI_API_KEY=your_key_here
cd examples/03-full-pipeline
python main.py

# With local Ollama model
python main.py --model ollama/llama3
```

## Configuration

The example uses `AgentConfig` with:
- `dry_run: True` — Don't apply changes, just show proposals
- `reflection_rounds: 1` — One round of validation

## Sample Code

The example refactors a complex `process_order()` function with:
- Cyclomatic complexity: 25
- Fan-out: 10
- Deeply nested conditionals

## Output

The example produces:
- Analysis summary (cycle number, decisions, proposals)
- Generated refactoring proposals in `refactor_output/`
- Memory statistics (LLM calls, memory usage)

## Expected Results

With the sample code provided, you should see:
- Multiple refactoring proposals generated
- Functions extracted from the complex `process_order()`
- Splitting recommendations for god modules
