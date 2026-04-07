<!-- code2docs:start --># redsl

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.11-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-208-green)
> **208** functions | **44** classes | **40** files | CC̄ = 5.1

> Auto-generated project documentation from source code analysis.

**Author:** ReDSL Team  
**License:** Apache-2.0[(LICENSE)](./LICENSE)  
**Repository:** [https://github.com/wronai/redsl](https://github.com/wronai/redsl)

## Installation

### From PyPI

```bash
pip install redsl
```

### From Source

```bash
git clone https://github.com/wronai/redsl
cd redsl
pip install -e .
```

### Optional Extras

```bash
pip install redsl[dev]    # development tools
```

## Quick Start

### CLI Usage

```bash
# Generate full documentation for your project
redsl ./my-project

# Only regenerate README
redsl ./my-project --readme-only

# Preview what would be generated (no file writes)
redsl ./my-project --dry-run

# Check documentation health
redsl check ./my-project

# Sync — regenerate only changed modules
redsl sync ./my-project
```

### Python API

```python
from redsl import generate_readme, generate_docs, Code2DocsConfig

# Quick: generate README
generate_readme("./my-project")

# Full: generate all documentation
config = Code2DocsConfig(project_name="mylib", verbose=True)
docs = generate_docs("./my-project", config=config)
```

## Generated Output

When you run `redsl`, the following files are produced:

```
<project>/
├── README.md                 # Main project README (auto-generated sections)
├── docs/
│   ├── api.md               # Consolidated API reference
│   ├── modules.md           # Module documentation with metrics
│   ├── architecture.md      # Architecture overview with diagrams
│   ├── dependency-graph.md  # Module dependency graphs
│   ├── coverage.md          # Docstring coverage report
│   ├── getting-started.md   # Getting started guide
│   ├── configuration.md    # Configuration reference
│   └── api-changelog.md    # API change tracking
├── examples/
│   ├── quickstart.py       # Basic usage examples
│   └── advanced_usage.py   # Advanced usage examples
├── CONTRIBUTING.md         # Contribution guidelines
└── mkdocs.yml             # MkDocs site configuration
```

## Configuration

Create `redsl.yaml` in your project root (or run `redsl init`):

```yaml
project:
  name: my-project
  source: ./
  output: ./docs/

readme:
  sections:
    - overview
    - install
    - quickstart
    - api
    - structure
  badges:
    - version
    - python
    - coverage
  sync_markers: true

docs:
  api_reference: true
  module_docs: true
  architecture: true
  changelog: true

examples:
  auto_generate: true
  from_entry_points: true

sync:
  strategy: markers    # markers | full | git-diff
  watch: false
  ignore:
    - "tests/"
    - "__pycache__"
```

## Sync Markers

redsl can update only specific sections of an existing README using HTML comment markers:

```markdown
<!-- redsl:start -->
# Project Title
... auto-generated content ...
<!-- redsl:end -->
```

Content outside the markers is preserved when regenerating. Enable this with `sync_markers: true` in your configuration.

## Architecture

```
redsl/
├── project        ├── main        ├── main        ├── main        ├── hybrid_quality_refactor        ├── apply_semcod_refactor        ├── debug_llm_config        ├── hybrid_llm_refactor        ├── batch_refactor_semcod        ├── debug_decisions        ├── batch_quality_refactor    ├── consciousness_loop    ├── cli├── redsl/    ├── __main__        ├── main    ├── formatters        ├── main    ├── config        ├── pyqual        ├── hybrid        ├── batch    ├── memory/    ├── llm/        ├── engine    ├── orchestrator        ├── prompts    ├── refactors/        ├── models        ├── analyzer    ├── main        ├── direct    ├── analyzers/        ├── parsers        ├── metrics        ├── utils    ├── dsl/        ├── engine        ├── quality_visitor    ├── api```

## API Overview

### Classes

- **`ConsciousnessLoop`** — Ciągła pętla „świadomości" agenta.
- **`LLMConfig`** — Konfiguracja warstwy LLM.
- **`MemoryConfig`** — Konfiguracja systemu pamięci.
- **`AnalyzerConfig`** — Konfiguracja analizatora kodu.
- **`RefactorConfig`** — Konfiguracja silnika refaktoryzacji.
- **`AgentConfig`** — Główna konfiguracja agenta.
- **`PyQualAnalyzer`** — Python code quality analyzer.
- **`MemoryEntry`** — Pojedynczy wpis w pamięci.
- **`MemoryLayer`** — Warstwa pamięci oparta na ChromaDB.
- **`InMemoryCollection`** — Fallback gdy ChromaDB nie jest dostępne.
- **`AgentMemory`** — Kompletny system pamięci z trzema warstwami.
- **`LLMResponse`** — Odpowiedź z modelu LLM.
- **`LLMLayer`** — Warstwa abstrakcji nad LLM z obsługą:
- **`RefactorEngine`** — Silnik refaktoryzacji z pętlą refleksji.
- **`CycleReport`** — Raport z jednego cyklu refaktoryzacji.
- **`RefactorOrchestrator`** — Główny orkiestrator — „mózg" systemu.
- **`FileChange`** — Zmiana w pojedynczym pliku.
- **`RefactorProposal`** — Propozycja refaktoryzacji wygenerowana przez LLM.
- **`RefactorResult`** — Wynik zastosowania refaktoryzacji.
- **`CodeAnalyzer`** — Główny analizator kodu.
- **`DirectRefactorEngine`** — Applies simple refactorings directly via AST manipulation.
- **`ReturnTypeAdder`** — AST transformer to add return type annotations.
- **`UnusedImportRemover`** — AST transformer to remove unused imports.
- **`ToonParser`** — Parser plików toon — obsługuje wiele formatów wyjścia code2llm.
- **`CodeMetrics`** — Metryki pojedynczej funkcji/modułu.
- **`AnalysisResult`** — Wynik analizy projektu.
- **`Operator`** — —
- **`RefactorAction`** — —
- **`Condition`** — Pojedynczy warunek DSL.
- **`Rule`** — Reguła DSL: warunki → akcja z priorytetem.
- **`Decision`** — Wynik ewaluacji reguł — decyzja co refaktoryzować.
- **`DSLEngine`** — Silnik ewaluacji reguł DSL.
- **`CodeQualityVisitor`** — Detects common code quality issues in Python AST.
- **`AnalyzeRequest`** — —
- **`RefactorRequest`** — —
- **`BatchSemcodRequest`** — —
- **`BatchHybridRequest`** — —
- **`DebugConfigRequest`** — —
- **`DebugDecisionsRequest`** — —
- **`PyQualAnalyzeRequest`** — —
- **`PyQualFixRequest`** — —
- **`RulesRequest`** — —
- **`DecisionResponse`** — —
- **`CycleResponse`** — —

### Functions

- `example_curl_commands()` — Wydrukuj przykładowe komendy curl.
- `example_python_client()` — Przykład klienta Python z httpx.
- `example_websocket()` — Przykład klienta WebSocket.
- `main()` — —
- `main()` — —
- `main()` — —
- `apply_all_quality_changes(project_path, max_changes)` — Apply ALL quality refactorings to a project without LLM.
- `main()` — Process semcod projects with hybrid refactoring.
- `main()` — Apply reDSL to a semcod project.
- `debug_llm()` — Debug LLM configuration.
- `apply_changes_with_llm_supervision(project_path, max_changes, enable_llm, validate_direct_changes)` — Apply refactorings with optional LLM supervision.
- `main()` — Process semcod projects with hybrid refactoring.
- `apply_refactor(project_path, max_actions)` — Apply reDSL to a project and return the report.
- `measure_todo_reduction(project_path)` — Measure TODO.md before and after refactoring.
- `main()` — Process semcod projects.
- `debug_decisions(project_path)` — Show all decisions generated for a project.
- `apply_quality_refactors(project_path)` — Apply all quality refactorings to a project.
- `main()` — Process semcod projects.
- `main_loop()` — Punkt wejścia dla pętli ciągłej.
- `cli(verbose)` — reDSL - Automated code refactoring tool.
- `refactor(project_path, max_actions, dry_run, format)` — Run refactoring on a project.
- `batch()` — Batch refactoring commands.
- `batch_semcod(semcod_root, max_actions, format)` — Apply refactoring to semcod projects.
- `batch_hybrid(semcod_root, max_changes)` — Apply hybrid quality refactorings (no LLM needed).
- `pyqual()` — Python code quality analysis commands.
- `pyqual_analyze(project_path, config, format)` — Analyze Python code quality.
- `pyqual_fix(project_path, config)` — Apply automatic quality fixes.
- `debug()` — Debug and diagnostic commands.
- `debug_config(show_env)` — Debug configuration loading.
- `debug_decisions(project_path, limit)` — Debug DSL decision making.
- `main()` — —
- `format_refactor_plan(decisions, format, analysis)` — Format refactoring plan in specified format.
- `format_batch_results(results, format)` — Format batch processing results.
- `format_debug_info(info, format)` — Format debug information.
- `main()` — —
- `run_pyqual_analysis(project_path, config_path, output_format)` — Run pyqual analysis on a project.
- `run_pyqual_fix(project_path, config_path)` — Run automatic fixes based on pyqual analysis.
- `run_hybrid_quality_refactor(project_path, max_changes)` — Apply ALL quality refactorings to a project without LLM.
- `run_hybrid_batch(semcod_root, max_changes)` — Run hybrid refactoring on all semcod projects.
- `run_semcod_batch(semcod_root, max_actions)` — Run batch refactoring on semcod projects.
- `apply_refactor(project_path, max_actions)` — Apply reDSL to a project and return the report.
- `measure_todo_reduction(project_path)` — Measure TODO.md before and after refactoring.
- `cmd_analyze(project_dir)` — Analiza projektu — wyświetl metryki i alerty.
- `cmd_explain(project_dir)` — Wyjaśnij decyzje refaktoryzacji bez ich wykonywania.
- `cmd_refactor(project_dir, dry_run, auto, max_actions)` — Uruchom cykl refaktoryzacji.
- `cmd_memory_stats()` — Statystyki pamięci agenta.
- `cmd_serve(port, host)` — Uruchom serwer API.
- `main()` — Główny punkt wejścia CLI.
- `create_app()` — Tworzenie aplikacji FastAPI.


## Project Structure

📄 `archive.legacy_scripts.apply_semcod_refactor` (1 functions)
📄 `archive.legacy_scripts.batch_quality_refactor` (2 functions)
📄 `archive.legacy_scripts.batch_refactor_semcod` (3 functions)
📄 `archive.legacy_scripts.debug_decisions` (1 functions)
📄 `archive.legacy_scripts.debug_llm_config` (1 functions)
📄 `archive.legacy_scripts.hybrid_llm_refactor` (2 functions)
📄 `archive.legacy_scripts.hybrid_quality_refactor` (2 functions)
📄 `examples.01-basic-analysis.main` (1 functions)
📄 `examples.02-custom-rules.main` (1 functions)
📄 `examples.03-full-pipeline.main` (1 functions)
📄 `examples.04-memory-learning.main` (1 functions)
📄 `examples.05-api-integration.main` (4 functions)
📄 `project`
📦 `redsl`
📄 `redsl.__main__`
📦 `redsl.analyzers`
📄 `redsl.analyzers.analyzer` (20 functions, 1 classes)
📄 `redsl.analyzers.metrics` (2 functions, 2 classes)
📄 `redsl.analyzers.parsers` (22 functions, 1 classes)
📄 `redsl.analyzers.quality_visitor` (14 functions, 1 classes)
📄 `redsl.analyzers.utils` (3 functions)
📄 `redsl.api` (1 functions, 11 classes)
📄 `redsl.cli` (11 functions)
📄 `redsl.commands.batch` (3 functions)
📄 `redsl.commands.hybrid` (2 functions)
📄 `redsl.commands.pyqual` (14 functions, 1 classes)
📄 `redsl.config` (1 functions, 5 classes)
📄 `redsl.consciousness_loop` (6 functions, 1 classes)
📦 `redsl.dsl`
📄 `redsl.dsl.engine` (12 functions, 6 classes)
📄 `redsl.formatters` (10 functions)
📦 `redsl.llm` (4 functions, 2 classes)
📄 `redsl.main` (15 functions)
📦 `redsl.memory` (18 functions, 4 classes)
📄 `redsl.orchestrator` (9 functions, 2 classes)
📦 `redsl.refactors`
📄 `redsl.refactors.direct` (14 functions, 3 classes)
📄 `redsl.refactors.engine` (7 functions, 1 classes)
📄 `redsl.refactors.models` (3 classes)
📄 `redsl.refactors.prompts`

## Requirements

- Python >= >=3.11
- fastapi >=0.110.0- uvicorn >=0.27.0- pydantic >=2.6.0- litellm >=1.30.0- chromadb >=0.4.22- pyyaml >=6.0.1- rich >=13.7.0- httpx >=0.27.0- click >=8.1.0- python-dotenv >=1.0.0- goal >=2.1.0- costs >=0.1.20- pfix >=0.1.60

## Contributing

**Contributors:**
- Tom Softreck <tom@sapletta.com>
- Tom Sapletta <tom-sapletta-com@users.noreply.github.com>

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/wronai/redsl
cd redsl

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Documentation

- 📖 [Full Documentation](https://github.com/wronai/redsl/tree/main/docs) — API reference, module docs, architecture
- 🚀 [Getting Started](https://github.com/wronai/redsl/blob/main/docs/getting-started.md) — Quick start guide
- 📚 [API Reference](https://github.com/wronai/redsl/blob/main/docs/api.md) — Complete API documentation
- 🔧 [Configuration](https://github.com/wronai/redsl/blob/main/docs/configuration.md) — Configuration options
- 💡 [Examples](./examples) — Usage examples and code samples

### Generated Files

| Output | Description | Link |
|--------|-------------|------|
| `README.md` | Project overview (this file) | — |
| `docs/api.md` | Consolidated API reference | [View](./docs/api.md) |
| `docs/modules.md` | Module reference with metrics | [View](./docs/modules.md) |
| `docs/architecture.md` | Architecture with diagrams | [View](./docs/architecture.md) |
| `docs/dependency-graph.md` | Dependency graphs | [View](./docs/dependency-graph.md) |
| `docs/coverage.md` | Docstring coverage report | [View](./docs/coverage.md) |
| `docs/getting-started.md` | Getting started guide | [View](./docs/getting-started.md) |
| `docs/configuration.md` | Configuration reference | [View](./docs/configuration.md) |
| `docs/api-changelog.md` | API change tracking | [View](./docs/api-changelog.md) |
| `CONTRIBUTING.md` | Contribution guidelines | [View](./CONTRIBUTING.md) |
| `examples/` | Usage examples | [Browse](./examples) |
| `mkdocs.yml` | MkDocs configuration | — |

<!-- code2docs:end -->