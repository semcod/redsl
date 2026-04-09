# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Analyzer**: Fixed false positive unused import detection for submodule imports like `import urllib.request` used as `urllib.request.urlopen()` — now correctly detects usage via attribute chain
- **Guard Refactorer**: Fixed `fix_module_execution_block` wrapping FastAPI/Flask configuration calls (e.g., `app.add_middleware()`, `app.include_router()`) in `__main__` guard — now skips config methods

### Test
- Add regression tests in `tests/test_direct_bugs_and_bridges.py`:
  - `TestQualityVisitorSubmoduleImports` (3 tests): Verify submodule imports are not falsely reported as unused
  - `TestDirectGuardConfigSkip` (4 tests): Verify FastAPI/Flask config calls are not wrapped in `__main__` guard

### Docs
- Update README.md with the current 2026-04-09 analysis snapshot and hotspot priorities
- Update README_EN.md with the current 2026-04-09 analysis snapshot and hotspot priorities
- Update TODO.md with the current backlog priorities

## [1.2.24] - 2026-04-09

### Docs
- Update README.md

### Test
- Update tests/test_direct_bugs_and_bridges.py

### Other
- Update redsl/project/analysis.toon.yaml
- Update redsl/project/batch_1/analysis.toon.yaml
- Update redsl/project/root/analysis.toon.yaml

## [1.2.23] - 2026-04-09

### Docs
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md
- Update redsl/project/README.md
- Update redsl/project/context.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- ... and 9 more files

## [1.2.22] - 2026-04-09

### Docs
- Update CHANGELOG.md
- Update README.md
- Update README_EN.md
- Update TODO.md
- Update docs/README.md
- Update docs/algitex-progresywna-algorytmizacja.md
- Update docs/ats-benchmark.md
- Update docs/clickmd-markdown-terminal.md
- Update docs/code2docs-automatyczna-dokumentacja.md
- Update docs/code2llm-analiza-przeplywu-kodu.md
- ... and 31 more files

### Test
- Update tests/test_autonomy.py
- Update tests/test_batch_pyqual.py
- Update tests/test_cli_refactor.py
- Update tests/test_direct_bugs_and_bridges.py

### Other
- Update examples/01-basic-analysis/advanced.yaml
- Update examples/01-basic-analysis/default.yaml
- Update examples/01-basic-analysis/main.py
- Update examples/02-custom-rules/advanced.yaml
- Update examples/02-custom-rules/default.yaml
- Update examples/02-custom-rules/main.py
- Update examples/03-full-pipeline/advanced.yaml
- Update examples/03-full-pipeline/default.yaml
- Update examples/03-full-pipeline/main.py
- Update examples/04-memory-learning/advanced.yaml
- ... and 51 more files

## [1.2.21] - 2026-04-09

### Docs
- Update CHANGELOG.md
- Update README.md
- Update docs/README.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/duplication.toon.yaml
- Update project/index.html
- Update project/map.toon.yaml
- Update redsl/project/analysis.toon.yaml
- Update redsl/project/batch_1/analysis.toon.yaml
- Update redsl/project/root/analysis.toon.yaml
- Update requirements.txt

## [1.2.20] - 2026-04-09

### Added
- **Markdown Report Generation** - Automatic Markdown reports for refactor and batch commands:
  - `redsl_refactor_plan.md` — dry-run output saved next to project
  - `redsl_refactor_report.md` — executed refactor cycle report
  - `redsl_batch_semcod_report.md` — batch summary for `batch semcod`
  - `redsl_batch_hybrid_report.md` — batch summary for `batch hybrid`
- **Formatter Module** - New `redsl/formatters.py` with Markdown generation functions
  - `format_cycle_report_markdown()` — Format refactor cycle as Markdown
  - `format_batch_report_markdown()` — Format batch run as Markdown

### Changed
- **Batch Persistence** - All batch runs now persist Markdown reports to disk
- **Report Structure** - Reports include summary, decisions, and file changes

### Test
- **test_tier3.py** - Added tests for Markdown report creation and batch persistence

