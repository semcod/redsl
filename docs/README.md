---
path: /home/tom/github/semcod/redsl
---

<!-- code2docs:start --># redsl

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.11-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-4624-green)
> **4624** functions | **288** classes | **464** files | CC̄ = 3.9

> Auto-generated project documentation from source code analysis.

**Author:** Tom Sapletta  
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
pip install redsl[deploy]    # deploy features
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




## Architecture

```
redsl/
    ├── toon
├── SUMR
├── vallm
├── goal
├── README_EN
├── redsl_refactor_report
├── planfile
├── Makefile
├── SUMD
├── docker-compose
    ├── pre-commit-config
├── pyqual
├── requirements
├── sumd
├── pyproject
├── tree
├── TODO
├── pyqual_report
├── prefact
├── CHANGELOG
├── Taskfile
├── Dockerfile
├── project
├── README
├── redsl_scan_report
        ├── state
    ├── weekly-analizator-jakosci
    ├── regix-indeks-regresji
    ├── CONFIG_STANDARD
    ├── proxym-proxy-ai
    ├── prefact-linter-llm-aware
    ├── cost-kalkulator-kosztow-ai
    ├── domd-walidacja-komend-markdown
    ├── goal-automatyczny-git-push
    ├── redup-detekcja-duplikacji
    ├── toonic-format-toon
    ├── API
    ├── clickmd-markdown-terminal
    ├── CONFIG_MIGRATION
    ├── heal-zdrowie-wellness
    ├── model-policy-quickstart
    ├── metrun-profilowanie-wydajnosci
    ├── nfo-automatyczne-logowanie-funkcji
    ├── autonomous_pr_example
    ├── prellm-preprocessing-llm
    ├── pyqual-quality-gates
    ├── planfile-automatyzacja-sdlc
    ├── code2docs-automatyczna-dokumentacja
    ├── code2llm-analiza-przeplywu-kodu
    ├── vallm-walidacja-kodu-llm
    ├── CONFIG_CHEATSHEET
    ├── ats-benchmark
    ├── model-policy
    ├── qualbench-ci-dla-kodu-ai
    ├── llx-routing-modeli-llm
    ├── code2logic-analiza-nlp
    ├── zautomatyzowany-biznes-semcod
    ├── pactfix-bash-analyzer
    ├── pfix-self-healing-python
    ├── README
    ├── validation
        ├── advanced
        ├── default
        ├── main
        ├── README
        ├── advanced
        ├── default
        ├── main
        ├── README
        ├── advanced
        ├── default
        ├── main
        ├── README
        ├── advanced
        ├── default
        ├── main
        ├── README
        ├── advanced
        ├── default
        ├── main
        ├── README
        ├── advanced
        ├── default
        ├── main
        ├── README
        ├── main
        ├── README
        ├── advanced
        ├── team_rules
        ├── default
        ├── main
        ├── README
        ├── advanced
        ├── default
        ├── main
        ├── README
        ├── advanced
        ├── default
        ├── main
        ├── README
        ├── advanced
        ├── default
        ├── main
        ├── README
    ├── models
    ├── redsl_refactor_report
    ├── complex_code
        ├── config
            ├── backlog
            ├── current
        ├── toon
    ├── redsl_refactor_report
    ├── bad_code
    ├── redsl_refactor_plan
    ├── validation
    ├── hybrid_refactor_results
    ├── pyqual_report
    ├── redsl_batch_hybrid_report
        ├── toon
        ├── toon
    ├── SUMR
    ├── propozycje
    ├── nda-form
    ├── nda-wzor
    ├── smoke-test
    ├── README_CONFIG
    ├── DEPLOY_CHECKLIST
    ├── README_PROPozycje
    ├── Makefile
    ├── bootstrap
    ├── SUMD
    ├── config-editor
    ├── README-PLESK
    ├── email-notifications
    ├── docker-compose
    ├── phpunit
    ├── install-plesk
    ├── proposals
    ├── polityka-prywatnosci
    ├── index
    ├── composer
    ├── README_NDA
    ├── test-plesk
    ├── config-api
    ├── Dockerfile
    ├── project
    ├── regulamin
    ├── README
    ├── app
        ├── index
        ├── landing-page-copy
        ├── README
        ├── authorize
        ├── access_token
        ├── user
        ├── index
        ├── logs
        ├── tickets
        ├── index
        ├── invoices
        ├── auth
        ├── scans
        ├── contracts
        ├── clients
        ├── projects
        ├── en
        ├── de
        ├── pl
        ├── index
        ├── context
        ├── prompt
            ├── toon
        ├── calls
            ├── toon
            ├── toon
        ├── README
            ├── toon
            ├── toon
                ├── toon
        ├── invoice-generator
        ├── scan-worker
        ├── index
        ├── redsl
        ├── toon
    ├── default_rules
        ├── vallm-pre-commit
        ├── pre-commit-hook
    ├── context
    ├── prompt
        ├── toon
        ├── toon
    ├── README
        ├── toon
        ├── toon
    ├── config
    ├── consciousness_loop
├── redsl/
    ├── __main__
    ├── history
    ├── orchestrator
    ├── main
    ├── pyqual_report
        ├── cli_awareness
        ├── _fixer_utils
        ├── _scan_report
        ├── doctor
        ├── sumr_planfile/
        ├── doctor_indent_fixers
        ├── planfile_bridge
        ├── scan
        ├── doctor_fstring_fixers
        ├── doctor_fixers
        ├── _guard_fixers
        ├── plan_sync
        ├── doctor_helpers
        ├── multi_project
        ├── doctor_data
        ├── github_source
        ├── cli_autonomy
        ├── cli_doctor
        ├── hybrid
        ├── _indent_fixers
        ├── doctor_detectors
        ├── batch
            ├── reporting
            ├── runner
            ├── verdict
        ├── batch_pyqual/
            ├── utils
            ├── models
            ├── pipeline
            ├── discovery
            ├── config_gen
            ├── reporting
            ├── helpers
            ├── runner
        ├── autofix/
            ├── models
            ├── todo_gen
            ├── pipeline
            ├── hybrid
            ├── discovery
            ├── extractors
            ├── parsers
            ├── utils
            ├── models
            ├── core
            ├── ruff_analyzer
            ├── mypy_analyzer
            ├── reporter
        ├── pyqual/
            ├── bandit_analyzer
            ├── fix_decisions
            ├── ast_analyzer
            ├── validator
            ├── analyzer
            ├── reporter
        ├── autonomy_pr/
            ├── models
            ├── git_ops
        ├── applier
        ├── store
        ├── llm_policy
        ├── nlp_handlers
        ├── proposals
        ├── catalog
        ├── security
    ├── config_standard/
        ├── agent_bridge
        ├── paths
        ├── models
        ├── core
        ├── profiles
        ├── secrets
    ├── debug
        ├── workflow
        ├── full_pipeline
        ├── basic_analysis
    ├── examples/
        ├── _common
        ├── pyqual_example
        ├── badge
        ├── custom_rules
        ├── awareness
        ├── api_integration
        ├── audit
        ├── pr_bot
        ├── memory_learning
    ├── diagnostics/
        ├── perf_bridge
    ├── core/
        ├── pipeline
        ├── quality_gate
        ├── review
        ├── intent
    ├── autonomy/
        ├── metrics
        ├── adaptive_executor
        ├── scheduler
        ├── smart_scorer
        ├── auto_fix
        ├── growth_control
    ├── formatters/
        ├── refactor
        ├── core
        ├── cycle
        ├── pyqual_report
        ├── debug
        ├── batch
    ├── memory/
        ├── llm_banner
        ├── config
        ├── examples
        ├── pyqual
        ├── events
    ├── cli/
        ├── scan
        ├── __main__
        ├── refactor
        ├── logging
        ├── deploy
        ├── model_policy
        ├── utils
        ├── models
        ├── planfile
        ├── workflow
        ├── debug
        ├── batch
        ├── planfile_runner
        ├── resolution
        ├── decision
        ├── reporter
    ├── execution/
        ├── planfile_updater
        ├── pyqual_validators
        ├── sandbox_execution
        ├── backup_manager
        ├── validation
        ├── reflector
        ├── executor
        ├── project_scanner
        ├── cycle
        ├── workflow
        ├── deploy_detector
        ├── redeploy_bridge
        ├── base
    ├── bridges/
        ├── context
            ├── toon
        ├── README
            ├── toon
                ├── toon
                ├── toon
                ├── toon
                ├── toon
                ├── toon
                ├── toon
        ├── gate
    ├── llm/
        ├── selection/
        ├── llx_router
        ├── registry/
            ├── models
            ├── aggregator
                ├── base
            ├── sources/
            ├── ops
            ├── config
            ├── metrics
            ├── models
            ├── checks
            ├── strategy
            ├── selector
        ├── direct_types
        ├── direct_guard
        ├── engine
        ├── direct
        ├── diff_manager
        ├── direct_imports
        ├── prompts
        ├── ast_transformers
        ├── body_restorer
    ├── refactors/
        ├── models
        ├── direct_constants
        ├── _base
    ├── ci/
        ├── github_actions
        ├── git_timeline
        ├── ecosystem
        ├── timeline_git
        ├── timeline_toon
        ├── timeline_models
    ├── awareness/
        ├── proactive
        ├── timeline_analysis
        ├── change_patterns
        ├── self_model
        ├── health_model
        ├── sandbox
    ├── validation/
        ├── vallm_bridge
        ├── pyqual_bridge
        ├── testql_bridge
        ├── regix_bridge
        ├── tool_check
    ├── utils/
        ├── json_helpers
        ├── python_analyzer
        ├── sumd_bridge
        ├── incremental
        ├── analyzer
        ├── quality_visitor
    ├── analyzers/
        ├── metrics
        ├── redup_bridge
        ├── toon_analyzer
        ├── semantic_chunker
        ├── utils
        ├── resolver
        ├── code2llm_bridge
        ├── radon_analyzer
            ├── project_parser
        ├── parsers/
            ├── functions_parser
            ├── validation_parser
            ├── duplication_parser
        ├── webhook
    ├── integrations/
        ├── pyqual_routes
        ├── health_routes
    ├── api/
        ├── refactor_routes
        ├── scan_routes
        ├── models
        ├── cqrs_routes
        ├── webhook_routes
        ├── openapi
        ├── debug_routes
        ├── example_routes
            ├── commands
            ├── events
        ├── cqrs/
            ├── websocket_manager
            ├── queries
            ├── projections
        ├── engine
    ├── dsl/
        ├── rule_generator
            ├── context
            ├── README
                ├── toon
    ├── prompt
        ├── toon
    ├── context
        ├── toon
    ├── README
        ├── toon
        ├── toon
    ├── calls
        ├── toon
```

## API Overview

### Classes

