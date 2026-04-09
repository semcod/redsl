# ReDSL Example 04: Memory and Learning System

This example demonstrates the three-layer memory system used by the ReDSL agent.

## Memory Layers

### 1. Episodic Memory
Stores the history of actions taken by the agent:
- What action was performed
- On which target (file/function)
- The result (success/failure)
- Time spent and other details

### 2. Semantic Memory
Stores learned patterns and lessons:
- What refactoring patterns work well
- Context for when patterns are effective
- Effectiveness ratings

### 3. Procedural Memory
Stores reusable strategies:
- Step-by-step refactoring strategies
- Tags for categorization
- Best practices for common scenarios

## Running the Example

```bash
cd examples/04-memory-learning
python main.py
```

## Example Output

The example demonstrates:
1. Recording 4 different refactoring actions
2. Learning 3 patterns from experience
3. Storing 2 reusable strategies
4. Recalling similar actions and patterns
5. Displaying memory statistics

## Key Functions

- `remember_action()` — Store an action in episodic memory
- `learn_pattern()` — Store a pattern in semantic memory
- `store_strategy()` — Store a strategy in procedural memory
- `recall_similar_actions()` — Find similar past actions
- `recall_patterns()` — Find relevant patterns
- `recall_strategies()` — Find applicable strategies

## Note

This example uses in-memory storage (no ChromaDB required).