### Docs
- Update README.md with Markdown report documentation
- Update README_EN.md with Markdown report documentation
- Update docs/README.md (auto-generated)
- Update project documentation files

### Other
- Update project analysis artifacts (toon.yaml, diagrams)

## [1.2.19] - 2026-04-08

### Docs
- Update README.md
- Update redsl/project/context.md

### Other
- Update redsl/project/analysis.toon.yaml
- Update redsl/project/batch_1/analysis.toon.yaml
- Update redsl/project/root/analysis.toon.yaml

## [1.2.18] - 2026-04-08

### Docs
- Update README.md
- Update redsl/project/README.md
- Update redsl/project/context.md

### Test
- Update tests/test_api.py
- Update tests/test_bridges.py
- Update tests/test_tier3.py

### Other
- Update redsl/autonomy/auto_fix.py
- Update redsl/autonomy/intent.py
- Update redsl/cli.py
- Update redsl/commands/cli_autonomy.py
- Update redsl/commands/cli_awareness.py
- Update redsl/commands/cli_doctor.py
- Update redsl/execution/cycle.py
- Update redsl/llm/llx_router.py
- Update redsl/project/analysis.toon.yaml
- Update redsl/project/batch_1/analysis.toon.yaml
- ... and 3 more files

## [1.2.17] - 2026-04-08

### Docs
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md
- Update redsl/project/README.md
- Update redsl/project/context.md

### Test
- Update tests/test_autonomy.py

### Other
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- ... and 16 more files

## [1.2.16] - 2026-04-08

### Docs
- Update README.md

### Other
- Update redsl/analyzers/radon_analyzer.py
- Update redsl/project/analysis.toon.yaml

## [1.2.15] - 2026-04-08

### Docs
- Update README.md
- Update redsl/project/README.md
- Update redsl/project/context.md

### Test
- Update tests/test_doctor.py

### Other
- Update project/analysis.toon.yaml
- Update project/evolution.toon.yaml
- Update project/project.toon.yaml
- Update redsl/api.py
- Update redsl/commands/doctor.py
- Update redsl/project/analysis.toon.yaml

## [1.2.14] - 2026-04-08

### Docs
- Update README.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md
- Update redsl/project/README.md
- Update redsl/project/context.md

### Test
- Update tests/test_integration.py

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- ... and 9 more files

## [1.2.13] - 2026-04-08

### Docs
- Update README.md
- Update README_EN.md
- Update TODO.md
- Update redsl/project/README.md
- Update redsl/project/context.md

### Test
- Update tests/test_awareness.py
- Update tests/test_config_loading.py

### Other
- Update examples/03-full-pipeline/main.py
- Update redsl/awareness/__init__.py
- Update redsl/cli.py
- Update redsl/config.py
- Update redsl/llm/__init__.py
- Update redsl/project/analysis.toon.yaml

## [1.2.12] - 2026-04-08

### Docs
- Update README.md

### Test
- Update tests/test_cli_refactor.py

### Other
- Update examples/03-full-pipeline/main.py
- Update project/evolution.toon.yaml
- Update redsl/awareness/__init__.py
- Update redsl/cli.py
- Update redsl/execution/cycle.py
- Update redsl/execution/validation.py
- Update redsl/orchestrator.py
- Update redsl/project/analysis.toon.yaml

## [1.2.11] - 2026-04-08

### Docs
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/REFACTORING_SUMMARY_2026-04-08.md
- Update project/context.md
- Update redsl/project/README.md
- Update redsl/project/context.md

### Test
- Update tests/test_analyzer.py
- Update tests/test_awareness.py
- Update tests/test_cli_refactor.py
- Update tests/test_direct_bugs_and_bridges.py
- Update tests/test_direct_refactor.py
- Update tests/test_git_timeline.py
- Update tests/test_llm_execution.py
- Update tests/test_tier3.py

### Other
- Update examples/03-full-pipeline/main.py
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- ... and 46 more files

## [1.2.10] - 2026-04-08

### Docs
- Update README.md
- Update README_EN.md
- Update docs/README.md
- Update redsl/project/context.md