- **`HistoryEvent`** — —
- **`HistoryWriter`** — —
- **`HistoryReader`** — —
- **`ConsciousnessLoop`** — —
- **`LLMConfig`** — —
- **`MemoryConfig`** — —
- **`AnalyzerConfig`** — —
- **`RefactorConfig`** — —
- **`AgentConfig`** — —
- **`CycleReport`** — —
- **`RefactorOrchestrator`** — —
- **`HistoryEvent`** — —
- **`HistoryWriter`** — —
- **`HistoryReader`** — —
- **`ConsciousnessLoop`** — —
- **`LLMConfig`** — —
- **`MemoryConfig`** — —
- **`AnalyzerConfig`** — —
- **`RefactorConfig`** — —
- **`AgentConfig`** — —
- **`CycleReport`** — —
- **`RefactorOrchestrator`** — —
- **`SessionManager`** — —
- **`SessionValidator`** — —
- **`SessionStore`** — —
- **`SessionLifecycle`** — —
- **`Formatter`** — —
- **`Formatter`** — —
- **`FileChange`** — Zmiana w pojedynczym pliku.
- **`RefactorProposal`** — Propozycja refaktoryzacji wygenerowana przez LLM.
- **`RefactorResult`** — Wynik zastosowania refaktoryzacji.
- **`GodClass`** — A god class with too many responsibilities.
- **`BadClass`** — —
- **`LLMConfig`** — Konfiguracja warstwy LLM.
- **`MemoryConfig`** — Konfiguracja systemu pamięci.
- **`AnalyzerConfig`** — Konfiguracja analizatora kodu.
- **`RefactorConfig`** — Konfiguracja silnika refaktoryzacji.
- **`AgentConfig`** — Główna konfiguracja agenta.
- **`ConsciousnessLoop`** — Ciągła pętla „świadomości" agenta.
- **`HistoryEvent`** — A single persisted event in the refactor history.
- **`HistoryWriter`** — Append-only history logger backed by .redsl/history.jsonl.
- **`HistoryReader`** — Read-only access to .redsl/history.jsonl for querying and dedup.
- **`CycleReport`** — Raport z jednego cyklu refaktoryzacji.
- **`RefactorOrchestrator`** — Główny orkiestrator — „mózg" systemu.
- **`ProjectScanResult`** — Scan result for a single project.
- **`MergeResult`** — —
- **`SyncResult`** — —
- **`ProjectAnalysis`** — Wyniki analizy pojedynczego projektu.
- **`MultiProjectReport`** — Zbiorczy raport z analizy wielu projektów.
- **`MultiProjectRunner`** — Uruchamia ReDSL na wielu projektach.
- **`Issue`** — A single detected issue.
- **`DoctorReport`** — Aggregated report for one project.
- **`PyqualProjectResult`** — Result of pyqual pipeline for a single project.
- **`ProjectContext`** — Mutable context passed through pipeline stages.
- **`ProjectFixResult`** — Result of autofix processing for a single project.
- **`PlanTask`** — —
- **`SumrData`** — —
- **`PlanfileResult`** — —
- **`RuffAnalyzer`** — Uruchamia ruff i zbiera wyniki.
- **`MypyAnalyzer`** — Uruchamia mypy i zbiera wyniki.
- **`Reporter`** — Generuje rekomendacje i zapisuje raporty analizy jakości.
- **`PyQualAnalyzer`** — Python code quality analyzer — fasada nad wyspecjalizowanymi analizatorami.
- **`BanditAnalyzer`** — Uruchamia bandit i zbiera wyniki bezpieczeństwa.
- **`AstAnalyzer`** — Analizuje pliki Python przez AST w poszukiwaniu typowych problemów jakości.
- **`ApplyResult`** — —
- **`ConfigApplier`** — Apply config proposals atomically with locking and audit logging.
- **`ConfigStoreError`** — —
- **`ConfigVersionMismatch`** — —
- **`ConfigValidationError`** — —
- **`ConfigHistoryRecord`** — —
- **`ConfigStore`** — Manage a redsl-config directory with manifest, profiles and history.
- **`LLMPolicy`** — —
- **`CostWeights`** — —
- **`CodingTiers`** — —
- **`DefaultOperationTiers`** — —
- **`CodingConfig`** — —
- **`ToolError`** — Raised when a tool call fails validation or execution.
- **`ProposalMetadata`** — —
- **`ConfigPreconditions`** — —
- **`ConfigValidationState`** — —
- **`ConfigChange`** — —
- **`ConfigChangeProposal`** — —
- **`PathCatalogEntry`** — —
- **`SecretMatch`** — —
- **`SecretInterceptor`** — Redact secret-looking substrings before data is shown to an LLM.
- **`ConfigBridgeError`** — Raised when config bridge cannot resolve configuration.
- **`ConfigOrigin`** — —
- **`ConfigMetadata`** — —
- **`RegistrySource`** — —
- **`CacheConfig`** — —
- **`RedslConfigSpec`** — —
- **`RedslConfigDocument`** — —
- **`SecretRotation`** — —
- **`SecretSpec`** — —
- **`Bottleneck`** — —
- **`CriticalStep`** — —
- **`PerformanceReport`** — —
- **`StepResult`** — —
- **`PipelineStep`** — Abstract base for a single pipeline step.
- **`PipelineResult`** — —
- **`Pipeline`** — Run a sequence of PipelineStep objects against a shared context dict.
- **`GateVerdict`** — Result of a quality gate check.
- **`AutonomyMetrics`** — Metrics for the autonomy subsystem.
- **`AdaptiveExecutor`** — Execute decisions while adapting strategy on repeated failures.
- **`AutonomyMode`** — —
- **`Scheduler`** — Periodic quality-improvement loop.
- **`AutoFixResult`** — Outcome of the auto-fix pipeline.
- **`GrowthBudget`** — LOC growth budget per iteration.
- **`GrowthController`** — Enforce growth budgets on a project.
- **`ModuleBudget`** — Complexity budget for a single module.
- **`MemoryEntry`** — Pojedynczy wpis w pamięci.
- **`MemoryLayer`** — Warstwa pamięci oparta na ChromaDB.
- **`InMemoryCollection`** — Fallback gdy ChromaDB nie jest dostępne.
- **`AgentMemory`** — Kompletny system pamięci z trzema warstwami.
- **`ProjectMap`** — Structured inventory of config files found in a project.
- **`PerceiveConfig`** — —
- **`DecideConfig`** — —
- **`ExecuteConfig`** — —
- **`TuneConfig`** — —
- **`ValidateStepConfig`** — —
- **`ValidateConfig`** — —
- **`PlanfileConfig`** — —
- **`ReflectConfig`** — —
- **`StorageConfig`** — Controls where redsl stores its logs and LLM chat history.
- **`DeployConfig`** — Controls whether and how redsl performs push / publish after a cycle.
- **`ProjectMapConfig`** — Inventory of configuration files found in the project.
- **`WorkflowConfig`** — —
- **`DeployAction`** — A single detected push or publish action.
- **`DetectedDeployConfig`** — Result of auto-detection for a single project.
- **`CliBridge`** — Base class for bridges wrapping external CLI tools.
- **`ModelRejectedError`** — Raised when model is rejected by policy.
- **`ModelAgeGate`** — Enforces model age and lifecycle policy before LLM calls.
- **`LLMResponse`** — Odpowiedź z modelu LLM.
- **`LLMLayer`** — Warstwa abstrakcji nad LLM z obsługą:
- **`ModelSelection`** — —
- **`PolicyMode`** — Policy mode for model age checking.
- **`UnknownReleaseAction`** — Action when model release date is unknown.
- **`Pricing`** — Ceny USD per token (nie per million!).
- **`Capabilities`** — Features modelu istotne dla programowania.
- **`QualitySignals`** — Sygnały jakości z różnych benchmarków.
- **`ModelInfo`** — Information about an LLM model.
- **`PolicyDecision`** — Result of policy check for a model.
- **`RegistryAggregator`** — Aggregates model info from multiple sources with caching.
- **`ModelRegistrySource`** — Abstract base class for model registry sources.
- **`OpenRouterSource`** — OpenRouter public API - no auth required, ~300+ models.
- **`ModelsDevSource`** — Models.dev community API - public, ~200+ models.
- **`OpenAIProviderSource`** — Native OpenAI API - requires key, authoritative for OpenAI models.
- **`AnthropicProviderSource`** — Native Anthropic API - requires key, authoritative for Claude models.
- **`AiderLeaderboardSource`** — Drugie niezależne źródło — benchmark polyglot od Aider.
- **`CostProfile`** — Jak liczymy koszt per model.
- **`CodingRequirements`** — Wymagania techniczne dla modelu do kodowania.
- **`ModelCandidate`** — Kandydat na model z metrykami.
- **`ModelSelectionError`** — Raised when no model can be selected.
- **`SelectionStrategy`** — Strategia wyboru modelu.
- **`ModelSelector`** — Wybiera najtańszy model spełniający wymagania.
- **`DirectTypesRefactorer`** — Handles return type annotation addition.
- **`DirectGuardRefactorer`** — Handles main guard wrapping for module-level execution code.
- **`RefactorEngine`** — Silnik refaktoryzacji z pętlą refleksji.
- **`DirectRefactorEngine`** — Applies simple refactorings directly via AST manipulation.
- **`DirectImportRefactorer`** — Handles import-related direct refactoring.
- **`ReturnTypeAdder`** — AST transformer to add return type annotations.
- **`UnusedImportRemover`** — AST transformer to remove unused imports.
- **`FileChange`** — Zmiana w pojedynczym pliku.
- **`RefactorProposal`** — Propozycja refaktoryzacji wygenerowana przez LLM.
- **`RefactorResult`** — Wynik zastosowania refaktoryzacji.
- **`DirectConstantsRefactorer`** — Handles magic number to constant extraction.
- **`DirectRefactorBase`** — Mixin that provides ``get_applied_changes`` for Direct* refactorers.
- **`WorkflowConfig`** — Konfiguracja generowanego workflow.
- **`GitTimelineAnalyzer`** — Build a historical metric timeline from git commits — facade.
- **`ProjectNode`** — Single project node in the ecosystem graph.
- **`EcosystemGraph`** — Basic ecosystem graph for semcod-style project collections.
- **`GitTimelineProvider`** — Provides git-based timeline data.
- **`ToonCollector`** — Collects and processes toon files from git history.
- **`MetricPoint`** — Single timeline point captured from a git commit.
- **`TrendAnalysis`** — Trend summary for a single metric series.
- **`TimelineSummary`** — High-level summary of a git timeline.
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
- **`SumdMetrics`** — Metrics extracted from sumd analysis.
- **`SumdAnalyzer`** — Native project analyzer using sumd extractor patterns.
- **`EvolutionaryCache`** — Cache wyników analizy per-plik oparty o hash pliku.
- **`IncrementalAnalyzer`** — Analizuje tylko zmienione pliki i scala z cached wynikami.
- **`CodeAnalyzer`** — Główny analizator kodu — fasada.
- **`CodeQualityVisitor`** — Detects common code quality issues in Python AST.
- **`CodeMetrics`** — Metryki pojedynczej funkcji/modułu.
- **`AnalysisResult`** — Wynik analizy projektu.
- **`ToonAnalyzer`** — Analizator plików toon — przetwarza dane z code2llm.
- **`SemanticChunk`** — Wycięty semantyczny fragment kodu gotowy do wysłania do LLM.
- **`SemanticChunker`** — Buduje semantyczne chunki kodu dla LLM.
- **`PathResolver`** — Resolver ścieżek i kodu źródłowego funkcji.
- **`ProjectParser`** — Parser sekcji project_toon.
- **`ToonParser`** — Parser plików toon — fasada nad wyspecjalizowanymi parserami.
- **`FunctionsParser`** — Parser sekcji functions_toon — per-funkcja CC.
- **`ValidationParser`** — Parser sekcji validation_toon.
- **`DuplicationParser`** — Parser sekcji duplication_toon.
- **`ScanRepoRequest`** — Request to scan a remote repository.
- **`ScanRepoResponse`** — Response from remote repository scan.
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
- **`ScanRemoteRequest`** — Request to scan remote repository.
- **`ScanRemoteResponse`** — Response from scan operation.
- **`RefactorRequest`** — Request to run refactoring.
- **`QueryResponse`** — Generic query response.
- **`EventStreamRequest`** — Request for event stream subscription.
- **`Command`** — Base command.
- **`ScanRemoteCommand`** — Command to scan remote repository.
- **`RefactorCommand`** — Command to run refactoring cycle.
- **`CommandHandler`** — Base command handler.
- **`ScanRemoteHandler`** — Handler for ScanRemoteCommand.
- **`RefactorHandler`** — Handler for RefactorCommand.
- **`CommandBus`** — Command Bus - dispatches commands to handlers.
- **`DomainEvent`** — Base class for domain events.
- **`ScanStarted`** — Event emitted when remote scan starts.
- **`ScanProgress`** — Event emitted during scan progress.
- **`ScanCompleted`** — Event emitted when scan completes successfully.
- **`ScanFailed`** — Event emitted when scan fails.
- **`RefactorStarted`** — Event emitted when refactoring starts.
- **`RefactorProgress`** — Event emitted during refactoring.
- **`RefactorCompleted`** — Event emitted when refactoring completes.
- **`EventStore`** — Append-only event store with file-based persistence.
- **`WebSocketManager`** — Manages WebSocket connections for real-time event streaming.
- **`Query`** — Base query.
- **`ScanResultQuery`** — Query for scan results.
- **`ProjectHealthQuery`** — Query for project health metrics.
- **`RecentEventsQuery`** — Query for recent events.
- **`AggregateHistoryQuery`** — Query for aggregate event history.
- **`QueryHandler`** — Base query handler.
- **`ScanResultHandler`** — Handler for ScanResultQuery - reads from projection.
- **`ProjectHealthHandler`** — Handler for ProjectHealthQuery.
- **`RecentEventsHandler`** — Handler for RecentEventsQuery - reads from event store.
- **`AggregateHistoryHandler`** — Handler for AggregateHistoryQuery.
- **`QueryBus`** — Query Bus - dispatches queries to handlers.
- **`Projection`** — Base class for read model projections.
- **`ScanProjection`** — Projection for scan results.
- **`ProjectHealthProjection`** — Projection for project health over time.
- **`ProjectionManager`** — Manages projections and rebuilds them from events.
- **`Operator`** — —
- **`RefactorAction`** — —
- **`Condition`** — Pojedynczy warunek DSL.
- **`Rule`** — Reguła DSL: warunki → akcja z priorytetem.
- **`Decision`** — Wynik ewaluacji reguł — decyzja co refaktoryzować.
- **`DSLEngine`** — Silnik ewaluacji reguł DSL.
- **`LearnedRule`** — Reguła DSL wygenerowana z wzorców w pamięci.
- **`RuleGenerator`** — Generuje nowe reguły DSL z historii refaktoryzacji w pamięci agenta.

### Functions

