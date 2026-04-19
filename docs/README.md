---
path: /home/tom/github/semcod/redsl
---

<!-- code2docs:start --># ReDSL

![version](https://img.shields.io/badge/version-1.2.30-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.11-blue) ![tests](https://img.shields.io/badge/tests-571%20passing-green) ![e2e](https://img.shields.io/badge/e2e-18%20tests-green)
> **Re**factor + **DSL** + **S**elf-**L**earning — Autonomiczny System Refaktoryzacji Kodu

> **781** functions | **112** classes | **114** files | CC̄ = 4.1 | **19 151** LOC

> Aktualna analiza: 2026-04-19 | Hotspoty krytyczne: 3 | Duplikacje/cykle: 0/0

**Author:** ReDSL Team  
**License:** Apache-2.0[(LICENSE)](./LICENSE)  
**Repository:** [https://github.com/semcod/redsl](https://github.com/semcod/redsl)

## Installation

### From PyPI

```bash
pip install redsl
```

### From Source

```bash
git clone https://github.com/semcod/redsl
cd redsl
pip install -e .
```

### Optional Extras

```bash
pip install redsl[dev]    # development tools
```

## Quick Start

### CLI Usage — Refaktoryzacja

```bash
# Analiza projektu (dry-run)
redsl refactor ./my-project --dry-run --max-actions 10

# Wykonaj refaktoryzację
redsl refactor ./my-project --max-actions 5

# Hybrydowa refaktoryzacja (bez LLM — szybka)
redsl batch hybrid /path/to/semcod --max-changes 50

# Pełna refaktoryzacja z LLM i refleksją
redsl batch semcod /path/to/semcod --max-actions 10

# Sprawdź jakość kodu
redsl pyqual analyze ./my-project --format yaml

# Automatyczne naprawy jakościowe
redsl pyqual fix ./my-project

# Uruchom serwer API
redsl server --host 0.0.0.0 --port 8000

# Zobacz decyzje DSL
redsl debug decisions ./my-project --limit 20
```

### Python API

```python
from redsl.orchestrator import RefactorOrchestrator
from redsl.config import AgentConfig

# Inicjalizacja orkiestratora
config = AgentConfig.from_env()
orchestrator = RefactorOrchestrator(config)

# Uruchom cykl refaktoryzacji
report = orchestrator.run_cycle(
    project_dir="./my-project",
    max_actions=5,
    dry_run=True
)

# Analiza bez refaktoryzacji
analysis = orchestrator.analyzer.analyze_project("./my-project")
print(f"Znaleziono {len(analysis.issues)} problemów")
```

## Generated Output

ReDSL generuje raporty i historię zmian podczas refaktoryzacji:

```
<project>/
├── .redsl/
│   └── history.jsonl        # Historia decyzji i zdarzeń (append-only)
├── redsl_refactor_plan.md   # Plan refaktoryzacji (dry-run)
├── redsl_refactor_report.md # Raport wykonanej refaktoryzacji
├── redsl_pyqual_report.md   # Raport analizy jakości (pyqual)
└── redsl_batch_semcod_report.md  # Raport batch semcod
```

Każdy raport zawiera:
- Szczegółowy plan zmian
- Metryki przed/po (CC, LOC, pokrycie)
- Decyzje DSL z uzasadnieniem
- Refleksję LLM nad zmianami
- Walidację regresji (regix)

## Configuration

Create `redsl.yaml` in your project root (or run `redsl init`):

```yaml
project:
  name: my-project
  source: ./
  output: ./docs/

# Reguły refaktoryzacji DSL
rules:
  - name: high_complexity
    condition: cyclomatic_complexity > 15
    action: EXTRACT_FUNCTIONS
    priority: 0.9
  
  - name: unused_imports
    condition: unused_import_count > 5
    action: REMOVE_UNUSED_IMPORTS
    priority: 0.8
  
  - name: long_function
    condition: function_lines > 50
    action: SPLIT_FUNCTION
    priority: 0.7

# Wykluczenia z analizy
exclude:
  - .venv/
  - venv/
  - node_modules/
  - .git/
  - tests/
  - __pycache__/
```

## Ecosystem Bridges

ReDSL integruje się z ekosystemem semcod:

| Narzędzie | Bridge | Funkcja |
|-----------|--------|---------|
| `code2llm` | `code2llm_bridge.py` | Generowanie plików toon.yaml z metrykami |
| `regix` | `regix_bridge.py` | Wykrywanie regresji metryk po refaktoryzacji |
| `pyqual` | `pyqual_bridge.py` | Analiza jakości kodu (ruff, mypy, bandit) |
| `planfile` | `planfile_bridge.py` | Tworzenie ticketów dla refactoring tasks |
| `vallm` | `vallm_bridge.py` | Walidacja poprawności kodu przez LLM |
| `redup` | `redup_bridge.py` | Detekcja duplikacji kodu |
| `testql` | `testql_bridge.py` | Post-refactoring API validation |
| `metrun` | `perf_bridge.py` | Profilowanie wydajności |

## Transparency (Przezroczystość)

ReDSL zapewnia pełną przezroczystość procesu decyzyjnego:

### CLI
```bash
# Zobacz decyzje DSL
redsl debug decisions ./my-project --limit 20

# Sprawdź konfigurację
redsl debug config --show-env

# Historia decyzji
cat ./my-project/.redsl/history.jsonl | jq '.'
```

### API
```bash
curl "http://localhost:8000/debug/decisions?project_path=./my-project&limit=20"
curl "http://localhost:8000/debug/config?show_env=true"
```

### Struktura historii (.redsl/history.jsonl)
Każda linia to JSON z polami:
- `event_type`: decision, reflection, execution, ticket_created
- `decision_rule`: nazwa reguły DSL
- `target_file`: plik docelowy
- `action`: podjęta akcja
- `score`: priorytet decyzji
- `thought`: uzasadnienie
- `reflection`: auto-krytyka LLM
- `outcome_reason`: rezultat wykonania

## Architecture

### Pętla świadomości (Consciousness Loop)

```
┌─────────────────────────────────────────────────────────────────┐
│                     REFACTOR ORCHESTRATOR                       │
│         PERCEIVE → DECIDE → PLAN → EXECUTE → REFLECT            │
│                    ↓                    ↓                       │
│              REMEMBER → IMPROVE (auto-learning)                 │
├─────────────────┬───────────────────┬───────────────────────────┤
│    ANALYZER     │    DSL ENGINE     │     REFACTOR ENGINES      │
│  ─ toon.yaml    │  ─ rule scoring   │  ┌─────────────────────┐  │
│  ─ code2llm     │  ─ decisions      │  │ DirectRefactorEngine│  │
│  ─ linters      │  ─ auto-learning  │  │ (bez LLM)           │  │
│  ─ redup        │                   │  ├─────────────────────┤  │
│                 │                   │  │ LLM RefactorEngine  │  │
│                 │                   │  │ (z refleksją)       │  │
│                 │                   │  └─────────────────────┘  │
├─────────────────┴───────────────────┴───────────────────────────┤
│                     VALIDATION LAYER                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ regix       │  │ vallm       │  │ sandbox (Docker)        │  │
│  │ (regression)│  │ (pactfix)   │  │ (bezpieczne testowanie) │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                     ECOSYSTEM BRIDGES                           │
│  code2llm │ regix │ pyqual │ planfile │ vallm │ redup │ llx     │
├─────────────────────────────────────────────────────────────────┤
│                     LLM LAYER (LiteLLM)                         │
│  ─ model routing (llx_router)  ─ cost estimation  ─ reflection  │
├─────────────────────────────────────────────────────────────────┤
│                     MEMORY SYSTEM                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐      │
│  │ episodic    │  │ semantic    │  │ procedural          │      │
│  │ (historia)  │  │ (wzorce)    │  │ (strategie)         │      │
│  └─────────────┘  └─────────────┘  └─────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### Struktura katalogów

```
redsl/
├── redsl/
│   ├── analyzers/       # Analiza kodu, metryki, code2llm/redup bridge
│   ├── commands/        # Komendy CLI: batch, pyqual, planfile bridge
│   ├── dsl/             # Silnik reguł DSL i scoring
│   ├── llm/             # Warstwa LLM (LiteLLM) + llx router
│   ├── memory/          # System pamięci (3 warstwy)
│   ├── refactors/       # Silniki: Direct + LLM + body_restorer
│   ├── validation/      # regix, vallm, test_runner, sandbox
│   ├── diagnostics/     # Profilowanie: perf_bridge (metrun)
│   ├── orchestrator.py  # Główny koordynator pipeline
│   ├── cli.py           # Punkt wejścia CLI
│   └── config.py        # AgentConfig, LLMConfig
├── tests/               # 571 testów (533 fast + 18 e2e + 20 integration)
├── examples/            # 10 przykładów użycia
├── config/              # Domyślna konfiguracja reguł DSL
└── pyproject.toml       # Packaging i zależności
```

## API Overview

### Classes

- **`ConsciousnessLoop`** — Ciągła pętla „świadomości" agenta.
- **`HistoryEvent`** — A single persisted event in the refactor history.
- **`HistoryWriter`** — Append-only history logger backed by .redsl/history.jsonl.
- **`HistoryReader`** — Read-only access to .redsl/history.jsonl for querying and dedup.
- **`LLMConfig`** — Konfiguracja warstwy LLM.
- **`MemoryConfig`** — Konfiguracja systemu pamięci.
- **`AnalyzerConfig`** — Konfiguracja analizatora kodu.
- **`RefactorConfig`** — Konfiguracja silnika refaktoryzacji.
- **`AgentConfig`** — Główna konfiguracja agenta.
- **`ProjectScanResult`** — Scan result for a single project.
- **`ProjectAnalysis`** — Wyniki analizy pojedynczego projektu.
- **`MultiProjectReport`** — Zbiorczy raport z analizy wielu projektów.
- **`MultiProjectRunner`** — Uruchamia ReDSL na wielu projektach.
- **`Issue`** — A single detected issue.
- **`DoctorReport`** — Aggregated report for one project.
- **`PyqualProjectResult`** — Result of pyqual pipeline for a single project.
- **`ProjectContext`** — Mutable context passed through pipeline stages.
- **`FileChange`** — Zmiana w pojedynczym pliku.
- **`RefactorProposal`** — Propozycja refaktoryzacji wygenerowana przez LLM.
- **`RefactorResult`** — Wynik zastosowania refaktoryzacji.
- **`ProjectFixResult`** — Result of autofix processing for a single project.
- **`RuffAnalyzer`** — Uruchamia ruff i zbiera wyniki.
- **`MypyAnalyzer`** — Uruchamia mypy i zbiera wyniki.
- **`Reporter`** — Generuje rekomendacje i zapisuje raporty analizy jakości.
- **`BanditAnalyzer`** — Uruchamia bandit i zbiera wyniki bezpieczeństwa.
- **`PyQualAnalyzer`** — Python code quality analyzer — fasada nad wyspecjalizowanymi analizatorami.
- **`AstAnalyzer`** — Analizuje pliki Python przez AST w poszukiwaniu typowych problemów jakości.
- **`Bottleneck`** — —
- **`CriticalStep`** — —
- **`PerformanceReport`** — —
- **`GateVerdict`** — Result of a quality gate check.
- **`CycleReport`** — Raport z jednego cyklu refaktoryzacji.
- **`RefactorOrchestrator`** — Główny orkiestrator — „mózg" systemu.
- **`AdaptiveExecutor`** — Execute decisions while adapting strategy on repeated failures.
- **`AutonomyMetrics`** — Metrics for the autonomy subsystem.
- **`GrowthBudget`** — LOC growth budget per iteration.
- **`GrowthController`** — Enforce growth budgets on a project.
- **`ModuleBudget`** — Complexity budget for a single module.
- **`AutonomyMode`** — —
- **`Scheduler`** — Periodic quality-improvement loop.
- **`MemoryEntry`** — Pojedynczy wpis w pamięci.
- **`MemoryLayer`** — Warstwa pamięci oparta na ChromaDB.
- **`InMemoryCollection`** — Fallback gdy ChromaDB nie jest dostępne.
- **`AgentMemory`** — Kompletny system pamięci z trzema warstwami.
- **`AutoFixResult`** — Outcome of the auto-fix pipeline.
- **`LLMResponse`** — Odpowiedź z modelu LLM.
- **`LLMLayer`** — Warstwa abstrakcji nad LLM z obsługą:
- **`DirectTypesRefactorer`** — Handles return type annotation addition.
- **`ModelSelection`** — —
- **`DirectGuardRefactorer`** — Handles main guard wrapping for module-level execution code.
- **`DirectRefactorEngine`** — Applies simple refactorings directly via AST manipulation.
- **`RefactorEngine`** — Silnik refaktoryzacji z pętlą refleksji.
- **`DirectImportRefactorer`** — Handles import-related direct refactoring.
- **`FileChange`** — Zmiana w pojedynczym pliku.
- **`RefactorProposal`** — Propozycja refaktoryzacji wygenerowana przez LLM.
- **`RefactorResult`** — Wynik zastosowania refaktoryzacji.
- **`WorkflowConfig`** — Konfiguracja generowanego workflow.
- **`DirectConstantsRefactorer`** — Handles magic number to constant extraction.
- **`GitTimelineAnalyzer`** — Build a historical metric timeline from git commits — facade.
- **`ProjectNode`** — Single project node in the ecosystem graph.
- **`EcosystemGraph`** — Basic ecosystem graph for semcod-style project collections.
- **`GitTimelineProvider`** — Provides git-based timeline data.
- **`ToonCollector`** — Collects and processes toon files from git history.
- **`AwarenessSnapshot`** — Compact overview of the current awareness state for a project.
- **`AwarenessManager`** — Facade that combines all awareness layers into one snapshot.
- **`ProactiveAlert`** — A proactive issue detected from trends.
- **`ProactiveAnalyzer`** — Turn trend forecasts into alerts and suggested interventions.
- **`TimelineAnalyzer`** — Analyzes metric trends from timeline data.
- **`ChangePattern`** — A learned pattern describing a recurring change shape.
- **`ChangePatternLearner`** — Infer patterns from timeline deltas and trend transitions.
- **`CapabilityStat`** — Track how well the agent performs a capability.
- **`AgentCapabilityProfile`** — Structured self-assessment summary.
- **`SelfModel`** — Introspective model backed by agent memory.
- **`HealthDimension`** — Single health dimension with score and rationale.
- **`UnifiedHealth`** — Aggregated health snapshot.
- **`HealthModel`** — Combine timeline metrics into a single health snapshot.
- **`DockerNotFoundError`** — Raised when Docker daemon is not available.
- **`SandboxError`** — Raised for sandbox-level failures.
- **`RefactorSandbox`** — Docker sandbox do bezpiecznego testowania refaktoryzacji.
- **`TestqlVerdict`** — Validation verdict from testql scenario execution.
- **`TestqlValidator`** — Post-refactoring validator using testql scenarios.
- **`PythonAnalyzer`** — Analizator plików .py przez stdlib ast.
- **`ReturnTypeAdder`** — AST transformer to add return type annotations.
- **`UnusedImportRemover`** — AST transformer to remove unused imports.
- **`EvolutionaryCache`** — Cache wyników analizy per-plik oparty o hash pliku.
- **`IncrementalAnalyzer`** — Analizuje tylko zmienione pliki i scala z cached wynikami.
- **`SumdMetrics`** — Metrics extracted from sumd analysis.
- **`SumdAnalyzer`** — Native project analyzer using sumd extractor patterns.
- **`CodeAnalyzer`** — Główny analizator kodu — fasada.
- **`CodeMetrics`** — Metryki pojedynczej funkcji/modułu.
- **`AnalysisResult`** — Wynik analizy projektu.
- **`ToonAnalyzer`** — Analizator plików toon — przetwarza dane z code2llm.
- **`SemanticChunk`** — Wycięty semantyczny fragment kodu gotowy do wysłania do LLM.
- **`SemanticChunker`** — Buduje semantyczne chunki kodu dla LLM.
- **`PathResolver`** — Resolver ścieżek i kodu źródłowego funkcji.
- **`MetricPoint`** — Single timeline point captured from a git commit.
- **`TrendAnalysis`** — Trend summary for a single metric series.
- **`TimelineSummary`** — High-level summary of a git timeline.
- **`ToonParser`** — Parser plików toon — fasada nad wyspecjalizowanymi parserami.
- **`FunctionsParser`** — Parser sekcji functions_toon — per-funkcja CC.
- **`ValidationParser`** — Parser sekcji validation_toon.
- **`ProjectParser`** — Parser sekcji project_toon.
- **`DuplicationParser`** — Parser sekcji duplication_toon.
- **`CodeQualityVisitor`** — Detects common code quality issues in Python AST.
- **`LearnedRule`** — Reguła DSL wygenerowana z wzorców w pamięci.
- **`RuleGenerator`** — Generuje nowe reguły DSL z historii refaktoryzacji w pamięci agenta.
- **`Operator`** — —
- **`RefactorAction`** — —
- **`Condition`** — Pojedynczy warunek DSL.
- **`Rule`** — Reguła DSL: warunki → akcja z priorytetem.
- **`Decision`** — Wynik ewaluacji reguł — decyzja co refaktoryzować.
- **`DSLEngine`** — Silnik ewaluacji reguł DSL.
- **`AnalyzeRequest`** — —
- **`RefactorRequest`** — —
- **`BatchSemcodRequest`** — —
- **`BatchHybridRequest`** — —
- **`DebugConfigRequest`** — —
- **`DebugDecisionsRequest`** — —
- **`PyQualAnalyzeRequest`** — —
- **`PyQualFixRequest`** — —
- **`RulesRequest`** — —
- **`ExampleRunRequest`** — —
- **`DecisionResponse`** — —
- **`CycleRequest`** — —
- **`CycleResponse`** — —

### Functions

- `main()` — —
- `main()` — —
- `main()` — —
- `main()` — —
- `main()` — —
- `main()` — —
- `main()` — —
- `main()` — —
- `main()` — Run pre-commit validation.
- `main()` — —
- `main()` — —
- `main_loop()` — Punkt wejścia dla pętli ciągłej.
- `register(cli, host_module)` — Register all awareness commands on the given Click group.
- `render_markdown(results, folder)` — Render a markdown priority report from scan results.
- `diagnose(root)` — Run all detectors on a project and return a report (no fixes applied).
- `heal(root, dry_run)` — Diagnose and fix issues in a project.
- `heal_batch(semcod_root, dry_run)` — Run doctor on all semcod subprojects.
- `is_available()` — Return True if planfile CLI is installed and functional.
- `create_ticket(project_dir, title, description, priority)` — Create a planfile ticket for a refactoring action.
- `list_tickets(project_dir, status)` — List planfile tickets, optionally filtered by status.
- `report_refactor_results(project_dir, decisions_applied, files_modified, avg_cc_before)` — Create a summary ticket for a completed refactor cycle.
- `scan_folder(folder, progress)` — Scan all sub-projects in *folder* and return sorted results.
- `fix_broken_guards(root, report)` — Use body_restorer to repair stolen class/function bodies.
- `fix_stolen_indent(root, report)` — Restore indentation for function/class bodies that lost it.
- `fix_broken_fstrings(root, report)` — Fix common broken f-string patterns.
- `fix_stale_pycache(root, report)` — Remove all __pycache__ directories.
- `fix_missing_install(root, report)` — Run pip install -e . for the project.
- `fix_module_level_exit(root, report)` — Wrap bare sys.exit() calls in if __name__ == '__main__' guards.
- `fix_version_mismatch(root, report)` — Update hardcoded version strings in test files.
- `fix_pytest_collision(root, report)` — Add override_name to pytest config so it doesn't collide with Typer CLI.
- `run_multi_analysis(project_dirs, config)` — Convenience function — analiza wielu projektów.
- `register(cli, host_module)` — Register all autonomy commands on the given Click group.
- `register(cli)` — Register the doctor command group on the given Click group.
- `run_hybrid_quality_refactor(project_path, max_changes)` — Apply ALL quality refactorings to a project without LLM.
- `run_hybrid_batch(semcod_root, max_changes)` — Run hybrid refactoring on all semcod projects.
- `detect_broken_guards(root)` — Find Python files with syntax errors caused by misplaced ``if __name__`` guards.
- `detect_stolen_indent(root)` — Find files where function/class body lost indentation after guard removal.
- `detect_broken_fstrings(root)` — Find files with broken f-strings (single brace, missing open brace).
- `detect_stale_pycache(root)` — Find stale __pycache__ directories.
- `detect_missing_install(root)` — Check whether the project's own package is importable.
- `detect_module_level_exit(root)` — Find test files with bare ``sys.exit(...)`` outside ``if __name__`` guard.
- `detect_version_mismatch(root)` — Find tests that hardcode a version string that differs from VERSION file.
- `detect_pytest_cli_collision(root)` — Check if ``python -m pytest`` is hijacked by a Typer/Click CLI.
- `run_semcod_batch(semcod_root, max_actions)` — Run batch refactoring on semcod projects.
- `apply_refactor(project_path, max_actions)` — Apply reDSL to a project and return the report.
- `measure_todo_reduction(project_path)` — Measure TODO.md before and after refactoring.
- `run_pyqual_batch(workspace_root, max_fixes, run_pipeline, git_push)` — Run ReDSL + pyqual on all projects in workspace.
- `compute_verdict(result, require_pipeline, require_push, require_publish)` — Compute final verdict for a project result.
- `process_project(project, max_fixes, run_pipeline, git_push)` — Full ReDSL + pyqual pipeline for a single project.
- `run_autofix_batch(semcod_root, max_changes)` — Run full autofix pipeline on all semcod packages.
- `run_pyqual_analysis(project_path, config_path, output_format)` — Run pyqual analysis on a project.
- `run_pyqual_fix(project_path, config_path)` — Run automatic fixes based on pyqual analysis.
- `run_autonomous_pr(git_url, max_actions, dry_run, auto_apply)` — Run the autonomous PR workflow.
- `run_full_pipeline_example(scenario, source, model)` — —
- `main(argv)` — —
- `run_basic_analysis_example(scenario, source)` — —
- `main(argv)` — —
- `load_example_yaml(example_name, scenario, source)` — —
- `list_available_examples()` — Return metadata for every example that has at least a ``default.yaml``.
- `print_banner(title, width, char)` — —
- `parse_scenario(argv)` — —
- `run_pyqual_example(scenario, source)` — —
- `main(argv)` — —
- `run_badge_example(scenario, source)` — —
- `main(argv)` — —
- `run_custom_rules_example(scenario, source)` — —
- `main(argv)` — —
- `run_awareness_example(scenario, source)` — —
- `main(argv)` — —
- `run_api_integration_example(scenario, source)` — —
- `main(argv)` — —
- `run_pr_bot_example(scenario, source)` — —
- `main(argv)` — —
- `run_audit_example(scenario, source)` — —
- `main(argv)` — —
- `profile_refactor_cycle(project_dir)` — Profiluj jeden cykl analizy/refaktoryzacji za pomocą metrun (lub fallback).
- `profile_llm_latency()` — Zmierz latencję wywołań LLM — kluczowy bottleneck.
- `profile_memory_operations()` — Zmierz czas operacji ChromaDB — store, recall, similarity search.
- `generate_optimization_report(project_dir)` — Wygeneruj raport z sugestiami optymalizacji (używany przez CLI i loop).
- `run_quality_gate(project_dir)` — Check whether current changes pass the quality gate.
- `install_pre_commit_hook(project_dir)` — Install a git pre-commit hook that runs the quality gate.
- `review_staged_changes(project_dir, model_override, max_diff_chars)` — Return a textual code review for all staged/unstaged changes.
- `analyze_commit_intent(project_dir)` — Analyse the current working-tree changes and return an intent report.
- `collect_autonomy_metrics(project_dir)` — Collect all autonomy metrics for a project.
- `save_metrics(metrics, path)` — Save metrics to a JSON file.
- `load_metrics(path)` — Load metrics from a JSON file.
- `smart_score(rule, context)` — Compute a multi-dimensional score for a refactoring decision.
- `run_memory_learning_example(scenario, source)` — —
- `main(argv)` — —
- `check_module_budget(file_path, module_type)` — Check whether a module stays within its complexity budget.
- `format_refactor_plan(decisions, format, analysis)` — Format refactoring plan in specified format.
- `format_debug_info(info, format)` — Format debug information.
- `format_cycle_report_yaml(report, decisions, analysis)` — Format full cycle report as YAML for stdout.
- `format_cycle_report_markdown(report, decisions, analysis, project_path)` — Format a refactor cycle as a Markdown report.
- `format_plan_yaml(decisions, analysis)` — Format dry-run plan as YAML for stdout.
- `format_batch_results(results, format)` — Format batch processing results.
- `format_batch_report_markdown(report, root, title)` — Format a batch run report as Markdown.
- `example()` — Run built-in examples and demos.
- `example_basic_analysis(scenario, source)` — Run the basic code-analysis demo.
- `example_custom_rules(scenario, source)` — Run the custom DSL rules demo.
- `example_full_pipeline(scenario, model, source)` — Run the full refactoring-pipeline demo (requires LLM key).
- `example_memory_learning(scenario, source)` — Run the agent-memory demo (episodic / semantic / procedural).
- `example_api_integration(scenario, source)` — Show API curl / httpx / WebSocket usage examples.
- `example_awareness(scenario, source)` — Run the awareness / change-pattern detection demo.
- `example_pyqual(scenario, source)` — Run the PyQual code-quality analysis demo.
- `example_audit(scenario, source)` — Run One-click Audit - full scan -> grade report -> badge.
- `example_pr_bot(scenario, source)` — Run PR Bot - realistic GitHub PR comment preview.
- `example_badge(scenario, source)` — Run Badge Generator - grade A+ to F with Markdown/HTML code.
- `example_list()` — List available example scenarios.
- `register_examples(cli)` — —
- `pyqual()` — Python code quality analysis commands.
- `pyqual_analyze(project_path, config, format)` — Analyze Python code quality.
- `pyqual_fix(project_path, config)` — Apply automatic quality fixes.
- `register_pyqual(cli)` — —
- `cli(ctx, verbose)` — reDSL - Automated code refactoring tool.
- `scan(ctx, folder, output_path, quiet)` — Scan a folder of projects and produce a markdown priority report.
- `cmd_analyze(project_dir)` — Analiza projektu — wyświetl metryki i alerty.
- `cmd_explain(project_dir)` — Wyjaśnij decyzje refaktoryzacji bez ich wykonywania.
- `cmd_refactor(project_dir, dry_run, auto, max_actions)` — Uruchom cykl refaktoryzacji.
- `cmd_memory_stats()` — Statystyki pamięci agenta.
- `cmd_serve(port, host)` — Uruchom serwer API.
- `main()` — Główny punkt wejścia CLI.
- `perf_command(ctx, project_path)` — Profile a refactoring cycle and report performance bottlenecks.
- `cost_command(ctx, project_path, max_actions)` — Estimate LLM cost for the next refactoring cycle without running it.
- `debug()` — Debug utilities for development.
- `debug_ast(project_path, file)` — Show AST analysis for debugging.
- `debug_llm(prompt, model)` — Test LLM with a simple prompt.
- `debug_metrics(project_path)` — Show project metrics for debugging.
- `register_debug(cli)` — —
- `refactor(ctx, project_path, max_actions, dry_run)` — Run refactoring on a project.
- `register_refactor(cli)` — —
- `batch()` — Batch refactoring commands.
- `batch_semcod(semcod_root, max_actions, format)` — Apply refactoring to semcod projects.
- `batch_hybrid(semcod_root, max_changes)` — Apply hybrid quality refactorings (no LLM needed).
- `batch_autofix(ctx, semcod_root, max_changes)` — Auto-fix all packages: scan -> generate TODO.md -> apply hybrid fixes -> gate fix.
- `batch_pyqual_run(ctx, workspace_root, max_fixes, limit)` — Multi-project quality pipeline: ReDSL analysis + pyqual gates + optional push.
- `register_batch(cli)` — —
- `explain_decisions(orchestrator, project_dir, limit)` — Explain refactoring decisions without executing them.
- `get_memory_stats(orchestrator)` — Return memory and runtime statistics for the orchestrator.
- `estimate_cycle_cost(orchestrator, project_dir, max_actions)` — Estimate the cost of the next cycle without executing it.
- `execute_sandboxed(orchestrator, decision, project_dir)` — Execute a decision in a sandboxed environment.
- `auto_fix_violations(project_dir, violations)` — Try to automatically fix each violation; create ticket on failure.
- `run_cycle(orchestrator, project_dir, max_actions, use_code2llm)` — Run a complete refactoring cycle.
- `run_from_toon_content(orchestrator, project_toon, duplication_toon, validation_toon)` — Run a cycle from pre-parsed toon content.
- `select_model(action, context, budget_remaining)` — Wybierz optymalny model na podstawie akcji i kontekstu.
- `select_reflection_model(use_local)` — Wybierz model do refleksji — zawsze tańszy.
- `estimate_cycle_cost(decisions, contexts)` — Szacuj koszt całego cyklu refaktoryzacji — lista per decyzja.
- `apply_provider_prefix(model, configured_model)` — Apply provider prefix from configured model to a bare model name.
- `call_via_llx(messages, task_type)` — Deleguj wywołanie LLM do llx CLI jeśli dostępne.
- `generate_diff(original, refactored, file_path)` — Wygeneruj unified diff dla dwóch wersji pliku.
- `preview_proposal(proposal, project_dir)` — Wygeneruj sformatowany diff wszystkich zmian w propozycji.
- `create_checkpoint(project_dir)` — Utwórz checkpoint aktualnego stanu projektu.
- `rollback_to_checkpoint(checkpoint_id, project_dir)` — Cofnij projekt do stanu z checkpointa.
- `rollback_single_file(file_path, checkpoint_id, project_dir)` — Cofnij jeden plik do stanu z checkpointa.
- `build_ecosystem_context(context)` — Render a short ecosystem/context block for prompts.
- `repair_file(path)` — Attempt to restore stolen class/function bodies in *path*.
- `repair_directory(root, dry_run)` — Walk *root* and repair all damaged Python files.
- `generate_github_workflow(project_dir, config, output_path)` — Wygeneruj zawartość pliku .github/workflows/redsl.yml.
- `install_github_workflow(project_dir, config, overwrite)` — Zainstaluj workflow w projekcie (.github/workflows/redsl.yml).
- `sandbox_available()` — True if Docker or pactfix is available for sandbox testing.
- `is_available()` — Sprawdź czy vallm jest zainstalowane i w pełni działa (nie tylko czy jest w PATH).
- `validate_patch(file_path, refactored_code, project_dir)` — Waliduj wygenerowany kod przez pipeline vallm.
- `validate_proposal(proposal, project_dir)` — Waliduj wszystkie zmiany w propozycji refaktoryzacji.
- `blend_confidence(base_confidence, vallm_score)` — Połącz confidence z metryk ReDSL z wynikiem vallm (punkt 2.3).
- `is_available()` — Return True if pyqual CLI is installed and functional.
- `doctor(project_dir)` — Run `pyqual doctor` and return structured tool availability dict.
- `check_gates(project_dir)` — Run `pyqual gates` and return pass/fail status.
- `get_status(project_dir)` — Run `pyqual status` and return current metrics summary.
- `validate_config(project_dir, fix)` — Run `pyqual validate` to check pyqual.yaml is well-formed.
- `init_config(project_dir, profile)` — Generate pyqual.yaml using `pyqual init`.
- `run_pipeline(project_dir, fix_config, dry_run)` — Run `pyqual run` and parse iterations plus push/publish status.
- `git_commit(project_dir, message, add_all, if_changed)` — Create a commit via `pyqual git commit`.
- `git_push(project_dir, detect_protection, dry_run)` — Push changes via `pyqual git push`.
- `validate_with_testql(project_dir, scenarios_dir, config)` — Validate project using testql scenarios.
- `check_testql_available()` — Check if testql CLI is available.
- `is_available()` — Sprawdź czy regix jest zainstalowane i działa poprawnie.
- `snapshot(project_dir, ref, timeout)` — Zrób snapshot metryk projektu przez regix.
- `compare(project_dir, before_ref, after_ref)` — Porównaj metryki między dwoma git refs przez regix.
- `compare_snapshots(project_dir, before, after)` — Porównaj dwa snapshoty (obiekty z `snapshot()`).
- `check_gates(project_dir)` — Sprawdź quality gates z regix.yaml (lub domyślne progi).
- `rollback_working_tree(project_dir)` — Cofnij niezatwierdzone zmiany w working tree przez `git checkout -- .`.
- `validate_no_regression(project_dir, rollback_on_failure)` — Porównaj HEAD~1 → HEAD i sprawdź czy nie ma regresji metryk.
- `validate_working_tree(project_dir, before_snapshot, rollback_on_failure)` — Porównaj snapshot 'przed' ze stanem working tree (po zmianach, przed commitem).
- `ast_max_nesting_depth(node)` — Oblicz max glębokość zagnieżdżenia pętli/warunków — nie wchodzi w zagnieżdżone def/class.
- `ast_cyclomatic_complexity(node)` — Oblicz CC dla funkcji — nie wchodzi w zagnieżdżone definicje funkcji/klas.
- `get_changed_files(project_dir, since)` — Pobierz listę zmienionych plików .py od podanego commita/ref.
- `get_staged_files(project_dir)` — Pobierz listę staged plików .py (git diff --cached).
- `analyze_with_sumd(project_dir)` — Analyze project using sumd if available, fallback to native analyzer.
- `is_available()` — Sprawdź czy redup jest zainstalowane i dostępne w PATH.
- `scan_duplicates(project_dir, min_lines, min_similarity)` — Uruchom redup i zwróć listę grup duplikatów.
- `scan_as_toon(project_dir, min_lines, min_similarity)` — Uruchom redup w formacie toon i zwróć zawartość jako string.
- `enrich_analysis(analysis, project_dir)` — Wzbogać istniejący AnalysisResult o dane z redup.
- `get_refactor_suggestions(project_dir)` — Pobierz sugestie refaktoryzacji duplikatów z redup.
- `is_available()` — Sprawdź czy code2llm jest zainstalowane i dostępne w PATH.
- `generate_toon_files(project_dir, output_dir, timeout)` — Uruchom code2llm na projekcie i zwróć katalog z wygenerowanymi plikami toon.
- `read_toon_contents(toon_dir)` — Wczytaj pliki toon z katalogu wyjściowego code2llm.
- `analyze_with_code2llm(project_dir, analyzer, output_dir, timeout)` — Pełna ścieżka percepcji z code2llm:
- `maybe_analyze(project_dir, analyzer, output_dir)` — Spróbuj analizy przez code2llm; zwróć None jeśli niezainstalowane.
- `is_radon_available()` — Sprawdź czy radon jest zainstalowany i dostępny.
- `run_radon_cc(project_dir, excludes)` — Uruchom `radon cc -j` i zwróć sparsowane wyniki.
- `extract_max_cc_per_file(radon_results, project_dir)` — Ekstraktuj maksymalne CC per plik z wyników radon.
- `enhance_metrics_with_radon(metrics, project_dir)` — Uzupełnij metryki o dokładne CC z radon (jeśli dostępne).
- `handle_push_webhook(payload)` — Process a GitHub push webhook payload.
- `create_app()` — Tworzenie aplikacji FastAPI.
- `setup_logging(project_path, verbose)` — Route all logging to a timestamped log file, keep stdout clean.


## Project Structure

📄 `.goal.pre-commit-hook` (1 functions)
📄 `.goal.vallm-pre-commit`
📄 `app.models` (3 classes)
📄 `examples.01-basic-analysis.main` (1 functions)
📄 `examples.02-custom-rules.main` (1 functions)
📄 `examples.03-full-pipeline.main` (1 functions)
📄 `examples.04-memory-learning.main` (1 functions)
📄 `examples.05-api-integration.main` (1 functions)
📄 `examples.06-awareness.main` (1 functions)
📄 `examples.07-pyqual.main` (1 functions)
📄 `examples.08-audit.main` (1 functions)
📄 `examples.09-pr-bot.main` (1 functions)
📄 `examples.10-badge.main` (1 functions)
📄 `project`
📦 `redsl`
📄 `redsl.__main__`
📦 `redsl.analyzers`
📄 `redsl.analyzers.analyzer` (8 functions, 1 classes)
📄 `redsl.analyzers.code2llm_bridge` (5 functions)
📄 `redsl.analyzers.incremental` (17 functions, 2 classes)
📄 `redsl.analyzers.metrics` (2 functions, 2 classes)
📦 `redsl.analyzers.parsers` (1 classes)
📄 `redsl.analyzers.parsers.duplication_parser` (1 functions, 1 classes)
📄 `redsl.analyzers.parsers.functions_parser` (6 functions, 1 classes)
📄 `redsl.analyzers.parsers.project_parser` (18 functions, 1 classes)
📄 `redsl.analyzers.parsers.validation_parser` (1 functions, 1 classes)
📄 `redsl.analyzers.python_analyzer` (8 functions, 1 classes)
📄 `redsl.analyzers.quality_visitor` (18 functions, 1 classes)
📄 `redsl.analyzers.radon_analyzer` (23 functions)
📄 `redsl.analyzers.redup_bridge` (8 functions)
📄 `redsl.analyzers.resolver` (4 functions, 1 classes)
📄 `redsl.analyzers.semantic_chunker` (11 functions, 2 classes)
📄 `redsl.analyzers.sumd_bridge` (13 functions, 2 classes)
📄 `redsl.analyzers.toon_analyzer` (13 functions, 1 classes)
📄 `redsl.analyzers.utils` (9 functions)
📦 `redsl.api` (2 functions)
📄 `redsl.api.debug_routes` (1 functions)
📄 `redsl.api.example_routes` (4 functions)
📄 `redsl.api.health_routes` (1 functions)
📄 `redsl.api.models` (13 classes)
📄 `redsl.api.pyqual_routes` (1 functions)
📄 `redsl.api.refactor_routes` (6 functions)
📄 `redsl.api.webhook_routes` (1 functions)
📦 `redsl.autonomy`
📄 `redsl.autonomy.adaptive_executor` (3 functions, 1 classes)
📄 `redsl.autonomy.auto_fix` (13 functions, 1 classes)
📄 `redsl.autonomy.growth_control` (12 functions, 3 classes)
📄 `redsl.autonomy.intent` (7 functions)
📄 `redsl.autonomy.metrics` (11 functions, 1 classes)
📄 `redsl.autonomy.quality_gate` (10 functions, 1 classes)
📄 `redsl.autonomy.review` (6 functions)
📄 `redsl.autonomy.scheduler` (16 functions, 2 classes)
📄 `redsl.autonomy.smart_scorer` (5 functions)
📦 `redsl.awareness` (16 functions, 2 classes)
📄 `redsl.awareness.change_patterns` (6 functions, 2 classes)
📄 `redsl.awareness.ecosystem` (10 functions, 2 classes)
📄 `redsl.awareness.git_timeline` (23 functions, 1 classes)
📄 `redsl.awareness.health_model` (6 functions, 3 classes)
📄 `redsl.awareness.proactive` (5 functions, 2 classes)
📄 `redsl.awareness.self_model` (7 functions, 3 classes)
📄 `redsl.awareness.timeline_analysis` (7 functions, 1 classes)
📄 `redsl.awareness.timeline_git` (7 functions, 1 classes)
📄 `redsl.awareness.timeline_models` (3 functions, 3 classes)
📄 `redsl.awareness.timeline_toon` (10 functions, 1 classes)
📦 `redsl.ci`
📄 `redsl.ci.github_actions` (6 functions, 1 classes)
📦 `redsl.cli` (3 functions)
📄 `redsl.cli.__main__`
📄 `redsl.cli.batch` (6 functions)
📄 `redsl.cli.debug` (5 functions)
📄 `redsl.cli.examples` (13 functions)
📄 `redsl.cli.logging` (1 functions)
📄 `redsl.cli.pyqual` (4 functions)
📄 `redsl.cli.refactor` (13 functions)
📄 `redsl.cli.scan` (2 functions)
📄 `redsl.cli.utils` (2 functions)
📄 `redsl.commands._guard_fixers` (8 functions)
📄 `redsl.commands._indent_fixers` (10 functions)
📄 `redsl.commands._scan_report` (8 functions)
📦 `redsl.commands.autofix`
📄 `redsl.commands.autofix.discovery` (2 functions)
📄 `redsl.commands.autofix.helpers` (2 functions)
📄 `redsl.commands.autofix.hybrid` (1 functions)
📄 `redsl.commands.autofix.models` (1 classes)
📄 `redsl.commands.autofix.pipeline` (6 functions)
📄 `redsl.commands.autofix.reporting` (5 functions)
📄 `redsl.commands.autofix.runner` (2 functions)
📄 `redsl.commands.autofix.todo_gen` (3 functions)
📦 `redsl.commands.autonomy_pr` (2 functions)
📄 `redsl.commands.autonomy_pr.analyzer` (6 functions)
📄 `redsl.commands.autonomy_pr.git_ops` (7 functions)
📄 `redsl.commands.autonomy_pr.models` (6 classes)
📄 `redsl.commands.autonomy_pr.reporter` (3 functions)
📄 `redsl.commands.autonomy_pr.validator` (7 functions)
📄 `redsl.commands.batch` (7 functions)
📦 `redsl.commands.batch_pyqual`
📄 `redsl.commands.batch_pyqual.config_gen` (4 functions)
📄 `redsl.commands.batch_pyqual.discovery` (7 functions)
📄 `redsl.commands.batch_pyqual.models` (1 classes)
📄 `redsl.commands.batch_pyqual.pipeline` (15 functions, 1 classes)
📄 `redsl.commands.batch_pyqual.reporting` (24 functions)
📄 `redsl.commands.batch_pyqual.runner` (10 functions)
📄 `redsl.commands.batch_pyqual.verdict` (7 functions)
📄 `redsl.commands.cli_autonomy` (20 functions)
📄 `redsl.commands.cli_awareness` (8 functions)
📄 `redsl.commands.cli_doctor` (8 functions)
📄 `redsl.commands.doctor` (3 functions)
📄 `redsl.commands.doctor_data` (1 functions, 2 classes)
📄 `redsl.commands.doctor_detectors` (16 functions)
📄 `redsl.commands.doctor_fixers` (8 functions)
📄 `redsl.commands.doctor_fstring_fixers` (11 functions)
📄 `redsl.commands.doctor_helpers` (2 functions)
📄 `redsl.commands.doctor_indent_fixers`
📄 `redsl.commands.hybrid` (14 functions)
📄 `redsl.commands.multi_project` (10 functions, 3 classes)
📄 `redsl.commands.planfile_bridge` (7 functions)
📦 `redsl.commands.pyqual` (13 functions, 1 classes)
📄 `redsl.commands.pyqual.ast_analyzer` (2 functions, 1 classes)
📄 `redsl.commands.pyqual.bandit_analyzer` (1 functions, 1 classes)
📄 `redsl.commands.pyqual.mypy_analyzer` (2 functions, 1 classes)
📄 `redsl.commands.pyqual.reporter` (5 functions, 1 classes)
📄 `redsl.commands.pyqual.ruff_analyzer` (1 functions, 1 classes)
📄 `redsl.commands.scan` (9 functions, 1 classes)
📄 `redsl.config` (4 functions, 5 classes)
📄 `redsl.consciousness_loop` (7 functions, 1 classes)
📦 `redsl.diagnostics`
📄 `redsl.diagnostics.perf_bridge` (11 functions, 3 classes)
📦 `redsl.dsl`
📄 `redsl.dsl.engine` (12 functions, 6 classes)
📄 `redsl.dsl.rule_generator` (11 functions, 2 classes)
📦 `redsl.examples`
📄 `redsl.examples._common` (6 functions)
📄 `redsl.examples.api_integration` (2 functions)
📄 `redsl.examples.audit` (4 functions)
📄 `redsl.examples.awareness` (6 functions)
📄 `redsl.examples.badge` (8 functions)
📄 `redsl.examples.basic_analysis` (2 functions)
📄 `redsl.examples.custom_rules` (3 functions)
📄 `redsl.examples.full_pipeline` (2 functions)
📄 `redsl.examples.memory_learning` (3 functions)
📄 `redsl.examples.pr_bot` (6 functions)
📄 `redsl.examples.pyqual_example` (2 functions)
📦 `redsl.execution`
📄 `redsl.execution.cycle` (5 functions)
📄 `redsl.execution.decision` (9 functions)
📄 `redsl.execution.executor`
📄 `redsl.execution.reflector` (2 functions)
📄 `redsl.execution.reporter` (4 functions)
📄 `redsl.execution.resolution` (6 functions)
📄 `redsl.execution.sandbox_execution` (1 functions)
📄 `redsl.execution.validation` (2 functions)
📦 `redsl.formatters`
📄 `redsl.formatters.batch` (12 functions)
📄 `redsl.formatters.core` (1 functions)
📄 `redsl.formatters.cycle` (11 functions)
📄 `redsl.formatters.debug` (1 functions)
📄 `redsl.formatters.refactor` (9 functions)
📄 `redsl.history` (13 functions, 3 classes)
📦 `redsl.integrations`
📄 `redsl.integrations.webhook` (3 functions)
📦 `redsl.llm` (7 functions, 2 classes)
📄 `redsl.llm.llx_router` (15 functions, 1 classes)
📄 `redsl.main` (23 functions)
📦 `redsl.memory` (18 functions, 4 classes)
📄 `redsl.orchestrator` (5 functions, 2 classes)
📦 `redsl.refactors`
📄 `redsl.refactors.ast_transformers` (9 functions, 2 classes)
📄 `redsl.refactors.body_restorer` (7 functions)
📄 `redsl.refactors.diff_manager` (9 functions)
📄 `redsl.refactors.direct` (6 functions, 1 classes)
📄 `redsl.refactors.direct_constants` (7 functions, 1 classes)
📄 `redsl.refactors.direct_guard` (7 functions, 1 classes)
📄 `redsl.refactors.direct_imports` (15 functions, 1 classes)
📄 `redsl.refactors.direct_types` (6 functions, 1 classes)
📄 `redsl.refactors.engine` (9 functions, 1 classes)
📄 `redsl.refactors.models` (3 classes)
📄 `redsl.refactors.prompts` (3 functions)
📦 `redsl.validation`
📄 `redsl.validation.pyqual_bridge` (12 functions)
📄 `redsl.validation.regix_bridge` (8 functions)
📄 `redsl.validation.sandbox` (9 functions, 3 classes)
📄 `redsl.validation.testql_bridge` (10 functions, 2 classes)
📄 `redsl.validation.vallm_bridge` (8 functions)

## Requirements

- Python >= 3.11
- fastapi >= 0.115.0
- uvicorn >= 0.44.0
- pydantic >= 2.10.0
- litellm >= 1.52.0
- chromadb >= 0.6.0
- pyyaml >= 6.0.2
- rich >= 13.9.0
- httpx >= 0.28.0
- click >= 8.1.7
- python-dotenv >= 1.0.1
- goal >= 2.1.0
- costs >= 0.1.20
- pfix >= 0.1.60

## Contributing

**Contributors:**
- Tom Sapletta

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/semcod/redsl
cd redsl

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Documentation

- 📖 [Full Documentation](https://github.com/semcod/redsl/tree/main/docs) — API reference, module docs, architecture
- 🚀 [Getting Started](https://github.com/semcod/redsl/blob/main/docs/getting-started.md) — Quick start guide
- 📚 [API Reference](https://github.com/semcod/redsl/blob/main/docs/api.md) — Complete API documentation
- 🔧 [Configuration](https://github.com/semcod/redsl/blob/main/docs/configuration.md) — Configuration options
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