### Test
- Update tests/test_direct_bugs_and_bridges.py

### Other
- Update .code2llmignore
- Update .gitignore
- Update archive/legacy_scripts/hybrid_llm_refactor.py
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- ... and 6 more files

## [1.2.9] - 2026-04-08

### Docs
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md
- Update redsl/project/README.md
- Update redsl/project/context.md

### Test
- Update tests/test_direct_bugs_and_bridges.py

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- ... and 10 more files

## [1.2.8] - 2026-04-08

### Added
- **DirectRefactorEngine** - Silnik bezpośredniej refaktoryzacji bez LLM:
  - `REMOVE_UNUSED_IMPORTS` - usuwanie nieużywanych importów (zachowuje `__future__`, `__all__`)
  - `FIX_MODULE_EXECUTION_BLOCK` - naprawa bloków `if __name__ == "__main__"` w środku pliku
  - `EXTRACT_CONSTANTS` - ekstrakcja magic numbers do stałych
  - `ADD_RETURN_TYPES` - dodawanie `-> None` dla funkcji bez return
- **body_restorer.py** - Naprawa skradzionych ciał klas/funkcji po błędach FIX_MODULE_EXECUTION_BLOCK
- **New Bridges** - Integracja z ekosystemem semcod:
  - `regix_bridge.py` - wykrywanie regresji metryk po refaktoryzacji
  - `pyqual_bridge.py` - integracja z pyqual CLI (doctor, gates, status)
  - `planfile_bridge.py` - tworzenie ticketów planfile dla zadań refaktoryzacji
- **llx_router.py** - Inteligentny routing modeli LLM z `apply_provider_prefix()` dla LiteLLM

### Fixed
- **regix_bridge** - użycie `regix --help` zamiast `--version` w `is_available()`
- **regix_bridge** - poprawne sprawdzanie klucza `regressions` zamiast `has_regressions`
- **regix_bridge** - usunięcie nieobsługiwanego `--format json` z `diff` i `gates`
- **pyqual** - wykluczenie `.venv/`, `venv/`, `node_modules/` z analizy (11k+ files fix)
- **pyqual** - timeout=60 dla mypy/bandit, timeout=30 dla ruff
- **direct.py** - poprawne liczenie linii dla multi-line imports w `EXTRACT_CONSTANTS`

### Changed
- **Orchestrator** - pełna pętla: PERCEIVE → DECIDE → PLAN → EXECUTE → REFLECT → REMEMBER → IMPROVE
- **CLI** - wsparcie formatów `--format yaml|json|text` dla wszystkich komend

### Docs
- Aktualizacja README.md z nową architekturą i akcjami refaktoryzacji
- Aktualizacja docs/README.md (328 testów, wersja 1.2.8)

### Test
- 328 testów przechodzi (dodano testy dla bridges i DirectRefactorEngine)

## [1.2.7] - 2026-04-07

### Docs
- Update README.md
- Update redsl/project/context.md

### Other
- Update redsl/project/analysis.toon.yaml
- Update redsl/validation/regix_bridge.py

## [1.2.6] - 2026-04-07

### Docs
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md
- Update redsl/dsl/project/README.md
- Update redsl/dsl/project/context.md
- Update redsl/project/README.md
- Update redsl/project/context.md

### Test
- Update tests/test_bridges.py
- Update tests/test_chunker_and_rules.py
- Update tests/test_incremental_and_ci.py
- Update tests/test_multi_project.py
- Update tests/test_pipeline.py
- Update tests/test_tier3.py

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- ... and 25 more files

## [1.2.5] - 2026-04-07

### Docs
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Test
- Update tests/test_bootstrap.py
- Update tests/test_validation_and_diff.py

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- ... and 20 more files

## [1.2.4] - 2026-04-07

### Docs
- Update README.md
- Update docs/README.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/duplication.toon.yaml
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml
- Update redsl/analyzers/__init__.py
- Update redsl/analyzers/analyzer.py
- Update redsl/analyzers/parsers/__init__.py
- ... and 18 more files