- `cmd_analyze()` — —
- `cmd_explain()` — —
- `cmd_refactor()` — —
- `cmd_memory_stats()` — —
- `cmd_serve()` — —
- `main()` — —
- `record()` — —
- `record_event()` — —
- `decision_signature()` — —
- `has_recent_signature()` — —
- `load_events()` — —
- `filter_by_file()` — —
- `filter_by_type()` — —
- `has_recent_proposal()` — —
- `has_recent_ticket()` — —
- `generate_decision_report()` — —
- `main_loop()` — —
- `run()` — —
- `stop()` — —
- `is_local()` — —
- `api_key()` — —
- `from_env()` — —
- `run_cycle()` — —
- `run_from_toon_content()` — —
- `add_custom_rules()` — —
- `OPENAI_API_KEY()` — —
- `main()` — —
- `main()` — —
- `process_order()` — —
- `demo_policy_check()` — —
- `demo_list_allowed()` — —
- `demo_safe_completion()` — —
- `demo_strict_mode()` — —
- `is_available()` — —
- `generate_toon_files()` — —
- `read_toon_contents()` — —
- `analyze_with_code2llm()` — —
- `maybe_analyze()` — —
- `get_changed_files()` — —
- `get_staged_files()` — —
- `ast_max_nesting_depth()` — —
- `ast_cyclomatic_complexity()` — —
- `is_radon_available()` — —
- `run_radon_cc()` — —
- `extract_max_cc_per_file()` — —
- `enhance_metrics_with_radon()` — —
- `scan_duplicates()` — —
- `scan_as_toon()` — —
- `enrich_analysis()` — —
- `get_refactor_suggestions()` — —
- `analyze_with_sumd()` — —
- `create_app()` — —
- `auto_fix_violations()` — —
- `check_module_budget()` — —
- `analyze_commit_intent()` — —
- `collect_autonomy_metrics()` — —
- `save_metrics()` — —
- `load_metrics()` — —
- `run_quality_gate()` — —
- `install_pre_commit_hook()` — —
- `review_staged_changes()` — —
- `smart_score()` — —
- `generate_github_workflow()` — —
- `install_github_workflow()` — —
- `cli()` — —
- `batch()` — —
- `batch_semcod()` — —
- `batch_hybrid()` — —
- `batch_autofix()` — —
- `batch_pyqual_run()` — —
- `register_batch()` — —
- `config()` — —
- `config_init()` — —
- `config_validate()` — —
- `config_diff()` — —
- `config_history()` — —
- `config_apply()` — —
- `config_clone()` — —
- `config_show()` — —
- `config_rollback()` — —
- `register_config()` — —
- `debug()` — —
- `debug_ast()` — —
- `debug_llm()` — —
- `debug_metrics()` — —
- `register_debug()` — —
- `example()` — —
- `example_basic_analysis()` — —
- `example_custom_rules()` — —
- `example_full_pipeline()` — —
- `example_memory_learning()` — —
- `example_api_integration()` — —
- `example_awareness()` — —
- `example_pyqual()` — —
- `example_audit()` — —
- `example_pr_bot()` — —
- `example_badge()` — —
- `example_list()` — —
- `register_examples()` — —
- `print_llm_banner()` — —
- `setup_logging()` — —
- `register_model_policy()` — —
- `model_policy()` — —
- `check_model()` — —
- `list_models()` — —
- `refresh_registry()` — —
- `show_config()` — —
- `register_models()` — —
- `models_group()` — —
- `pick_coding()` — —
- `list_coding()` — —
- `estimate_cost()` — —
- `show_coding_config()` — —
- `planfile_group()` — —
- `planfile_sync()` — —
- `planfile_show()` — —
- `register()` — —
- `pyqual()` — —
- `pyqual_analyze()` — —
- `pyqual_fix()` — —
- `register_pyqual()` — —
- `refactor()` — —
- `register_refactor()` — —
- `scan()` — —
- `perf_command()` — —
- `cost_command()` — —
- `render_markdown()` — —
- `run_autofix_batch()` — —
- `run_autonomous_pr()` — —
- `run_semcod_batch()` — —
- `apply_refactor()` — —
- `measure_todo_reduction()` — —
- `process_project()` — —
- `run_pyqual_batch()` — —
- `run_cmd()` — —
- `git_status_lines()` — —
- `resolve_profile()` — —
- `compute_verdict()` — —
- `diagnose()` — —
- `heal()` — —
- `heal_batch()` — —
- `detect_broken_guards()` — —
- `detect_stolen_indent()` — —
- `detect_broken_fstrings()` — —
- `detect_stale_pycache()` — —
- `detect_missing_install()` — —
- `detect_module_level_exit()` — —
- `detect_version_mismatch()` — —
- `detect_pytest_cli_collision()` — —
- `fix_broken_guards()` — —
- `fix_stolen_indent()` — —
- `fix_broken_fstrings()` — —
- `fix_stale_pycache()` — —
- `fix_missing_install()` — —
- `fix_module_level_exit()` — —
- `fix_version_mismatch()` — —
- `fix_pytest_collision()` — —
- `run_hybrid_quality_refactor()` — —
- `run_hybrid_batch()` — —
- `run_multi_analysis()` — —
- `create_ticket()` — —
- `list_tickets()` — —
- `report_refactor_results()` — —
- `run_pyqual_analysis()` — —
- `run_pyqual_fix()` — —
- `build_pyqual_fix_decisions()` — —
- `scan_folder()` — —
- `parse_sumr()` — —
- `toon_to_tasks()` — —
- `refactor_plan_to_tasks()` — —
- `generate_planfile()` — —
- `resolve_secret_ref()` — —
- `find_config_root()` — —
- `load_agent_config_from_substrate()` — —
- `agent_config_from_substrate_or_env()` — —
- `get_risk_level()` — —
- `search_schema_matches()` — —
- `dispatch_tool()` — —
- `parse_config_path()` — —
- `get_nested_value()` — —
- `set_nested_value()` — —
- `remove_nested_value()` — —
- `deep_merge()` — —
- `deep_diff()` — —
- `materialize_diff()` — —
- `walk_paths()` — —
- `build_default_config()` — —
- `config_doc_to_yaml()` — —
- `export_config_schema()` — —
- `export_proposal_schema()` — —
- `proposal_to_yaml()` — —
- `is_sensitive_key()` — —
- `mask_sensitive_mapping()` — —
- `main_loop()` — —
- `profile_refactor_cycle()` — —
- `profile_llm_latency()` — —
- `profile_memory_operations()` — —
- `generate_optimization_report()` — —
- `load_example_yaml()` — —
- `list_available_examples()` — —
- `print_banner()` — —
- `parse_scenario()` — —
- `run_api_integration_example()` — —
- `run_audit_example()` — —
- `run_awareness_example()` — —
- `run_badge_example()` — —
- `run_basic_analysis_example()` — —
- `run_custom_rules_example()` — —
- `run_full_pipeline_example()` — —
- `run_memory_learning_example()` — —
- `run_pr_bot_example()` — —
- `run_pyqual_example()` — —
- `run_cycle()` — —
- `run_from_toon_content()` — —
- `explain_decisions()` — —
- `get_memory_stats()` — —
- `estimate_cycle_cost()` — —
- `execute_sandboxed()` — —
- `format_batch_results()` — —
- `format_batch_report_markdown()` — —
- `format_cycle_report_yaml()` — —
- `format_cycle_report_markdown()` — —
- `format_plan_yaml()` — —
- `format_cycle_report_toon()` — —
- `format_debug_info()` — —
- `format_refactor_plan()` — —
- `handle_push_webhook()` — —
- `get_gate()` — —
- `safe_completion()` — —
- `check_model_policy()` — —
- `list_allowed_models()` — —
- `select_model()` — —
- `select_reflection_model()` — —
- `apply_provider_prefix()` — —
- `call_via_llx()` — —
- `build_selector()` — —
- `select_model_for_operation()` — —
- `get_selector()` — —
- `invalidate_selector()` — —
- `track_model_selection()` — —
- `check_cost_per_call()` — —
- `cmd_analyze()` — —
- `cmd_explain()` — —
- `cmd_refactor()` — —
- `cmd_memory_stats()` — —
- `cmd_serve()` — —
- `repair_file()` — —
- `repair_directory()` — —
- `generate_diff()` — —
- `preview_proposal()` — —
- `create_checkpoint()` — —
- `rollback_to_checkpoint()` — —
- `rollback_single_file()` — —
- `build_ecosystem_context()` — —
- `extract_json_block()` — —
- `is_tool_available()` — —
- `doctor()` — —
- `check_gates()` — —
- `get_status()` — —
- `validate_config()` — —
- `init_config()` — —
- `run_pipeline()` — —
- `git_commit()` — —
- `git_push()` — —
- `snapshot()` — —
- `compare()` — —
- `compare_snapshots()` — —
- `rollback_working_tree()` — —
- `validate_no_regression()` — —
- `validate_working_tree()` — —
- `sandbox_available()` — —
- `generate_behavior_tests()` — —
- `generate_snapshot_test()` — —
- `verify_behavior_preserved()` — —
- `discover_test_command()` — —
- `run_tests()` — —
- `validate_refactor()` — —
- `validate_with_testql()` — —
- `check_testql_available()` — —
- `validate_patch()` — —
- `validate_proposal()` — —
- `blend_confidence()` — —
- `process_data()` — —
- `process_data_copy()` — —
- `calculate()` — —
- `calculate_area()` — —
- `process_items()` — —
- `format_data()` — —
- `pytest_configure()` — —
- `redsl_root()` — —
- `cached_analysis()` — —
- `test_resolve_secret_ref_env()` — —
- `test_resolve_secret_ref_file()` — —
- `test_resolve_secret_ref_file_not_found()` — —
- `test_find_config_root_in_cwd()` — —
- `test_find_config_root_in_parent()` — —
- `test_find_config_root_not_found()` — —
- `test_load_agent_config_from_substrate()` — —
- `test_agent_config_from_substrate_or_env_fallback_to_env()` — —
- `test_agent_config_from_env_uses_substrate_when_available()` — —
- `test_config_bridge_error_messages()` — —
- `test_create_app_registers_single_health_route()` — —
- `test_health_endpoint_returns_expected_payload()` — —
- `test_examples_list_endpoint()` — —
- `test_examples_run_endpoint()` — —
- `test_examples_yaml_endpoint()` — —
- `test_examples_run_unknown_returns_error()` — —
- `test_debug_config_masks_sensitive_environment_values()` — —
- `tmp_git_project()` — —
- `test_awareness_manager_build_snapshot_and_context()` — —
- `test_awareness_manager_snapshot_cache_invalidates_on_memory_change()` — —
- `test_self_model_records_outcome_and_assesses()` — —
- `test_proactive_analyzer_orders_critical_alert_first()` — —
- `test_cli_registers_awareness_commands_and_renders_json()` — —
- `test_root_package_exports_awareness_facade()` — —
- `test_find_packages_finds_real_packages()` — —
- `test_filter_packages_supports_include_and_exclude()` — —
- `test_build_summary_aggregates_correctly()` — —
- `test_resolve_profile_prefers_publish_when_auto()` — —
- `test_resolve_profile_defaults_to_python_when_pipeline_requested()` — —
- `test_compute_verdict_returns_ready_for_dry_run_success()` — —
- `test_compute_verdict_fails_when_dry_run_push_preflight_fails()` — —
- `test_process_project_skips_dirty_repo_when_requested()` — —
- `test_run_pyqual_batch_stops_on_fail_fast()` — —
- `test_run_pyqual_batch_smoke_with_mocked_project_flow()` — —
- `test_save_report_includes_project_notes_for_verdict_reasons_and_errors()` — —
- `test_pyqual_yaml_template_is_valid_yaml()` — —
- `test_pyqual_project_result_defaults()` — —
- `sample_file()` — —
- `test_config_init_validate_and_show()` — —
- `test_config_diff_history_apply_and_clone()` — —
- `test_config_rollback()` — —
- `test_refactor_dry_run_yaml_renders_plan_and_skips_cycle()` — —
- `test_refactor_live_json_emits_payload_and_passes_flags()` — —
- `test_example_list_shows_all_scenarios()` — —
- `test_example_memory_learning_default()` — —
- `test_example_basic_analysis_advanced()` — —
- `test_batch_pyqual_run_help()` — —
- `test_batch_pyqual_run_forwards_options()` — —
- `test_batch_autofix_help()` — —
- `test_secret_interceptor_redacts_and_resolves()` — —
- `test_store_save_load_validate_and_clone()` — —
- `test_applier_apply_and_rollback()` — —
- `test_store_history_can_be_serialized_as_json()` — —
- `test_project()` — —
- `git_project()` — —
- `runner()` — —
- `api_client()` — —
- `basic_analysis_result()` — —
- `custom_rules_result()` — —
- `full_pipeline_result()` — —
- `memory_learning_result()` — —
- `api_integration_result()` — —
- `awareness_result()` — —
- `pyqual_result()` — —
- `audit_result()` — —
- `pr_bot_result()` — —
- `badge_result()` — —
- `test_all_examples_exist()` — —
- `test_examples_have_readme()` — —
- `test_example_yaml_files_exist()` — —
- `test_advanced_examples_run()` — —
- `test_toon_candidate_priority_classifies_known_categories()` — —
- `test_analyze_trends_preserves_cc_alias()` — —
- `test_build_timeline_graceful_fallback_without_git()` — —
- `test_find_degradation_sources_returns_largest_jump_first()` — —
- `test_predict_future_state_returns_degrading_prediction()` — —
- `analyzer()` — —
- `dsl()` — —
- `goal_analysis()` — —
- `pfix_analysis()` — —
- `project_path()` — —
- `test_llm_execution()` — —
- `two_projects()` — —
- `redsl_analysis()` — —
- `redsl_enriched_analysis()` — —
- `test_toon_to_tasks_decisions()` — —
- `test_toon_to_tasks_layers_high_cc()` — —
- `test_refactor_plan_to_tasks()` — —
- `test_generate_planfile_dry_run()` — —
- `test_generate_planfile_writes_yaml()` — —
- `test_generate_planfile_merge_preserves_done()` — —
- `test_cli_planfile_sync_dry_run()` — —
- `test_cli_planfile_show()` — —
- `test_cli_planfile_sync_json_format()` — —
- `record()` — —
- `record_event()` — —
- `decision_signature()` — —
- `has_recent_signature()` — —
- `load_events()` — —
- `filter_by_file()` — —
- `filter_by_type()` — —
- `has_recent_proposal()` — —
- `has_recent_ticket()` — —
- `generate_decision_report()` — —
- `run()` — —
- `stop()` — —
- `is_local()` — —
- `api_key()` — —
- `from_env()` — —
- `add_custom_rules()` — —
- `main()` — —
- `OPENROUTER_API_KEY()` — —
- `print()` — —
- `process_data()` — —
- `print()` — —
- `safe_completion()` — —
- `check_model_policy()` — —
- `generate_readme()` — —
- `main()` — —
- `main()` — —
- `print()` — —
- `print()` — —
- `main()` — —
- `validate()` — —
- `store()` — —
- `lifecycle()` — —
- `retry_with_backoff()` — —
- `main()` — —
- `main()` — —
- `process_order()` — —
- `reconcile_invoice()` — —
- `process_order()` — —
- `main()` — —
- `demo_policy_check()` — Demonstrate checking models against policy.
- `demo_list_allowed()` — Demonstrate listing all allowed models.
- `demo_safe_completion()` — Demonstrate safe completion with policy enforcement.
- `demo_strict_mode()` — Demonstrate strict vs non-strict mode.
- `main()` — Run all demos.
- `print()` — —
- `main()` — —
- `main()` — —
- `process()` — —
- `helper()` — —
- `format()` — —
- `pad()` — —
- `verify()` — —
- `generate_token()` — —
- `process()` — —
- `helper()` — —
- `format()` — —
- `main()` — —
- `main()` — —
- `process_data(data, mode, threshold, callback)` — Very complex function with high CC.
- `process_data_copy(data, mode, threshold, callback)` — Copy of process_data - exact duplicate.
- `calculate(x, y, z)` — —
- `fetchCompanyData()` — —
- `h()` — —
- `extractNip()` — —
- `handleStep1()` — —
- `buildClientData()` — —
- `saveClient()` — —
- `createNdaContract()` — —
- `saveNdaToDatabase()` — —
- `storeStep2Data()` — —
- `handleStep2()` — —
- `generateNDAText()` — —
- `check_http()` — —
- `check_content()` — —
- `check_php_syntax()` — —
- `check_env_exists()` — —
- `check_encryption_key()` — —
- `check_directories()` — —
- `check_admin_auth()` — —
- `check_cron_scripts()` — —
- `env()` — —
- `h()` — —
- `csrf_token()` — —
- `check_rate_limit()` — —
- `h_ce()` — —
- `loadConfig()` — —
- `saveConfig()` — —
- `getNestedValue()` — —
- `getRiskLevel()` — —
- `generateProposalEmail()` — —
- `sendProposalEmail()` — —
- `generateAccessToken()` — —
- `verifyAccessToken()` — —
- `parseSelection()` — —
- `h()` — —
- `h_pp()` — —
- `send_notification()` — —
- `send_notification_smtp()` — —
- `check_status()` — —
- `check_contains()` — —
- `check_not_contains()` — —
- `validateConfig()` — —
- `getHistory()` — —
- `redactSecrets()` — —
- `loadConfig()` — —
- `sendError()` — —
- `handleValidate()` — —
- `handleHistory()` — —
- `computeFingerprint()` — —
- `handleShow()` — —
- `buildDiff()` — —
- `handleDiff()` — —
- `handleNotFound()` — —
- `h()` — —
- `masthead()` — —
- `target()` — —
- `form()` — —
- `emailField()` — —
- `nameField()` — —
- `repoField()` — —
- `submitBtn()` — —
- `setInvalid()` — —
- `validEmail()` — —
- `validRepo()` — —
- `io()` — —
- `details()` — —
- `flash()` — —
- `headline()` — —
- `y()` — —
- `callRedslApi()` — —
- `generateMarkdownReport()` — —
- `formatIssuesForEmail()` — —
- `formatIssuesForGitHub()` — —
- `showTab()` — —
- `copyToClipboard()` — —
- `downloadMarkdown()` — —
- `updateAsyncProgressStep()` — —
- `updateProgressStep()` — —
- `getCqrsStatus()` — —
- `connectWebSocket()` — —
- `h()` — —
- `h()` — —
- `classForLevel()` — —
- `fmtSize()` — —
- `validateCsrfToken()` — —
- `redsl_curl()` — —
- `json_out()` — —
- `resolve_project()` — —
- `build_mcp_subscription_payload()` — —
- `main()` — Run pre-commit validation.
- `parse_sumr()` — —
- `toon_to_tasks()` — —
- `refactor_plan_to_tasks()` — —
- `generate_planfile()` — —
- `process_data()` — —
- `process_data_copy()` — —
- `format_cycle_report_yaml()` — —
- `format_cycle_report_markdown()` — —
- `format_plan_yaml()` — —
- `format_cycle_report_toon()` — —
- `planfile_group()` — —
- `planfile_sync()` — —
- `planfile_show()` — —
- `register()` — —
- `register_models()` — —
- `models_group()` — —
- `pick_coding()` — —
- `list_coding()` — —
- `estimate_cost()` — —
- `show_coding_config()` — —
- `run_autonomous_pr()` — —
- `dispatch_tool()` — —
- `resolve_secret_ref()` — —
- `find_config_root()` — —
- `load_agent_config_from_substrate()` — —
- `agent_config_from_substrate_or_env()` — —
- `parse_config_path()` — —
- `get_nested_value()` — —
- `set_nested_value()` — —
- `remove_nested_value()` — —
- `deep_merge()` — —
- `deep_diff()` — —
- `materialize_diff()` — —
- `walk_paths()` — —
- `validate_with_testql()` — —
- `check_testql_available()` — —
- `ast_max_nesting_depth()` — —
- `ast_cyclomatic_complexity()` — —
- `run_quality_gate()` — —
- `install_pre_commit_hook()` — —
- `check_module_budget()` — —
- `register_model_policy()` — —
- `model_policy()` — —
- `check_model()` — —
- `list_models()` — —
- `refresh_registry()` — —
- `show_config()` — —
- `repair_file()` — —
- `repair_directory()` — —
- `sandbox_available()` — —
- `is_available()` — —
- `doctor()` — —
- `check_gates()` — —
- `get_status()` — —
- `validate_config()` — —
- `init_config()` — —
- `run_pipeline()` — —
- `git_commit()` — —
- `git_push()` — —
- `analyze_with_sumd()` — —
- `render_markdown()` — —
- `create_ticket()` — —
- `list_tickets()` — —
- `report_refactor_results()` — —
- `fix_broken_guards()` — —
- `fix_stolen_indent()` — —
- `fix_broken_fstrings()` — —
- `fix_stale_pycache()` — —
- `fix_missing_install()` — —
- `fix_module_level_exit()` — —
- `fix_version_mismatch()` — —
- `fix_pytest_collision()` — —
- `compute_verdict()` — —
- `process_project()` — —
- `select_model()` — —
- `select_reflection_model()` — —
- `estimate_cycle_cost()` — —
- `apply_provider_prefix()` — —
- `call_via_llx()` — —
- `validate_patch()` — —
- `validate_proposal()` — —
- `blend_confidence()` — —
- `is_radon_available()` — —
- `run_radon_cc()` — —
- `extract_max_cc_per_file()` — —
- `enhance_metrics_with_radon()` — —
- `run_hybrid_quality_refactor()` — —
- `run_hybrid_batch()` — —
- `review_staged_changes()` — —
- `explain_decisions()` — —
- `get_memory_stats()` — —
- `build_ecosystem_context()` — —
- `generate_diff()` — —
- `preview_proposal()` — —
- `create_checkpoint()` — —
- `rollback_to_checkpoint()` — —
- `rollback_single_file()` — —
- `snapshot()` — —
- `compare()` — —
- `compare_snapshots()` — —
- `rollback_working_tree()` — —
- `validate_no_regression()` — —
- `validate_working_tree()` — —
- `scan_duplicates()` — —
- `scan_as_toon()` — —
- `enrich_analysis()` — —
- `get_refactor_suggestions()` — —
- `build_selector()` — —
- `select_model_for_operation()` — —
- `get_selector()` — —
- `invalidate_selector()` — —
- `track_model_selection()` — —
- `check_cost_per_call()` — —
- `diagnose()` — —
- `heal()` — —
- `heal_batch()` — —
- `detect_broken_guards()` — —
- `detect_stolen_indent()` — —
- `detect_broken_fstrings()` — —
- `detect_stale_pycache()` — —
- `detect_missing_install()` — —
- `detect_module_level_exit()` — —
- `detect_version_mismatch()` — —
- `detect_pytest_cli_collision()` — —
- `run_pyqual_batch()` — —
- `is_sensitive_key()` — —
- `mask_sensitive_mapping()` — —
- `scan_folder()` — —
- `analyze_commit_intent()` — —
- `run_pyqual_example()` — —
- `main()` — —
- `print_llm_banner()` — —
- `auto_fix_violations()` — —
- `get_gate()` — —
- `safe_completion()` — —
- `check_model_policy()` — —
- `list_allowed_models()` — —
- `get_changed_files()` — —
- `get_staged_files()` — —
- `run_pyqual_analysis()` — —
- `run_pyqual_fix()` — —
- `run_pr_bot_example()` — —
- `smart_score()` — —
- `collect_autonomy_metrics()` — —
- `save_metrics()` — —
- `load_metrics()` — —
- `format_refactor_plan()` — —
- `config()` — —
- `config_init()` — —
- `config_validate()` — —
- `config_diff()` — —
- `config_history()` — —
- `config_apply()` — —
- `config_clone()` — —
- `config_show()` — —
- `config_rollback()` — —
- `register_config()` — —
- `format_batch_results()` — —
- `format_batch_report_markdown()` — —
- `run_cycle()` — —
- `run_from_toon_content()` — —
- `process_order()` — —
- `run_autofix_batch()` — —
- `run_custom_rules_example()` — —
- `run_badge_example()` — —
- `run_awareness_example()` — —
- `profile_refactor_cycle()` — —
- `profile_llm_latency()` — —
- `profile_memory_operations()` — —
- `generate_optimization_report()` — —
- `format_debug_info()` — —
- `scan()` — —
- `run_memory_learning_example()` — —
- `refactor()` — —
- `register_refactor()` — —
- `generate_github_workflow()` — —
- `install_github_workflow()` — —
- `cmd_analyze()` — —
- `cmd_explain()` — —
- `cmd_refactor()` — —
- `cmd_memory_stats()` — —
- `cmd_serve()` — —
- `setup_logging()` — —
- `main_loop()` — —
- `demo_policy_check()` — —
- `demo_list_allowed()` — —
- `demo_safe_completion()` — —
- `demo_strict_mode()` — —
- `get_risk_level()` — —
- `search_schema_matches()` — —
- `run_multi_analysis()` — —
- `generate_toon_files()` — —
- `read_toon_contents()` — —
- `analyze_with_code2llm()` — —
- `maybe_analyze()` — —
- `calculate_area()` — —
- `process_items()` — —
- `format_data()` — —
- `calculate()` — —
- `run_semcod_batch()` — —
- `apply_refactor()` — —
- `measure_todo_reduction()` — —
- `run_cmd()` — —
- `git_status_lines()` — —
- `resolve_profile()` — —
- `build_pyqual_fix_decisions()` — —
- `load_example_yaml()` — —
- `list_available_examples()` — —
- `print_banner()` — —
- `parse_scenario()` — —
- `run_audit_example()` — —
- `example()` — —
- `example_basic_analysis()` — —
- `example_custom_rules()` — —
- `example_full_pipeline()` — —
- `example_memory_learning()` — —
- `example_api_integration()` — —
- `example_awareness()` — —
- `example_pyqual()` — —
- `example_audit()` — —
- `example_pr_bot()` — —
- `example_badge()` — —
- `example_list()` — —
- `register_examples()` — —
- `execute_sandboxed()` — —
- `extract_json_block()` — —
- `run_full_pipeline_example()` — —
- `handle_push_webhook()` — —
- `main_function()` — —
- `validate_data()` — —
- `save_data()` — —
- `log_error()` — —
- `run_basic_analysis_example()` — —
- `perf_command()` — —
- `cost_command()` — —
- `debug()` — —
- `debug_ast()` — —
- `debug_llm()` — —
- `debug_metrics()` — —
- `register_debug()` — —
- `batch()` — —
- `batch_semcod()` — —
- `batch_hybrid()` — —
- `batch_autofix()` — —
- `batch_pyqual_run()` — —
- `register_batch()` — —
- `export_proposal_schema()` — —
- `proposal_to_yaml()` — —
- `run_api_integration_example()` — —
- `is_tool_available()` — —
- `build_default_config()` — —
- `config_doc_to_yaml()` — —
- `export_config_schema()` — —
- `pyqual()` — —
- `pyqual_analyze()` — —
- `pyqual_fix()` — —
- `register_pyqual()` — —
- `cli()` — —
- `create_app()` — —
- `main_loop()` — Punkt wejścia dla pętli ciągłej.
- `cmd_analyze(project_dir)` — Analiza projektu — wyświetl metryki i alerty.
- `cmd_explain(project_dir)` — Wyjaśnij decyzje refaktoryzacji bez ich wykonywania.
- `cmd_refactor(project_dir, dry_run, auto, max_actions)` — Uruchom cykl refaktoryzacji.
- `cmd_memory_stats()` — Statystyki pamięci agenta.
- `cmd_serve(port, host)` — Uruchom serwer API.
- `main()` — Główny punkt wejścia CLI.
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
- `merge_tasks(existing_tasks, incoming_issues, source_id)` — Merge incoming GitHub issues into existing local tasks for one source.
- `apply_planfile_sources(planfile_path, dry_run)` — Read planfile.yaml, sync all github sources, write result.
- `run_multi_analysis(project_dirs, config)` — Convenience function — analiza wielu projektów.
- `resolve_auth_ref(auth_ref)` — Resolve an auth_ref string to a plaintext token.
- `fingerprint_issue(issue)` — Compute a stable fingerprint of the externally-visible issue state.
- `fetch_issues(source_config)` — Fetch issues from GitHub according to source_config.
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
- `run_cmd(cmd, cwd, timeout)` — Run a shell command and return the result.
- `git_status_lines(project)` — Return non-empty git status lines for *project*, or [] on error.
- `resolve_profile(requested_profile, run_pipeline, publish)` — Resolve the effective pyqual profile based on CLI options.
- `process_project(project, max_fixes, run_pipeline, git_push)` — Full ReDSL + pyqual pipeline for a single project.
- `run_autofix_batch(semcod_root, max_changes)` — Run full autofix pipeline on all semcod packages.
- `extract_refactor_decisions(toon_content, source, _next_id)` — Extract tasks from refactor cycle TOON (DECISIONS[] section).
- `extract_complexity_layers(toon_content, source, _next_id, project_path)` — Extract tasks from code analysis TOON (LAYERS with high CC).
- `extract_duplications(toon_content, source, _next_id)` — Extract tasks from Duplication TOON (DUPLICATES section).
- `refactor_plan_to_tasks(yaml_content, source)` — Convert a redsl ``refactor_plan.yaml`` to PlanTask list.
- `toon_to_tasks(toon_content, source, project_path)` — Extract PlanTask list from TOON-format content.
- `parse_sumr(path)` — Parse a SUMR.md file and extract refactoring-relevant data.
- `parse_refactor_plan_yaml(yaml_content, source)` — Parse refactor_plan.yaml content into raw task dicts.
- `get_toon_patterns()` — Get all TOON parsing regex patterns.
- `refactor_plan_to_tasks(yaml_content, source)` — Backward-compat alias: parse refactor_plan.yaml → list[PlanTask].
- `make_id_generator()` — Return a closure that generates sequential IDs with given prefix.
- `deduplicate_tasks(tasks)` — Remove duplicate tasks with same (action, file) pair.
- `merge_with_existing_planfile(tasks, planfile_path)` — Merge task statuses with existing planfile (preserve in_progress/done).
- `tasks_to_planfile_yaml(tasks, project_name, project_version, sources)` — Serialise tasks to planfile.yaml YAML string.
- `generate_planfile(project_path)` — Generate or update planfile.yaml for *project_path* from SUMR.md.
- `run_pyqual_analysis(project_path, config_path, output_format)` — Run pyqual analysis on a project.
- `run_pyqual_fix(project_path, config_path)` — Run automatic fixes based on pyqual analysis.
- `build_pyqual_fix_decisions(issues, project_path)` — Build direct-refactor Decisions grouped by file from pyqual issues.
- `run_autonomous_pr(git_url, max_actions, dry_run, auto_apply)` — Run the autonomous PR workflow.
- `dispatch_tool(tool_name, arguments)` — Route an LLM tool call to the correct handler.
- `export_proposal_schema()` — —
- `proposal_to_yaml(proposal)` — —
- `get_risk_level(path)` — Return risk level for a config path. Falls back to 'low' for unknown paths.
- `search_schema_matches(query)` — Return catalog entries matching *query* across path/title/description/aliases.
- `is_sensitive_key(key)` — —
- `mask_sensitive_mapping(data)` — Return a shallow copy with secret-like values masked.
- `resolve_secret_ref(secret)` — Resolve a secret reference to its actual value.
- `find_config_root(start_path)` — Find redsl-config directory by walking up from start_path or cwd.
- `load_agent_config_from_substrate(config_root, profile)` — Load AgentConfig from config substrate, resolving secrets.
- `agent_config_from_substrate_or_env(config_root, profile)` — Try substrate first, fall back to env-based config.
- `parse_config_path(path)` — Parse a dotted / indexed config path into navigation tokens.
- `get_nested_value(data, path)` — —
- `set_nested_value(data, path, value)` — —
- `remove_nested_value(data, path)` — —
- `deep_merge(base, overlay)` — Recursively merge *overlay* into *base* and return a new object.
- `deep_diff(base, current)` — Return the minimal overlay needed to transform *base* into *current*.
- `materialize_diff(base, current)` — Public wrapper around :func:`deep_diff` that always returns JSON-friendly data.
- `walk_paths(data, prefix)` — Yield dotted paths for scalar leaves in a nested mapping/list tree.
- `build_default_config()` — —
- `config_doc_to_yaml(document)` — —
- `export_config_schema()` — —
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
- `run_audit_example(scenario, source)` — —
- `main(argv)` — —
- `run_pr_bot_example(scenario, source)` — —
- `main(argv)` — —
- `run_memory_learning_example(scenario, source)` — —
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
- `auto_fix_violations(project_dir, violations)` — Try to automatically fix each violation; create ticket on failure.
- `check_module_budget(file_path, module_type)` — Check whether a module stays within its complexity budget.
- `format_refactor_plan(decisions, format, analysis)` — Format refactoring plan in specified format.
- `format_cycle_report_yaml(report, decisions, analysis)` — Format full cycle report as YAML for stdout.
- `format_cycle_report_markdown(report, decisions, analysis, project_path)` — Format a refactor cycle as a Markdown report.
- `format_plan_yaml(decisions, analysis)` — Format dry-run plan as YAML for stdout.
- `format_cycle_report_toon(report, decisions, analysis, project_path)` — Format a refactor cycle as TOON for planfile integration.
- `format_debug_info(info, format)` — Format debug information.
- `format_batch_results(results, format)` — Format batch processing results.
- `format_batch_report_markdown(report, root, title)` — Format a batch run report as Markdown.
- `print_llm_banner()` — Print the LLM config banner to stderr.
- `config()` — Config substrate commands for manifests, profiles and audit logs.
- `config_init(root, name, profile, force)` — Initialize a new redsl-config layout.
- `config_validate(root, output_format)` — Validate a config manifest against the standard.
- `config_diff(root, against, output_format)` — Diff current config against another config file or root.
- `config_history(root, limit, output_format)` — Show the append-only config audit history.
- `config_apply(root, proposal_path, actor, user)` — Apply a ConfigChangeProposal atomically.
- `config_clone(source, target, profile, replace_secrets)` — Clone a config substrate locally.
- `config_show(root, output_format)` — Print the current manifest.
- `config_rollback(root, to_version, output_format)` — Rollback config to a previous version atomically.
- `register_config(cli)` — —
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
- `events_group()` — Browse and analyze .redsl/history.jsonl decision events.
- `events_show(project, event_type, last_n, target_file)` — Show decision events for a project from .redsl/history.jsonl.
- `events_summary(project)` — Print a statistical summary of all recorded events.
- `events_cycles(project)` — Show per-cycle summary from cycle_started / cycle_completed events.
- `register(cli_group)` — —
- `cli(ctx, verbose)` — reDSL - Automated code refactoring tool.
- `scan(ctx, folder, output_path, quiet)` — Scan a folder of projects and produce a markdown priority report.
- `refactor(ctx, project_path, max_actions, dry_run)` — Run refactoring on a project.
- `register_refactor(cli)` — —
- `setup_logging(project_path, verbose)` — Route all logging to a timestamped log file, keep stdout clean.
- `register(cli_group)` — —
- `deploy()` — Infrastructure deployment via redeploy (detect → plan → apply).
- `deploy_detect(host, app, domain, output)` — Probe infrastructure on HOST and save infra.yaml.
- `deploy_plan(infra, target, strategy, domain)` — Generate migration-plan.yaml from infra.yaml + desired state.
- `deploy_apply(plan_file, dry_run, step)` — Execute a migration-plan.yaml.
- `deploy_run(spec, dry_run, plan_only, do_detect)` — Run full pipeline from a migration spec YAML (source + target in one file).
- `deploy_migrate(host, app, domain, strategy)` — Full detect → plan → apply on HOST in one command.
- `register_model_policy(cli)` — Register model-policy commands.
- `model_policy()` — Manage LLM model age and lifecycle policy.
- `check_model(model, json_output)` — Check if a model is allowed by policy.
- `list_models(max_age, provider, json_output, limit)` — List models currently allowed by policy.
- `refresh_registry()` — Force refresh model registry from sources.
- `show_config()` — Show current model policy configuration.
- `perf_command(ctx, project_path)` — Profile a refactoring cycle and report performance bottlenecks.
- `cost_command(ctx, project_path, max_actions)` — Estimate LLM cost for the next refactoring cycle without running it.
- `register_models(cli)` — Register model selection commands.
- `models_group()` — Model selection for coding - cheapest suitable model.
- `pick_coding(tier, min_context, require_tools, show_all)` — Pokaż jaki model zostałby wybrany dla danego tieru.
- `list_coding(tier, limit, show_rejected, sort)` — Tabela modeli spełniających wymagania coding, posortowana po cenie.
- `estimate_cost(tier, input_tokens, output_tokens, ops_per_day)` — Estimate monthly cost for given tier and usage pattern.
- `show_coding_config()` — Show current coding model selection configuration.
- `planfile_group()` — SUMR.md → planfile.yaml task generation.
- `planfile_sync(project_path, sumr_path, dry_run, no_merge)` — Generate or update planfile.yaml from SUMR.md.
- `planfile_show(project_path, status, output_format)` — Show tasks from an existing planfile.yaml.
- `auth_group()` — Manage authentication credentials for planfile sources.
- `auth_github()` — GitHub authentication helpers.
- `auth_github_login(token, env_var)` — Store a GitHub token for planfile sync.
- `source_group()` — Manage task sources (GitHub, SUMR) in planfile.yaml.
- `source_list(project_path)` — List configured sources in planfile.yaml.
- `source_remove(source_id, project_path)` — Remove a source from planfile.yaml.
- `source_add(repo, auth_ref, labels, state)` — Add a GitHub source to planfile.yaml.
- `planfile_gh_sync(project_path, dry_run, output_format)` — Fetch GitHub issues into planfile.yaml (three-way merge).
- `planfile_validate(project_path, fix, as_json)` — Check whether planfile.yaml tickets are still current.
- `register(cli_group)` — —
- `workflow_group()` — Manage redsl.yaml — declarative refactor pipeline config.
- `workflow_init(project_dir, name, force)` — Generate redsl.yaml in PROJECT_DIR.
- `workflow_show(project_dir)` — Show effective workflow config for PROJECT_DIR (resolved with fallbacks).
- `workflow_scan(project_dir, write, print_only)` — Scan PROJECT_DIR and build a map of configuration files.
- `register(cli_group)` — —
- `debug()` — Debug utilities for development.
- `debug_ast(project_path, file)` — Show AST analysis for debugging.
- `debug_llm(prompt, model)` — Test LLM with a simple prompt.
- `debug_metrics(project_path)` — Show project metrics for debugging.
- `register_debug(cli)` — —
- `batch()` — Batch refactoring commands.
- `batch_semcod(semcod_root, max_actions, format)` — Apply refactoring to semcod projects.
- `batch_hybrid(semcod_root, max_changes)` — Apply hybrid quality refactorings (no LLM needed).
- `batch_autofix(ctx, semcod_root, max_changes)` — Auto-fix all packages: scan -> generate TODO.md -> apply hybrid fixes -> gate fix.
- `batch_pyqual_run(ctx, workspace_root, max_fixes, limit)` — Multi-project quality pipeline: ReDSL analysis + pyqual gates + optional push.
- `register_batch(cli)` — —
- `run_tasks_from_planfile(orchestrator, project_dir, max_actions, use_code2llm)` — Iterate over planfile todo tasks and run refactor for each file directly.
- `explain_decisions(orchestrator, project_dir, limit)` — Explain refactoring decisions without executing them.
- `get_memory_stats(orchestrator)` — Return memory and runtime statistics for the orchestrator.
- `estimate_cycle_cost(orchestrator, project_dir, max_actions)` — Estimate the cost of the next cycle without executing it.
- `mark_applied_tasks_done(project_dir, applied_files)` — Mark planfile tasks whose ``file:`` matches applied files as done.
- `get_todo_tasks(project_dir)` — Return list of todo tasks from planfile.yaml, sorted by priority (ascending).
- `add_quality_task(project_dir, title, description, priority)` — Append a new todo task to planfile.yaml for quality improvement.
- `add_decision_tasks(project_dir, decisions, source, priority)` — Convert refactor decisions into todo tasks in planfile.yaml.
- `execute_sandboxed(orchestrator, decision, project_dir)` — Execute a decision in a sandboxed environment.
- `ensure_gitignore(project_dir)` — Add .redsl/ to project .gitignore if not already present.
- `list_backups(project_dir)` — Return all ``.bak`` files stored in ``.redsl/backups/``.
- `has_backups(project_dir)` — —
- `cleanup_backups(project_dir)` — Remove all backups after a successful cycle.
- `rollback_from_backups(project_dir)` — Restore all backed-up files to their original locations.
- `scan_project(project_dir)` — Scan *project_dir* and return a :class:`ProjectMap`.
- `project_map_to_yaml_block(pm, indent)` — Render a ProjectMap as a YAML block suitable for embedding in redsl.yaml.
- `run_cycle(orchestrator, project_dir, max_actions, use_code2llm)` — Run a complete refactoring cycle driven by WorkflowConfig.
- `run_from_toon_content(orchestrator, project_toon, duplication_toon, validation_toon)` — Run a cycle from pre-parsed toon content.
- `default_workflow()` — —
- `load_workflow(project_dir)` — Load workflow config for *project_dir*.
- `detect_deploy_config(project_dir)` — Auto-detect push/publish mechanisms for *project_dir*.
- `run_deploy_action(action, project_dir, dry_run)` — Execute a single deploy action. Returns True on success.
- `is_available()` — Return True if the redeploy package is installed and importable.
- `detect(host, app, domain)` — Probe infrastructure on *host* and return InfraState as a dict.
- `detect_and_save(host, output, app, domain)` — Run detect and save InfraState YAML to *output*.  Returns same dict as :func:`detect`.
- `plan(infra_path, target_path)` — Generate a MigrationPlan from *infra_path* + optional *target_path*.
- `plan_from_spec(spec_path)` — Generate a MigrationPlan from a single migration spec YAML (source + target).
- `plan_and_save(infra_path, output, target_path)` — Like :func:`plan` but also saves the plan YAML to *output*.
- `apply(plan_path)` — Execute a MigrationPlan from *plan_path*.
- `run_spec(spec_path)` — Run the full pipeline from a migration spec YAML (source + target).
- `migrate(host)` — Full detect → plan → apply pipeline without intermediate YAML files.
- `get_gate()` — Get or create the global ModelAgeGate singleton.
- `safe_completion(model)` — Drop-in replacement for litellm.completion with policy enforcement.
- `check_model_policy(model)` — Check if a model is allowed without making an LLM call.
- `list_allowed_models()` — List all models currently allowed by policy.
- `select_model(action, context, budget_remaining)` — Wybierz optymalny model na podstawie akcji i kontekstu.
- `select_reflection_model(use_local)` — Wybierz model do refleksji — zawsze tańszy.
- `estimate_cycle_cost(decisions, contexts)` — Szacuj koszt całego cyklu refaktoryzacji — lista per decyzja.
- `apply_provider_prefix(model, configured_model)` — Apply provider prefix from configured model to a bare model name.
- `call_via_llx(messages, task_type)` — Deleguj wywołanie LLM do llx CLI jeśli dostępne.
- `select_model_for_operation(operation)` — Mapping: 'extract_function' → tier z .env → konkretny model.
- `build_selector(aggregator, gate)` — Build ModelSelector from environment configuration.
- `get_selector()` — Get or build the global ModelSelector.
- `invalidate_selector()` — Invalidate the global selector cache (e.g., after config change).
- `track_model_selection(model, tier, operation)` — Track model selection for metrics.
- `check_cost_per_call(estimated_cost_usd)` — Check if cost is within safety limits.
- `check_hard_requirements(info, req)` — Check if model meets hard requirements.
- `score_quality(info)` — Syntetyczna jakość 0-100 z dostępnych sygnałów.
- `apply_strategy(candidates, strategy)` — Apply selection strategy to candidates.
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
- `tune(project_dir, aggressive, conservative, dry_run)` — Run `pyqual tune` to auto-adjust quality gate thresholds.
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
- `is_tool_available(cmd, timeout)` — Return True if running *cmd* exits with code 0 within *timeout* seconds.
- `extract_json_block(text)` — Extract first JSON block from *text*, skipping preamble lines.
- `ast_max_nesting_depth(node)` — Oblicz max glębokość zagnieżdżenia pętli/warunków — nie wchodzi w zagnieżdżone def/class.
- `ast_cyclomatic_complexity(node)` — Oblicz CC dla funkcji — nie wchodzi w zagnieżdżone definicje funkcji/klas.
- `analyze_with_sumd(project_dir)` — Analyze project using sumd if available, fallback to native analyzer.
- `get_changed_files(project_dir, since)` — Pobierz listę zmienionych plików .py od podanego commita/ref.
- `get_staged_files(project_dir)` — Pobierz listę staged plików .py (git diff --cached).
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
- `planfile_group()` — —
- `planfile_sync()` — —
- `planfile_show()` — —
- `auth_group()` — —
- `auth_github()` — —
- `auth_github_login()` — —
- `source_group()` — —
- `source_list()` — —
- `source_remove()` — —
- `source_add()` — —
- `planfile_gh_sync()` — —
- `planfile_validate()` — —
- `register()` — —
- `process_data()` — —
- `process_data_copy()` — —
- `events_group()` — —
- `events_show()` — —
- `events_summary()` — —
- `events_cycles()` — —
- `callRedslApi()` — —
- `generateMarkdownReport()` — —
- `formatIssuesForEmail()` — —
- `formatIssuesForGitHub()` — —
- `showTab()` — —
- `copyToClipboard()` — —
- `downloadMarkdown()` — —
- `updateAsyncProgressStep()` — —
- `updateProgressStep()` — —
- `getCqrsStatus()` — —
- `connectWebSocket()` — —
- `run_cycle()` — —
- `run_from_toon_content()` — —
- `masthead()` — —
- `target()` — —
- `form()` — —
- `emailField()` — —
- `nameField()` — —
- `repoField()` — —
- `submitBtn()` — —
- `setInvalid()` — —
- `validEmail()` — —
- `validRepo()` — —
- `io()` — —
- `details()` — —
- `flash()` — —
- `headline()` — —
- `y()` — —
- `mark_applied_tasks_done()` — —
- `get_todo_tasks()` — —
- `add_quality_task()` — —
- `add_decision_tasks()` — —
- `detect_deploy_config()` — —
- `run_deploy_action()` — —
- `redsl_curl()` — —
- `json_out()` — —
- `resolve_project()` — —
- `build_mcp_subscription_payload()` — —
- `deploy()` — —
- `deploy_detect()` — —
- `deploy_plan()` — —
- `deploy_apply()` — —
- `deploy_run()` — —
- `deploy_migrate()` — —
- `dispatch_tool()` — —
- `resolve_secret_ref()` — —
- `find_config_root()` — —
- `load_agent_config_from_substrate()` — —
- `agent_config_from_substrate_or_env()` — —
- `parse_config_path()` — —
- `get_nested_value()` — —
- `set_nested_value()` — —
- `remove_nested_value()` — —
- `deep_merge()` — —
- `deep_diff()` — —
- `materialize_diff()` — —
- `walk_paths()` — —
- `register_models()` — —
- `models_group()` — —
- `pick_coding()` — —
- `list_coding()` — —
- `estimate_cost()` — —
- `show_coding_config()` — —
- `validate_with_testql()` — —
- `check_testql_available()` — —
- `ast_max_nesting_depth()` — —
- `ast_cyclomatic_complexity()` — —
- `fetchCompanyData()` — —
- `h()` — —
- `extractNip()` — —
- `handleStep1()` — —
- `buildClientData()` — —
- `saveClient()` — —
- `createNdaContract()` — —
- `saveNdaToDatabase()` — —
- `storeStep2Data()` — —
- `handleStep2()` — —
- `generateNDAText()` — —
- `extract_refactor_decisions()` — —
- `extract_complexity_layers()` — —
- `extract_duplications()` — —
- `refactor_plan_to_tasks()` — —
- `toon_to_tasks()` — —
- `generate_planfile()` — —
- `run_quality_gate()` — —
- `install_pre_commit_hook()` — —
- `check_module_budget()` — —
- `register_model_policy()` — —
- `model_policy()` — —
- `check_model()` — —
- `list_models()` — —
- `refresh_registry()` — —
- `show_config()` — —
- `repair_file()` — —
- `repair_directory()` — —
- `sandbox_available()` — —
- `is_available()` — —
- `doctor()` — —
- `check_gates()` — —
- `get_status()` — —
- `validate_config()` — —
- `init_config()` — —
- `run_pipeline()` — —
- `git_commit()` — —
- `git_push()` — —
- `tune()` — —
- `analyze_with_sumd()` — —
- `render_markdown()` — —
- `create_ticket()` — —
- `list_tickets()` — —
- `report_refactor_results()` — —
- `fix_broken_guards()` — —
- `fix_stolen_indent()` — —
- `fix_broken_fstrings()` — —
- `fix_stale_pycache()` — —
- `fix_missing_install()` — —
- `fix_module_level_exit()` — —
- `fix_version_mismatch()` — —
- `fix_pytest_collision()` — —
- `resolve_auth_ref()` — —
- `fingerprint_issue()` — —
- `fetch_issues()` — —
- `compute_verdict()` — —
- `process_project()` — —
- `make_id_generator()` — —
- `deduplicate_tasks()` — —
- `merge_with_existing_planfile()` — —
- `tasks_to_planfile_yaml()` — —
- `select_model()` — —
- `select_reflection_model()` — —
- `estimate_cycle_cost()` — —
- `apply_provider_prefix()` — —
- `call_via_llx()` — —
- `validate_patch()` — —
- `validate_proposal()` — —
- `blend_confidence()` — —
- `is_radon_available()` — —
- `run_radon_cc()` — —
- `extract_max_cc_per_file()` — —
- `enhance_metrics_with_radon()` — —
- `validateConfig()` — —
- `getHistory()` — —
- `redactSecrets()` — —
- `loadConfig()` — —
- `sendError()` — —
- `handleValidate()` — —
- `handleHistory()` — —
- `computeFingerprint()` — —
- `handleShow()` — —
- `buildDiff()` — —
- `handleDiff()` — —
- `handleNotFound()` — —
- `run_hybrid_quality_refactor()` — —
- `run_hybrid_batch()` — —
- `review_staged_changes()` — —
- `format_cycle_report_yaml()` — —
- `format_cycle_report_markdown()` — —
- `format_plan_yaml()` — —
- `format_cycle_report_toon()` — —
- `workflow_group()` — —
- `workflow_init()` — —
- `workflow_show()` — —
- `workflow_scan()` — —
- `explain_decisions()` — —
- `get_memory_stats()` — —
- `detect()` — —
- `detect_and_save()` — —
- `plan()` — —
- `plan_from_spec()` — —
- `plan_and_save()` — —
- `apply()` — —
- `run_spec()` — —
- `migrate()` — —
- `apply_strategy()` — —
- `generate_diff()` — —
- `preview_proposal()` — —
- `create_checkpoint()` — —
- `rollback_to_checkpoint()` — —
- `rollback_single_file()` — —
- `build_ecosystem_context()` — —
- `snapshot()` — —
- `compare()` — —
- `compare_snapshots()` — —
- `rollback_working_tree()` — —
- `validate_no_regression()` — —
- `validate_working_tree()` — —
- `scan_duplicates()` — —
- `scan_as_toon()` — —
- `enrich_analysis()` — —
- `get_refactor_suggestions()` — —
- `diagnose()` — —
- `heal()` — —
- `heal_batch()` — —
- `scan_folder()` — —
- `merge_tasks()` — —
- `apply_planfile_sources()` — —
- `detect_broken_guards()` — —
- `detect_stolen_indent()` — —
- `detect_broken_fstrings()` — —
- `detect_stale_pycache()` — —
- `detect_missing_install()` — —
- `detect_module_level_exit()` — —
- `detect_version_mismatch()` — —
- `detect_pytest_cli_collision()` — —
- `run_pyqual_batch()` — —
- `parse_sumr()` — —
- `parse_refactor_plan_yaml()` — —
- `get_toon_patterns()` — —
- `run_autonomous_pr()` — —
- `is_sensitive_key()` — —
- `mask_sensitive_mapping()` — —
- `run_pyqual_example()` — —
- `main()` — —
- `analyze_commit_intent()` — —
- `auto_fix_violations()` — —
- `print_llm_banner()` — —
- `scan_project()` — —
- `project_map_to_yaml_block()` — —
- `default_workflow()` — —
- `load_workflow()` — —
- `get_gate()` — —
- `safe_completion()` — —
- `check_model_policy()` — —
- `list_allowed_models()` — —
- `get_changed_files()` — —
- `get_staged_files()` — —
- `run_pyqual_analysis()` — —
- `run_pyqual_fix()` — —
- `run_pr_bot_example()` — —
- `collect_autonomy_metrics()` — —
- `save_metrics()` — —
- `load_metrics()` — —
- `smart_score()` — —
- `format_refactor_plan()` — —
- `format_batch_results()` — —
- `format_batch_report_markdown()` — —
- `config()` — —
- `config_init()` — —
- `config_validate()` — —
- `config_diff()` — —
- `config_history()` — —
- `config_apply()` — —
- `config_clone()` — —
- `config_show()` — —
- `config_rollback()` — —
- `register_config()` — —
- `ensure_gitignore()` — —
- `list_backups()` — —
- `has_backups()` — —
- `cleanup_backups()` — —
- `rollback_from_backups()` — —
- `generateProposalEmail()` — —
- `sendProposalEmail()` — —
- `generateAccessToken()` — —
- `verifyAccessToken()` — —
- `cmd_analyze()` — —
- `cmd_explain()` — —
- `cmd_refactor()` — —
- `cmd_memory_stats()` — —
- `cmd_serve()` — —
- `run_autofix_batch()` — —
- `run_badge_example()` — —
- `run_custom_rules_example()` — —
- `run_awareness_example()` — —
- `run_memory_learning_example()` — —
- `profile_refactor_cycle()` — —
- `profile_llm_latency()` — —
- `profile_memory_operations()` — —
- `generate_optimization_report()` — —
- `format_debug_info()` — —
- `scan()` — —
- `setup_logging()` — —
- `generate_github_workflow()` — —
- `install_github_workflow()` — —
- `refactor()` — —
- `register_refactor()` — —
- `demo_policy_check()` — —
- `demo_list_allowed()` — —
- `demo_safe_completion()` — —
- `demo_strict_mode()` — —
- `send_notification()` — —
- `send_notification_smtp()` — —
- `classForLevel()` — —
- `fmtSize()` — —
- `validateCsrfToken()` — —
- `main_loop()` — —
- `run_multi_analysis()` — —
- `get_risk_level()` — —
- `search_schema_matches()` — —
- `run_tasks_from_planfile()` — —
- `check_hard_requirements()` — —
- `score_quality()` — —
- `generate_toon_files()` — —
- `read_toon_contents()` — —
- `analyze_with_code2llm()` — —
- `maybe_analyze()` — —
- `calculate()` — —
- `h_ce()` — —
- `saveConfig()` — —
- `getNestedValue()` — —
- `getRiskLevel()` — —
- `run_semcod_batch()` — —
- `apply_refactor()` — —
- `measure_todo_reduction()` — —
- `run_cmd()` — —
- `git_status_lines()` — —
- `resolve_profile()` — —
- `build_pyqual_fix_decisions()` — —
- `run_full_pipeline_example()` — —
- `load_example_yaml()` — —
- `list_available_examples()` — —
- `print_banner()` — —
- `parse_scenario()` — —
- `run_audit_example()` — —
- `example()` — —
- `example_basic_analysis()` — —
- `example_custom_rules()` — —
- `example_full_pipeline()` — —
- `example_memory_learning()` — —
- `example_api_integration()` — —
- `example_awareness()` — —
- `example_pyqual()` — —
- `example_audit()` — —
- `example_pr_bot()` — —
- `example_badge()` — —
- `example_list()` — —
- `register_examples()` — —
- `execute_sandboxed()` — —
- `build_selector()` — —
- `get_selector()` — —
- `invalidate_selector()` — —
- `extract_json_block()` — —
- `handle_push_webhook()` — —
- `env()` — —
- `csrf_token()` — —
- `check_rate_limit()` — —
- `parseSelection()` — —
- `export_proposal_schema()` — —
- `proposal_to_yaml()` — —
- `run_basic_analysis_example()` — —
- `perf_command()` — —
- `cost_command()` — —
- `debug()` — —
- `debug_ast()` — —
- `debug_llm()` — —
- `debug_metrics()` — —
- `register_debug()` — —
- `batch()` — —
- `batch_semcod()` — —
- `batch_hybrid()` — —
- `batch_autofix()` — —
- `batch_pyqual_run()` — —
- `register_batch()` — —
- `select_model_for_operation()` — —
- `run_api_integration_example()` — —
- `track_model_selection()` — —
- `check_cost_per_call()` — —
- `is_tool_available()` — —
- `h_pp()` — —
- `build_default_config()` — —
- `config_doc_to_yaml()` — —
- `export_config_schema()` — —
- `pyqual()` — —
- `pyqual_analyze()` — —
- `pyqual_fix()` — —
- `register_pyqual()` — —
- `cli()` — —
- `create_app()` — —
- `record()` — —
- `record_event()` — —
- `decision_signature()` — —
- `has_recent_signature()` — —
- `load_events()` — —
- `filter_by_file()` — —
- `filter_by_type()` — —
- `has_recent_proposal()` — —
- `has_recent_ticket()` — —
- `generate_decision_report()` — —
- `run()` — —
- `stop()` — —
- `is_local()` — —
- `api_key()` — —
- `from_env()` — —
- `add_custom_rules()` — —
- `OPENAI_API_KEY()` — —
- `process_order()` — —
- `generate_behavior_tests()` — —
- `generate_snapshot_test()` — —
- `verify_behavior_preserved()` — —
- `discover_test_command()` — —
- `run_tests()` — —
- `validate_refactor()` — —
- `calculate_area()` — —
- `process_items()` — —
- `format_data()` — —
- `pytest_configure()` — —
- `redsl_root()` — —
- `cached_analysis()` — —
- `test_resolve_secret_ref_env()` — —
- `test_resolve_secret_ref_file()` — —
- `test_resolve_secret_ref_file_not_found()` — —
- `test_find_config_root_in_cwd()` — —
- `test_find_config_root_in_parent()` — —
- `test_find_config_root_not_found()` — —
- `test_load_agent_config_from_substrate()` — —
- `test_agent_config_from_substrate_or_env_fallback_to_env()` — —
- `test_agent_config_from_env_uses_substrate_when_available()` — —
- `test_config_bridge_error_messages()` — —
- `test_create_app_registers_single_health_route()` — —
- `test_health_endpoint_returns_expected_payload()` — —
- `test_examples_list_endpoint()` — —
- `test_examples_run_endpoint()` — —
- `test_examples_yaml_endpoint()` — —
- `test_examples_run_unknown_returns_error()` — —
- `test_debug_config_masks_sensitive_environment_values()` — —
- `tmp_git_project()` — —
- `test_awareness_manager_build_snapshot_and_context()` — —
- `test_awareness_manager_snapshot_cache_invalidates_on_memory_change()` — —
- `test_self_model_records_outcome_and_assesses()` — —
- `test_proactive_analyzer_orders_critical_alert_first()` — —
- `test_cli_registers_awareness_commands_and_renders_json()` — —
- `test_root_package_exports_awareness_facade()` — —
- `test_find_packages_finds_real_packages()` — —
- `test_filter_packages_supports_include_and_exclude()` — —
- `test_build_summary_aggregates_correctly()` — —
- `test_resolve_profile_prefers_publish_when_auto()` — —
- `test_resolve_profile_defaults_to_python_when_pipeline_requested()` — —
- `test_compute_verdict_returns_ready_for_dry_run_success()` — —
- `test_compute_verdict_fails_when_dry_run_push_preflight_fails()` — —
- `test_process_project_skips_dirty_repo_when_requested()` — —
- `test_run_pyqual_batch_stops_on_fail_fast()` — —
- `test_run_pyqual_batch_smoke_with_mocked_project_flow()` — —
- `test_save_report_includes_project_notes_for_verdict_reasons_and_errors()` — —
- `test_pyqual_yaml_template_is_valid_yaml()` — —
- `test_pyqual_project_result_defaults()` — —
- `sample_file()` — —
- `test_config_init_validate_and_show()` — —
- `test_config_diff_history_apply_and_clone()` — —
- `test_config_rollback()` — —
- `test_refactor_dry_run_yaml_renders_plan_and_skips_cycle()` — —
- `test_refactor_live_json_emits_payload_and_passes_flags()` — —
- `test_example_list_shows_all_scenarios()` — —
- `test_example_memory_learning_default()` — —
- `test_example_basic_analysis_advanced()` — —
- `test_batch_pyqual_run_help()` — —
- `test_batch_pyqual_run_forwards_options()` — —
- `test_batch_autofix_help()` — —
- `test_secret_interceptor_redacts_and_resolves()` — —
- `test_store_save_load_validate_and_clone()` — —
- `test_applier_apply_and_rollback()` — —
- `test_store_history_can_be_serialized_as_json()` — —
- `test_project()` — —
- `git_project()` — —
- `runner()` — —
- `api_client()` — —
- `basic_analysis_result()` — —
- `custom_rules_result()` — —
- `full_pipeline_result()` — —
- `memory_learning_result()` — —
- `api_integration_result()` — —
- `awareness_result()` — —
- `pyqual_result()` — —
- `audit_result()` — —
- `pr_bot_result()` — —
- `badge_result()` — —
- `test_all_examples_exist()` — —
- `test_examples_have_readme()` — —
- `test_example_yaml_files_exist()` — —
- `test_advanced_examples_run()` — —
- `test_toon_candidate_priority_classifies_known_categories()` — —
- `test_analyze_trends_preserves_cc_alias()` — —
- `test_build_timeline_graceful_fallback_without_git()` — —
- `test_find_degradation_sources_returns_largest_jump_first()` — —
- `test_predict_future_state_returns_degrading_prediction()` — —
- `analyzer()` — —
- `dsl()` — —
- `goal_analysis()` — —
- `pfix_analysis()` — —
- `project_path()` — —
- `test_llm_execution()` — —
- `two_projects()` — —
- `redsl_analysis()` — —
- `redsl_enriched_analysis()` — —
- `test_toon_to_tasks_decisions()` — —
- `test_toon_to_tasks_layers_high_cc()` — —
- `test_refactor_plan_to_tasks()` — —
- `test_generate_planfile_dry_run()` — —
- `test_generate_planfile_writes_yaml()` — —
- `test_generate_planfile_merge_preserves_done()` — —
- `test_cli_planfile_sync_dry_run()` — —
- `test_cli_planfile_show()` — —
- `test_cli_planfile_sync_json_format()` — —
- `print()` — —
- `validate()` — —
- `store()` — —
- `lifecycle()` — —
- `retry_with_backoff()` — —
- `reconcile_invoice()` — —
- `process()` — —
- `helper()` — —
- `format()` — —
- `pad()` — —
- `verify()` — —
- `generate_token()` — —
- `load_env_pl()` — —
- `env_pl()` — —
- `parseSelection_pl()` — —
- `h_pl()` — —
- `load_env()` — —
- `OPENROUTER_API_KEY()` — —
- `generate_readme()` — —
- `check_http()` — —
- `check_content()` — —
- `check_php_syntax()` — —
- `check_env_exists()` — —
- `check_encryption_key()` — —
- `check_directories()` — —
- `check_admin_auth()` — —
- `check_cron_scripts()` — —
- `check_status()` — —
- `check_contains()` — —
- `check_not_contains()` — —
- `main_function()` — —
- `validate_data()` — —
- `save_data()` — —
- `log_error()` — —


