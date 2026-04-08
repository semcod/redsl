# ReDSL

**Re**factor + **DSL** + **S**elf-**L**earning — autonomous code refactoring with LLM, memory, and DSL.

ReDSL is a code refactoring system that combines static analysis, DSL rules, and LLM intelligence to automatically improve Python code quality.

## Features

- 🔍 **Static Analysis** - Integration with popular linters and metrics tools
- 🧠 **LLM with Reflection** - Generate refactoring proposals with self-reflection loop
- ⚡ **Hybrid Engine** - Direct refactorings for simple changes, LLM for complex ones
- 📊 **DSL Engine** - Define refactoring rules in readable YAML format
- 💾 **Memory System** - Learn from refactoring history
- 🚀 **Scalability** - Process multiple projects simultaneously

## Installation

```bash
pip install redsl
```

## Quick Start

### Basic CLI Usage

```bash
# Refactor a single project (dry run)
redsl refactor ./my-project --max-actions 5 --dry-run

# Refactor without dry run (apply changes)
redsl refactor ./my-project --max-actions 10

# Get output in YAML format (for integration)
redsl refactor ./my-project --format yaml

# Get output in JSON format (for APIs)
redsl refactor ./my-project --format json
```

### Batch Processing

```bash
# Process semcod projects with LLM
redsl batch semcod /path/to/semcod --max-actions 10

# Hybrid refactoring (no LLM) for semcod projects
redsl batch hybrid /path/to/semcod --max-changes 30

# Batch processing with JSON output
redsl batch semcod /path/to/semcod --format json
```

### Python Code Quality Analysis

```bash
# Analyze code quality
redsl pyqual analyze ./my-project

# Analyze with custom config
redsl pyqual analyze ./my-project --config pyqual.yaml

# Get analysis in JSON format
redsl pyqual analyze ./my-project --format json

# Apply automatic fixes
redsl pyqual fix ./my-project
```

### Debugging

```bash
# Check configuration
redsl debug config --show-env

# View DSL decisions for a project
redsl debug decisions ./my-project --limit 20
```

## Advanced Usage

### Using with CI/CD

```yaml
# GitHub Actions example
- name: Run reDSL analysis
  run: |
    redsl refactor ./ --max-actions 5 --dry-run --format yaml > refactor-plan.yaml
    
- name: Upload refactoring plan
  uses: actions/upload-artifact@v3
  with:
    name: refactor-plan
    path: refactor-plan.yaml
```

### Integration with Other Tools

```bash
# Use with jq for JSON processing
redsl refactor ./ --format json | jq '.refactoring_plan.decisions[] | select(.score > 1.0)'

# Pipe to file for review
redsl refactor ./ --format yaml > review-plan.yaml

# Extract only high-impact decisions
redsl refactor ./ --format yaml | yq '.refactoring_plan.decisions[] | select(.score > 1.5)'
```

### Environment Configuration

Create `.env` file:
```bash
# LLM Configuration
OPENAI_API_KEY (set in your environment)
REFACTOR_LLM_MODEL=openai/gpt-4
REFACTOR_DRY_RUN=false

# Custom settings
REFACTOR_MAX_ACTIONS=20
REFACTOR_REFLECTION_ROUNDS=2
```

## Available Refactoring Actions

### Simple Actions (no LLM)
- `REMOVE_UNUSED_IMPORTS` - Remove unused imports
- `FIX_MODULE_EXECUTION_BLOCK` - Fix module execution blocks
- `EXTRACT_CONSTANTS` - Extract magic numbers to constants
- `ADD_RETURN_TYPES` - Add return type annotations

> **Implementation note:** the deterministic AST helpers now live in `redsl/refactors/ast_transformers.py`, and `redsl.refactors` plus `redsl.refactors.direct` re-export them for backward compatibility.

### Complex Actions (with LLM)
- `EXTRACT_FUNCTIONS` - Extract high-complexity functions
- `SPLIT_MODULE` - Split large modules
- `REDUCE_COMPLEXITY` - Reduce cyclomatic complexity