## [1.2.3] - 2026-04-07

### Docs
- Update README.md

### Other
- Update project/validation.toon.yaml

## [1.2.2] - 2026-04-07

### Docs
- Update README.md
- Update docs/README.md
- Update project/context.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml

## [1.2.1] - 2026-04-07

### Docs
- Update CHANGELOG.md
- Update README.md
- Update README_EN.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Test
- Update test_sample_project/TODO.md
- Update test_sample_project/hybrid_llm_refactor_results_direct.json
- Update test_sample_project/hybrid_llm_refactor_results_llm.json
- Update test_sample_project/planfile.yaml
- Update test_sample_project/prefact.yaml
- Update test_sample_project/sample.py
- Update tests/__pycache__/__init__.cpython-313.pyc
- Update tests/__pycache__/test_analyzer.cpython-313-pytest-8.3.5.pyc
- Update tests/__pycache__/test_dsl_engine.cpython-313-pytest-8.3.5.pyc
- Update tests/__pycache__/test_memory.cpython-313-pytest-8.3.5.pyc
- ... and 7 more files

### Other
- Update VERSION
- Update app/__pycache__/__init__.cpython-313.pyc
- Update app/analyzers/__pycache__/__init__.cpython-313.pyc
- Update app/dsl/__pycache__/__init__.cpython-313.pyc
- Update app/dsl/__pycache__/engine.cpython-313.pyc
- Update app/memory/__pycache__/__init__.cpython-313.pyc
- Update archive/legacy_scripts/apply_semcod_refactor.py
- Update archive/legacy_scripts/batch_quality_refactor.py
- Update archive/legacy_scripts/batch_refactor_semcod.py
- Update archive/legacy_scripts/debug_decisions.py
- ... and 52 more files

## [1.2.0] - 2026-04-07

### Added
- **YAML/JSON Output Support**: All CLI commands now support `--format yaml|json|text` option
- **REST API**: Complete FastAPI-based REST API mirroring CLI commands
  - POST /refactor - Run refactoring on a project
  - POST /batch/semcod - Batch refactor semcod projects
  - POST /batch/hybrid - Hybrid quality refactoring
  - GET /debug/config - Get configuration info
  - GET /debug/decisions - Get DSL decisions
  - POST /pyqual/analyze - Python code quality analysis
  - POST /pyqual/fix - Apply automatic quality fixes
  - GET /health - Health check endpoint
- **Python-dotenv Support**: Automatic loading of .env files for configuration
- **Enhanced Documentation**: Added extensive usage examples and API documentation
- **Formatter Module**: Centralized output formatting for consistent CLI and API responses

### Changed
- **CLI Structure**: Updated to use AgentConfig.from_env() for consistent configuration
- **Batch Commands**: Now support structured output formats
- **API Responses**: All endpoints return structured data matching CLI output

### Fixed
- **Import Issues**: Added python-dotenv to dependencies
- **Configuration**: Improved environment variable handling

## [1.1.0] - 2026-04-07

### Added
- **CLI Interface**: Complete command-line interface with Click
  - `redsl refactor` - Single project refactoring
  - `redsl batch semcod` - Batch processing for semcod projects
  - `redsl batch hybrid` - Hybrid quality refactoring (no LLM)
  - `redsl debug config` - Configuration debugging
  - `redsl debug decisions` - DSL decision inspection
- **Package Structure**: Converted from loose scripts to proper Python package
- **Direct Refactoring**: Four quality refactor actions without LLM dependency
  - `REMOVE_UNUSED_IMPORTS`
  - `EXTRACT_CONSTANTS`
  - `FIX_MODULE_EXECUTION_BLOCK`
  - `ADD_RETURN_TYPES`
- **CodeQualityVisitor**: AST-based detection of code quality issues
- **Batch Processing**: Support for processing multiple semcod projects
- **English Documentation**: README_EN.md for international users