## Project Structure

📄 `.goal.pre-commit-hook` (1 functions)
📄 `.goal.vallm-pre-commit`
📄 `.planfile.config`
📄 `.planfile.sprints.backlog`
📄 `.planfile.sprints.current`
📄 `.pre-commit-config`
📄 `.taskill.state`
📄 `CHANGELOG`
📄 `Dockerfile`
📄 `Makefile`
📄 `README` (3 functions)
📄 `README_EN` (3 functions)
📄 `SUMD` (997 functions, 11 classes)
📄 `SUMR` (57 functions, 11 classes)
📄 `TODO`
📄 `Taskfile`
📄 `app.models` (3 classes)
📄 `config.default_rules`
📄 `docker-compose`
📄 `docs.API`
📄 `docs.CONFIG_CHEATSHEET`
📄 `docs.CONFIG_MIGRATION`
📄 `docs.CONFIG_STANDARD`
📄 `docs.README` (1 functions)
📄 `docs.ats-benchmark`
📄 `docs.autonomous_pr_example`
📄 `docs.clickmd-markdown-terminal`
📄 `docs.code2docs-automatyczna-dokumentacja`
📄 `docs.code2llm-analiza-przeplywu-kodu`
📄 `docs.code2logic-analiza-nlp`
📄 `docs.cost-kalkulator-kosztow-ai`
📄 `docs.domd-walidacja-komend-markdown`
📄 `docs.goal-automatyczny-git-push`
📄 `docs.heal-zdrowie-wellness`
📄 `docs.llx-routing-modeli-llm`
📄 `docs.metrun-profilowanie-wydajnosci`
📄 `docs.model-policy` (4 functions)
📄 `docs.model-policy-quickstart` (6 functions)
📄 `docs.nfo-automatyczne-logowanie-funkcji` (1 functions)
📄 `docs.pactfix-bash-analyzer`
📄 `docs.pfix-self-healing-python`
📄 `docs.planfile-automatyzacja-sdlc`
📄 `docs.prefact-linter-llm-aware`
📄 `docs.prellm-preprocessing-llm`
📄 `docs.proxym-proxy-ai`
📄 `docs.pyqual-quality-gates`
📄 `docs.qualbench-ci-dla-kodu-ai`
📄 `docs.redup-detekcja-duplikacji`
📄 `docs.regix-indeks-regresji`
📄 `docs.toonic-format-toon`
📄 `docs.vallm-walidacja-kodu-llm`
📄 `docs.weekly-analizator-jakosci`
📄 `docs.zautomatyzowany-biznes-semcod`
📄 `examples.01-basic-analysis.README`
📄 `examples.01-basic-analysis.advanced`
📄 `examples.01-basic-analysis.default`
📄 `examples.01-basic-analysis.main` (1 functions)
📄 `examples.02-custom-rules.README`
📄 `examples.02-custom-rules.advanced`
📄 `examples.02-custom-rules.default`
📄 `examples.02-custom-rules.main` (1 functions)
📄 `examples.02-custom-rules.team_rules`
📄 `examples.03-full-pipeline.README`
📄 `examples.03-full-pipeline.advanced` (2 functions)
📄 `examples.03-full-pipeline.default` (1 functions)
📄 `examples.03-full-pipeline.main` (1 functions)
📄 `examples.04-memory-learning.README`
📄 `examples.04-memory-learning.advanced`
📄 `examples.04-memory-learning.default`
📄 `examples.04-memory-learning.main` (1 functions)
📄 `examples.05-api-integration.README`
📄 `examples.05-api-integration.advanced` (5 functions)
📄 `examples.05-api-integration.default` (4 functions)
📄 `examples.05-api-integration.main` (1 functions)
📄 `examples.06-awareness.README`
📄 `examples.06-awareness.advanced`
📄 `examples.06-awareness.default`
📄 `examples.06-awareness.main` (1 functions)
📄 `examples.07-pyqual.README`
📄 `examples.07-pyqual.advanced` (6 functions, 1 classes)
📄 `examples.07-pyqual.default` (3 functions, 1 classes)
📄 `examples.07-pyqual.main` (1 functions)
📄 `examples.08-audit.README`
📄 `examples.08-audit.advanced`
📄 `examples.08-audit.default`
📄 `examples.08-audit.main` (1 functions)
📄 `examples.09-pr-bot.README`
📄 `examples.09-pr-bot.advanced` (4 functions, 4 classes)
📄 `examples.09-pr-bot.default` (3 functions)
📄 `examples.09-pr-bot.main` (1 functions)
📄 `examples.10-badge.README`
📄 `examples.10-badge.advanced`
📄 `examples.10-badge.default`
📄 `examples.10-badge.main` (1 functions)
📄 `examples.11-model-policy.README` (2 functions)
📄 `examples.11-model-policy.main` (5 functions)
📄 `goal`
📄 `planfile`
📄 `prefact`
📄 `project`
📄 `project.README`
📄 `project.analysis.toon`
📄 `project.calls`
📄 `project.calls.toon`
📄 `project.context`
📄 `project.duplication.toon`
📄 `project.evolution.toon`
📄 `project.map.toon` (16004 functions)
📄 `project.project.toon`
📄 `project.prompt`
📄 `project.validation.toon`
📄 `project_test.README`
📄 `project_test.analysis.toon`
📄 `project_test.context`
📄 `project_test.evolution.toon`
📄 `project_test.map.toon` (797 functions)
📄 `project_test.project.toon`
📄 `project_test.prompt`
📄 `pyproject`
📄 `pyqual`
📄 `pyqual_report`
📦 `redsl`
📄 `redsl.__main__`
📦 `redsl.analyzers`
📄 `redsl.analyzers.analyzer` (8 functions, 1 classes)
📄 `redsl.analyzers.code2llm_bridge` (5 functions, 1 classes)
📄 `redsl.analyzers.incremental` (17 functions, 2 classes)
📄 `redsl.analyzers.metrics` (2 functions, 2 classes)
📦 `redsl.analyzers.parsers` (1 classes)
📄 `redsl.analyzers.parsers.duplication_parser` (5 functions, 1 classes)
📄 `redsl.analyzers.parsers.functions_parser` (6 functions, 1 classes)
📄 `redsl.analyzers.parsers.project_parser` (18 functions, 1 classes)
📄 `redsl.analyzers.parsers.validation_parser` (1 functions, 1 classes)
📄 `redsl.analyzers.python_analyzer` (8 functions, 1 classes)
📄 `redsl.analyzers.quality_visitor` (18 functions, 1 classes)
📄 `redsl.analyzers.radon_analyzer` (23 functions, 1 classes)
📄 `redsl.analyzers.redup_bridge` (7 functions, 1 classes)
📄 `redsl.analyzers.resolver` (4 functions, 1 classes)
📄 `redsl.analyzers.semantic_chunker` (11 functions, 2 classes)
📄 `redsl.analyzers.sumd_bridge` (13 functions, 2 classes)
📄 `redsl.analyzers.toon_analyzer` (13 functions, 1 classes)
📄 `redsl.analyzers.utils` (9 functions)
📦 `redsl.api` (2 functions)
📦 `redsl.api.cqrs`
📄 `redsl.api.cqrs.commands` (6 functions, 7 classes)
📄 `redsl.api.cqrs.events` (19 functions, 9 classes)
📄 `redsl.api.cqrs.projections` (17 functions, 4 classes)
📄 `redsl.api.cqrs.queries` (8 functions, 11 classes)
📄 `redsl.api.cqrs.websocket_manager` (11 functions, 1 classes)
📄 `redsl.api.cqrs_routes` (1 functions, 5 classes)
📄 `redsl.api.debug_routes` (1 functions)
📄 `redsl.api.example_routes` (4 functions)
📄 `redsl.api.health_routes` (1 functions)
📄 `redsl.api.models` (13 classes)
📄 `redsl.api.openapi`
📄 `redsl.api.pyqual_routes` (1 functions)
📄 `redsl.api.refactor_routes` (8 functions)
📄 `redsl.api.scan_routes` (6 functions, 2 classes)
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
📦 `redsl.bridges`
📄 `redsl.bridges.base` (2 functions, 1 classes)
📄 `redsl.bridges.redeploy_bridge` (10 functions)
📦 `redsl.ci`
📄 `redsl.ci.github_actions` (6 functions, 1 classes)
📦 `redsl.cli` (4 functions)
📄 `redsl.cli.__main__`
📄 `redsl.cli.batch` (6 functions)
📄 `redsl.cli.config` (13 functions)
📄 `redsl.cli.debug` (5 functions)
📄 `redsl.cli.deploy` (7 functions)
📄 `redsl.cli.events` (6 functions)
📄 `redsl.cli.examples` (14 functions)
📄 `redsl.cli.llm_banner` (5 functions)
📄 `redsl.cli.logging` (1 functions)
📄 `redsl.cli.model_policy` (6 functions)
📄 `redsl.cli.models` (14 functions)
📄 `redsl.cli.planfile` (30 functions)
📄 `redsl.cli.pyqual` (4 functions)
📄 `redsl.cli.refactor` (14 functions)
📄 `redsl.cli.scan` (2 functions)
📄 `redsl.cli.utils` (2 functions)
📄 `redsl.cli.workflow` (5 functions)
📄 `redsl.commands._fixer_utils` (1 functions)
📄 `redsl.commands._guard_fixers` (7 functions)
📄 `redsl.commands._indent_fixers` (9 functions)
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
📦 `redsl.commands.autonomy_pr` (11 functions)
📄 `redsl.commands.autonomy_pr.analyzer` (6 functions)
📄 `redsl.commands.autonomy_pr.git_ops` (7 functions)
📄 `redsl.commands.autonomy_pr.models` (6 classes)
📄 `redsl.commands.autonomy_pr.reporter` (3 functions)
📄 `redsl.commands.autonomy_pr.validator` (7 functions)
📄 `redsl.commands.batch` (7 functions)
📦 `redsl.commands.batch_pyqual`
📄 `redsl.commands.batch_pyqual.config_gen` (3 functions, 1 classes)
📄 `redsl.commands.batch_pyqual.discovery` (5 functions)
📄 `redsl.commands.batch_pyqual.models` (1 classes)
📄 `redsl.commands.batch_pyqual.pipeline` (14 functions, 1 classes)
📄 `redsl.commands.batch_pyqual.reporting` (25 functions)
📄 `redsl.commands.batch_pyqual.runner` (7 functions, 1 classes)
📄 `redsl.commands.batch_pyqual.utils` (3 functions)
📄 `redsl.commands.batch_pyqual.verdict` (7 functions)
📄 `redsl.commands.cli_autonomy` (20 functions)
📄 `redsl.commands.cli_awareness` (8 functions)
📄 `redsl.commands.cli_doctor` (8 functions)
📄 `redsl.commands.doctor` (3 functions)
📄 `redsl.commands.doctor_data` (1 functions, 2 classes)
📄 `redsl.commands.doctor_detectors` (17 functions)
📄 `redsl.commands.doctor_fixers` (9 functions)
📄 `redsl.commands.doctor_fstring_fixers` (10 functions)
📄 `redsl.commands.doctor_helpers` (2 functions)
📄 `redsl.commands.doctor_indent_fixers`
📄 `redsl.commands.github_source` (9 functions)
📄 `redsl.commands.hybrid` (14 functions)
📄 `redsl.commands.multi_project` (10 functions, 3 classes)
📄 `redsl.commands.plan_sync` (16 functions, 2 classes)
📄 `redsl.commands.planfile_bridge` (7 functions)
📦 `redsl.commands.pyqual` (13 functions, 1 classes)
📄 `redsl.commands.pyqual.ast_analyzer` (2 functions, 1 classes)
📄 `redsl.commands.pyqual.bandit_analyzer` (1 functions, 1 classes)
📄 `redsl.commands.pyqual.fix_decisions` (5 functions)
📄 `redsl.commands.pyqual.mypy_analyzer` (2 functions, 1 classes)
📄 `redsl.commands.pyqual.reporter` (5 functions, 1 classes)
📄 `redsl.commands.pyqual.ruff_analyzer` (1 functions, 1 classes)
📄 `redsl.commands.scan` (13 functions, 4 classes)
📦 `redsl.commands.sumr_planfile` (5 functions)
📄 `redsl.commands.sumr_planfile.core` (5 functions)
📄 `redsl.commands.sumr_planfile.extractors` (15 functions)
📄 `redsl.commands.sumr_planfile.models` (1 functions, 3 classes)
📄 `redsl.commands.sumr_planfile.parsers` (3 functions)
📄 `redsl.commands.sumr_planfile.utils` (4 functions)
📄 `redsl.config` (4 functions, 5 classes)
📦 `redsl.config_standard`
📄 `redsl.config_standard.agent_bridge` (8 functions, 1 classes)
📄 `redsl.config_standard.applier` (7 functions, 2 classes)
📄 `redsl.config_standard.catalog` (3 functions, 1 classes)
📄 `redsl.config_standard.core` (3 functions, 6 classes)
📄 `redsl.config_standard.llm_policy` (1 functions, 5 classes)
📄 `redsl.config_standard.models`
📄 `redsl.config_standard.nlp_handlers` (10 functions, 1 classes)
📄 `redsl.config_standard.paths` (9 functions)
📄 `redsl.config_standard.profiles` (3 functions)
📄 `redsl.config_standard.proposals` (4 functions, 5 classes)
📄 `redsl.config_standard.secrets` (2 functions, 2 classes)
📄 `redsl.config_standard.security` (6 functions, 2 classes)
📄 `redsl.config_standard.store` (22 functions, 5 classes)
📄 `redsl.consciousness_loop` (7 functions, 1 classes)
📦 `redsl.core`
📄 `redsl.core.pipeline` (4 functions, 4 classes)
📄 `redsl.defaults.workflow`
📦 `redsl.diagnostics`
📄 `redsl.diagnostics.perf_bridge` (11 functions, 3 classes)
📦 `redsl.dsl`
📄 `redsl.dsl.engine` (12 functions, 6 classes)
📄 `redsl.dsl.project.README`
📄 `redsl.dsl.project.analysis.toon`
📄 `redsl.dsl.project.context`
📄 `redsl.dsl.rule_generator` (11 functions, 2 classes)
📦 `redsl.examples`
📄 `redsl.examples._common` (6 functions)
📄 `redsl.examples.api_integration` (2 functions)
📄 `redsl.examples.audit` (10 functions)
📄 `redsl.examples.awareness` (6 functions)
📄 `redsl.examples.badge` (8 functions)
📄 `redsl.examples.basic_analysis` (2 functions)
📄 `redsl.examples.custom_rules` (3 functions)
📄 `redsl.examples.full_pipeline` (2 functions)
📄 `redsl.examples.memory_learning` (6 functions)
📄 `redsl.examples.pr_bot` (6 functions)
📄 `redsl.examples.pyqual_example` (2 functions)
📦 `redsl.execution`
📄 `redsl.execution.backup_manager` (7 functions)
📄 `redsl.execution.cycle` (14 functions)
📄 `redsl.execution.decision` (9 functions)
📄 `redsl.execution.deploy_detector` (10 functions, 2 classes)
📄 `redsl.execution.executor`
📄 `redsl.execution.planfile_runner` (3 functions)
📄 `redsl.execution.planfile_updater` (12 functions)
📄 `redsl.execution.project_scanner` (7 functions, 1 classes)
📄 `redsl.execution.pyqual_validators` (7 functions)
📄 `redsl.execution.reflector` (2 functions)
📄 `redsl.execution.reporter` (4 functions)
📄 `redsl.execution.resolution` (6 functions)
📄 `redsl.execution.sandbox_execution` (1 functions)
📄 `redsl.execution.validation` (2 functions)
📄 `redsl.execution.workflow` (11 functions, 12 classes)
📦 `redsl.formatters`
📄 `redsl.formatters.batch` (12 functions)
📄 `redsl.formatters.core` (1 functions)
📄 `redsl.formatters.cycle` (18 functions)
📄 `redsl.formatters.debug` (1 functions)
📄 `redsl.formatters.pyqual_report`
📄 `redsl.formatters.refactor` (9 functions)
📄 `redsl.history` (16 functions, 3 classes)
📦 `redsl.integrations`
📄 `redsl.integrations.webhook` (3 functions)
📦 `redsl.llm` (14 functions, 2 classes)
📄 `redsl.llm.gate` (7 functions, 2 classes)
📄 `redsl.llm.llx_router` (15 functions, 1 classes)
📦 `redsl.llm.registry`
📄 `redsl.llm.registry.aggregator` (16 functions, 1 classes)
📄 `redsl.llm.registry.models` (7 classes)
📦 `redsl.llm.registry.sources`
📄 `redsl.llm.registry.sources.base` (13 functions, 6 classes)
📦 `redsl.llm.selection`
📄 `redsl.llm.selection.checks` (9 functions)
📄 `redsl.llm.selection.config` (7 functions)
📄 `redsl.llm.selection.metrics` (2 functions)
📄 `redsl.llm.selection.models` (1 functions, 4 classes)
📄 `redsl.llm.selection.ops` (1 functions)
📄 `redsl.llm.selection.selector` (9 functions, 1 classes)
📄 `redsl.llm.selection.strategy` (3 functions, 1 classes)
📄 `redsl.main` (23 functions)
📦 `redsl.memory` (18 functions, 4 classes)
📄 `redsl.orchestrator` (5 functions, 2 classes)
📄 `redsl.project.README`
📄 `redsl.project.analysis.toon`
📄 `redsl.project.batch_1.analysis.toon`
📄 `redsl.project.batch_2.analysis.toon`
📄 `redsl.project.context`
📄 `redsl.project.evolution.toon`
📄 `redsl.project.examples.analysis.toon`
📄 `redsl.project.refactors_validation_examples.analysis.toon`
📄 `redsl.project.root.analysis.toon`
📄 `redsl.project.validation_examples.analysis.toon`
📄 `redsl.pyqual_report`
📦 `redsl.refactors`
📄 `redsl.refactors._base` (1 functions, 1 classes)
📄 `redsl.refactors.ast_transformers` (9 functions, 2 classes)
📄 `redsl.refactors.body_restorer` (7 functions)
📄 `redsl.refactors.diff_manager` (9 functions)
📄 `redsl.refactors.direct` (6 functions, 1 classes)
📄 `redsl.refactors.direct_constants` (6 functions, 1 classes)
📄 `redsl.refactors.direct_guard` (6 functions, 1 classes)
📄 `redsl.refactors.direct_imports` (14 functions, 1 classes)
📄 `redsl.refactors.direct_types` (5 functions, 1 classes)
📄 `redsl.refactors.engine` (9 functions, 1 classes)
📄 `redsl.refactors.models` (3 classes)
📄 `redsl.refactors.prompts` (3 functions)
📦 `redsl.utils`
📄 `redsl.utils.json_helpers` (1 functions)
📄 `redsl.utils.tool_check` (1 functions)
📦 `redsl.validation`
📄 `redsl.validation.pyqual_bridge` (13 functions)
📄 `redsl.validation.regix_bridge` (8 functions, 1 classes)
📄 `redsl.validation.sandbox` (9 functions, 3 classes)
📄 `redsl.validation.testql_bridge` (10 functions, 2 classes)
📄 `redsl.validation.vallm_bridge` (7 functions, 1 classes)
📄 `redsl_output.hybrid_refactor_results`
📄 `redsl_output.pyqual_report`
📄 `redsl_output.redsl_batch_hybrid_report`
📄 `redsl_refactor_report`
📄 `redsl_refactor_report.toon`
📄 `redsl_scan_report`
📄 `requirements`
📄 `sumd`
📄 `test_refactor_bad.complex_code` (17 functions, 1 classes)
📄 `test_refactor_bad.redsl_refactor_report`
📄 `test_refactor_project.bad_code` (2 functions, 1 classes)
📄 `test_refactor_project.redsl_refactor_plan`
📄 `test_refactor_project.redsl_refactor_report`
📄 `tree`
📄 `vallm`
📄 `vallm_analysis.validation.toon`
📄 `vallm_analysis_full.validation.toon`
📄 `vallm_json.validation`
📄 `vallm_text.validation`
📄 `www.DEPLOY_CHECKLIST`
📄 `www.Dockerfile`
📄 `www.Makefile`
📄 `www.README`
📄 `www.README-PLESK`
📄 `www.README_CONFIG`
📄 `www.README_NDA`
📄 `www.README_PROPozycje`
📄 `www.SUMD`
📄 `www.SUMR`
📄 `www.admin.auth` (2 functions)
📄 `www.admin.clients`
📄 `www.admin.contracts`
📄 `www.admin.index`
📄 `www.admin.invoices`
📄 `www.admin.logs` (3 functions)
📄 `www.admin.projects`
📄 `www.admin.scans`
📄 `www.admin.tickets`
📄 `www.api.redsl` (4 functions)
📄 `www.app` (15 functions)
📄 `www.blog.index`
📄 `www.bootstrap` (5 functions)
📄 `www.client.index` (1 functions)
📄 `www.composer`
📄 `www.config-api` (15 functions)
📄 `www.config-editor` (5 functions)
📄 `www.cron.invoice-generator`
📄 `www.cron.scan-worker`
📄 `www.debug`
📄 `www.docker-compose`
📄 `www.docs.README`
📄 `www.docs.landing-page-copy`
📄 `www.email-notifications` (4 functions)
📄 `www.i18n.de`
📄 `www.i18n.en`
📄 `www.i18n.pl`
📄 `www.index` (2 functions)
📄 `www.install-plesk`
📄 `www.klient.index`
📄 `www.marketing.index` (11 functions)
📄 `www.mock-github.access_token`
📄 `www.mock-github.authorize`
📄 `www.mock-github.user`
📄 `www.nda-form` (11 functions)
📄 `www.nda-wzor`
📄 `www.phpunit`
📄 `www.polityka-prywatnosci` (1 functions)
📄 `www.project`
📄 `www.project.README`
📄 `www.project.analysis.toon`
📄 `www.project.calls`
📄 `www.project.calls.toon`
📄 `www.project.context`
📄 `www.project.evolution.toon`
📄 `www.project.map.toon`
📄 `www.project.project.toon`
📄 `www.project.prompt`
📄 `www.proposals` (2 functions)
📄 `www.propozycje`
📄 `www.regulamin` (1 functions)
📄 `www.smoke-test` (8 functions)
📄 `www.test-plesk` (3 functions)
📄 `www.testql-scenarios.generated-api-smoke.testql.toon`

## Requirements

- Python >= >=3.11
- fastapi >=0.115.0- uvicorn >=0.44.0- pydantic >=2.10.0- litellm >=1.52.0- chromadb >=0.6.0- pyyaml >=6.0.2- rich >=13.9.0- httpx >=0.28.0- click >=8.1.7- python-dotenv >=1.0.1- goal >=2.1.218- costs >=0.1.20- pfix >=0.1.60

## Contributing

**Contributors:**
- Tom Softreck <tom@sapletta.com>
- Tom Sapletta <tom-sapletta-com@users.noreply.github.com>

We welcome contributions! Open an issue or pull request to get started.
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

- 💡 [Examples](./examples) — Usage examples and code samples

### Generated Files

| Output | Description | Link |
|--------|-------------|------|
| `README.md` | Project overview (this file) | — |
| `examples` | Usage examples and code samples | [View](./examples) |

<!-- code2docs:end -->