## Fresh-project smoke test

To quickly verify that ReDSL runs in a brand-new project, create a tiny temporary project and run the CLI in dry-run mode:

```bash
mkdir -p /tmp/redsl-smoke
cat > /tmp/redsl-smoke/main.py <<'PY'
import os


def main() -> None:
    return None


main()
PY

python3 -m redsl analyze /tmp/redsl-smoke
python3 -m redsl refactor /tmp/redsl-smoke --dry-run --max-actions 5
```

## REST API

Start the API server:

```bash
# Using uvicorn directly
uvicorn redsl.api:app --reload --host 0.0.0.0 --port 8000

# Using the CLI
redsl api --host 0.0.0.0 --port 8000
```

### API Endpoints

#### Refactor a Project
```bash
curl -X POST "http://localhost:8000/refactor" \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "./my-project",
    "max_actions": 5,
    "dry_run": true,
    "format": "json"
  }'
```

#### Batch Processing
```bash
# Batch semcod processing
curl -X POST "http://localhost:8000/batch/semcod" \
  -H "Content-Type: application/json" \
  -d '{
    "semcod_root": "/path/to/semcod",
    "max_actions": 10,
    "format": "yaml"
  }'

# Hybrid batch processing
curl -X POST "http://localhost:8000/batch/hybrid" \
  -H "Content-Type: application/json" \
  -d '{
    "semcod_root": "/path/to/semcod",
    "max_changes": 30
  }'
```

#### Debug Endpoints
```bash
# Get configuration
curl "http://localhost:8000/debug/config?show_env=true"

# Get decisions for a project
curl "http://localhost:8000/debug/decisions?project_path=./my-project&limit=10"
```

#### Python Quality Analysis
```bash
# Analyze code quality
curl -X POST "http://localhost:8000/pyqual/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "./my-project",
    "format": "json"
  }'

# Apply fixes
curl -X POST "http://localhost:8000/pyqual/fix" \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "./my-project"
  }'
```

### Interactive API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  ORCHESTRATOR                       │
│   (loop: analyze → decide → refactor → reflect)    │
├─────────────┬──────────────┬────────────────────────┤
│  ANALYZER   │  DSL ENGINE  │   REFACTOR ENGINE      │
│  ─ toon.yaml│  ─ rules     │   ─ patch generation   │
│  ─ linters  │  ─ scoring   │   ─ validation         │
│  ─ metrics  │  ─ planning  │   ─ application        │
├─────────────┴──────────────┴────────────────────────┤
│            HYBRID REFACTOR ENGINES                  │
│  ─ DirectRefactorEngine (no LLM)                   │
│  ─ LLM RefactorEngine (with reflection)            │
├─────────────────────────────────────────────────────┤
│                  LLM LAYER (LiteLLM)                │
│   ─ code generation  ─ reflection  ─ self-critique  │
├─────────────────────────────────────────────────────┤
│                 MEMORY SYSTEM                       │
│   ─ episodic (refactoring history)                 │
│   ─ semantic (patterns, rules)                     │
│   ─ procedural (strategies, plans)                 │
└─────────────────────────────────────────────────────┘
```

## Configuration

Environment variables:
- `OPENAI_API_KEY` or `OPENROUTER_API_KEY` — API key
- `REFACTOR_LLM_MODEL` — LLM model (e.g., `openrouter/openai/gpt-5.4-mini`)
- `REFACTOR_DRY_RUN` — test mode (`true`/`false`)

## Examples

| Directory | Description |
|-----------|-------------|
| `examples/01-basic-analysis/` | Project analysis from toon.yaml files |
| `examples/02-custom-rules/` | Define custom DSL rules |
| `examples/03-full-pipeline/` | Full cycle: analyze → decide → refactor → reflect |
| `examples/04-memory-learning/` | Memory system: episodic, semantic, procedural |

## License

Apache License 2.0