### Changed
- **Module Renamed**: `app/` → `redsl/`
- **Import Statements**: All imports updated from `from app.` to `from redsl.`
- **Package Metadata**: Enhanced pyproject.toml with proper classifiers and metadata
- **Test Organization**: Moved test files to proper `tests/` directory

### Fixed
- **Import Errors**: Fixed all import statements after package restructuring
- **Indexing Bug**: Fixed `extract_constants` line indexing issue
- **Module Execution Block**: Improved detection and fixing logic
- **Return Type Inference**: Enhanced `ADD_RETURN_TYPES` with better type detection

### Deprecated
- Legacy scripts moved to `archive/legacy_scripts/`

## [1.0.7] - 2026-04-07

### Docs
- Update README.md

### Test
- Update tests/test_integration.py

### Other
- Update .gitignore
- Update app/__pycache__/__init__.cpython-313.pyc
- Update app/analyzers/__pycache__/__init__.cpython-313.pyc
- Update app/dsl/__pycache__/engine.cpython-313.pyc
- Update apply_semcod_refactor.py
- Update batch_refactor_semcod.py

## [1.0.6] - 2026-04-07

### Docs
- Update README.md

### Other
- Update app/__pycache__/__init__.cpython-313.pyc
- Update app/analyzers/__pycache__/__init__.cpython-313.pyc
- Update app/dsl/__pycache__/engine.cpython-313.pyc

## [1.0.5] - 2026-04-07

### Docs
- Update README.md

### Test
- Update tests/test_integration.py

### Other
- Update app/__pycache__/__init__.cpython-313.pyc
- Update app/analyzers/__pycache__/__init__.cpython-313.pyc

## [1.0.4] - 2026-04-07

### Docs
- Update README.md

### Other
- Update app/__pycache__/__init__.cpython-313.pyc
- Update app/analyzers/__pycache__/__init__.cpython-313.pyc

## [1.0.3] - 2026-04-07

### Docs
- Update README.md
- Update TODO.md

### Other
- Update app/__pycache__/__init__.cpython-313.pyc
- Update app/analyzers/__pycache__/__init__.cpython-313.pyc

## [1.0.2] - 2026-04-07

### Docs
- Update README.md
- Update TODO.md

### Other
- Update .gitignore
- Update app/__pycache__/__init__.cpython-313.pyc

## [1.0.1] - 2026-04-07

### Docs
- Update README.md

### Other
- Update VERSION
- Update app/__pycache__/__init__.cpython-313.pyc
- Update examples/01-basic-analysis/main.py
- Update examples/02-custom-rules/main.py
- Update examples/03-full-pipeline/main.py
- Update examples/04-memory-learning/main.py
- Update examples/05-api-integration/main.py

## [1.0.3] - 2026-04-07

### Docs
- Update README.md

### Other
- Update .gitignore
- Update app/__pycache__/__init__.cpython-313.pyc
- Update project_toon.yaml

## [1.0.2] - 2026-04-07

### Other
- Update .idea/redsl.iml
- Update app/__pycache__/__init__.cpython-313.pyc

## [1.0.1] - 2026-04-07

### Docs
- Update README.md

### Test
- Update tests/__init__.py
- Update tests/__pycache__/__init__.cpython-313.pyc
- Update tests/__pycache__/test_analyzer.cpython-313-pytest-8.3.5.pyc
- Update tests/__pycache__/test_dsl_engine.cpython-313-pytest-8.3.5.pyc
- Update tests/__pycache__/test_memory.cpython-313-pytest-8.3.5.pyc
- Update tests/test_analyzer.py
- Update tests/test_dsl_engine.py
- Update tests/test_memory.py

### Other
- Update .env.example
- Update .gitignore
- Update .idea/.gitignore
- Update Makefile
- Update app/__pycache__/__init__.cpython-313.pyc
- Update app/analyzers/__pycache__/__init__.cpython-313.pyc
- Update app/dsl/__pycache__/__init__.cpython-313.pyc
- Update app/dsl/__pycache__/engine.cpython-313.pyc
- Update app/memory/__pycache__/__init__.cpython-313.pyc
- Update config/default_rules.yaml
- ... and 1 more files

