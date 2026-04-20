# System Architecture Analysis

## Overview

- **Project**: /home/tom/github/semcod/redsl/redsl
- **Primary Language**: python
- **Languages**: python: 287
- **Analysis Mode**: static
- **Total Functions**: 1470
- **Total Classes**: 216
- **Modules**: 287
- **Entry Points**: 0

## Architecture by Module

### cli.planfile
- **Functions**: 30
- **File**: `planfile.py`

### commands.batch_pyqual.reporting
- **Functions**: 25
- **File**: `reporting.py`

### awareness.git_timeline
- **Functions**: 23
- **Classes**: 1
- **File**: `git_timeline.py`

### root.main
- **Functions**: 23
- **File**: `main.py`

### analyzers.radon_analyzer
- **Functions**: 23
- **Classes**: 1
- **File**: `radon_analyzer.py`

### batch_1.main
- **Functions**: 23
- **File**: `main.py`

### batch_2.main
- **Functions**: 23
- **File**: `main.py`

### config_standard.store
- **Functions**: 22
- **Classes**: 5
- **File**: `store.py`

### commands.cli_autonomy
- **Functions**: 20
- **File**: `cli_autonomy.py`

### formatters.cycle
- **Functions**: 18
- **File**: `cycle.py`

### root.memory
- **Functions**: 18
- **Classes**: 4
- **File**: `__init__.py`

### analyzers.parsers.project_parser
- **Functions**: 18
- **Classes**: 1
- **File**: `project_parser.py`

### analyzers.quality_visitor
- **Functions**: 18
- **Classes**: 1
- **File**: `quality_visitor.py`

### batch_1.memory
- **Functions**: 18
- **Classes**: 4
- **File**: `__init__.py`

### batch_2.memory
- **Functions**: 18
- **Classes**: 4
- **File**: `__init__.py`

### commands.doctor_detectors
- **Functions**: 17
- **File**: `doctor_detectors.py`

### analyzers.incremental
- **Functions**: 17
- **Classes**: 2
- **File**: `incremental.py`

### commands.plan_sync
- **Functions**: 16
- **Classes**: 2
- **File**: `plan_sync.py`

### root.history
- **Functions**: 16
- **Classes**: 3
- **File**: `history.py`

### autonomy.scheduler
- **Functions**: 16
- **Classes**: 2
- **File**: `scheduler.py`

## Key Entry Points

Main execution flows into the system:

## Process Flows

Key execution flows identified:

## Key Classes

### awareness.git_timeline.GitTimelineAnalyzer
> Build a historical metric timeline from git commits — facade.

This is a thin facade that delegates 
- **Methods**: 23
- **Key Methods**: awareness.git_timeline.GitTimelineAnalyzer.__init__, awareness.git_timeline.GitTimelineAnalyzer.build_timeline, awareness.git_timeline.GitTimelineAnalyzer.analyze_trends, awareness.git_timeline.GitTimelineAnalyzer.predict_future_state, awareness.git_timeline.GitTimelineAnalyzer.find_degradation_sources, awareness.git_timeline.GitTimelineAnalyzer.summarize, awareness.git_timeline.GitTimelineAnalyzer._resolve_repo_root, awareness.git_timeline.GitTimelineAnalyzer._project_rel_path, awareness.git_timeline.GitTimelineAnalyzer._git_log, awareness.git_timeline.GitTimelineAnalyzer._snapshot_for_commit

### config_standard.store.ConfigStore
> Manage a redsl-config directory with manifest, profiles and history.
- **Methods**: 22
- **Key Methods**: config_standard.store.ConfigStore.__init__, config_standard.store.ConfigStore.resolve, config_standard.store.ConfigStore.ensure_layout, config_standard.store.ConfigStore.create_default, config_standard.store.ConfigStore.apply_profile, config_standard.store.ConfigStore.load_document, config_standard.store.ConfigStore.load, config_standard.store.ConfigStore.load_any, config_standard.store.ConfigStore.save, config_standard.store.ConfigStore.write_schema_files

### analyzers.parsers.project_parser.ProjectParser
> Parser sekcji project_toon.
- **Methods**: 18
- **Key Methods**: analyzers.parsers.project_parser.ProjectParser.parse_project_toon, analyzers.parsers.project_parser.ProjectParser._parse_header_lines, analyzers.parsers.project_parser.ProjectParser._detect_section_change, analyzers.parsers.project_parser.ProjectParser._parse_section_line, analyzers.parsers.project_parser.ProjectParser._parse_health_line, analyzers.parsers.project_parser.ProjectParser._parse_alerts_line, analyzers.parsers.project_parser.ProjectParser._parse_hotspots_line, analyzers.parsers.project_parser.ProjectParser._parse_modules_line, analyzers.parsers.project_parser.ProjectParser._parse_layers_section_line, analyzers.parsers.project_parser.ProjectParser._parse_refactors_line

### analyzers.quality_visitor.CodeQualityVisitor
> Detects common code quality issues in Python AST.
- **Methods**: 18
- **Key Methods**: analyzers.quality_visitor.CodeQualityVisitor.__init__, analyzers.quality_visitor.CodeQualityVisitor.visit_Import, analyzers.quality_visitor.CodeQualityVisitor.visit_ImportFrom, analyzers.quality_visitor.CodeQualityVisitor.visit_Name, analyzers.quality_visitor.CodeQualityVisitor.visit_Assign, analyzers.quality_visitor.CodeQualityVisitor.visit_Attribute, analyzers.quality_visitor.CodeQualityVisitor._get_root_name, analyzers.quality_visitor.CodeQualityVisitor.visit_Constant, analyzers.quality_visitor.CodeQualityVisitor._count_untyped_params, analyzers.quality_visitor.CodeQualityVisitor.visit_FunctionDef
- **Inherits**: ast.NodeVisitor

### autonomy.scheduler.Scheduler
> Periodic quality-improvement loop.
- **Methods**: 16
- **Key Methods**: autonomy.scheduler.Scheduler.__init__, autonomy.scheduler.Scheduler.run, autonomy.scheduler.Scheduler.stop, autonomy.scheduler.Scheduler.run_once, autonomy.scheduler.Scheduler._has_changes_since_last_check, autonomy.scheduler.Scheduler._git_head, autonomy.scheduler.Scheduler._analyze, autonomy.scheduler.Scheduler._check_trends, autonomy.scheduler.Scheduler._check_proactive, autonomy.scheduler.Scheduler._generate_proposals

### llm.registry.aggregator.RegistryAggregator
> Aggregates model info from multiple sources with caching.
- **Methods**: 15
- **Key Methods**: llm.registry.aggregator.RegistryAggregator.__init__, llm.registry.aggregator.RegistryAggregator.get_all, llm.registry.aggregator.RegistryAggregator.get, llm.registry.aggregator.RegistryAggregator._fetch_and_merge, llm.registry.aggregator.RegistryAggregator._merge_model, llm.registry.aggregator.RegistryAggregator._collect_source_info, llm.registry.aggregator.RegistryAggregator._merge_context_length, llm.registry.aggregator.RegistryAggregator._merge_pricing, llm.registry.aggregator.RegistryAggregator._merge_capabilities, llm.registry.aggregator.RegistryAggregator._merge_quality

### refactors.direct_imports.DirectImportRefactorer
> Handles import-related direct refactoring.
- **Methods**: 14
- **Key Methods**: refactors.direct_imports.DirectImportRefactorer.__init__, refactors.direct_imports.DirectImportRefactorer.remove_unused_imports, refactors.direct_imports.DirectImportRefactorer._collect_unused_import_edits, refactors.direct_imports.DirectImportRefactorer._collect_import_edits, refactors.direct_imports.DirectImportRefactorer._collect_import_from_edits, refactors.direct_imports.DirectImportRefactorer._is_star_import, refactors.direct_imports.DirectImportRefactorer._build_import_from_replacement, refactors.direct_imports.DirectImportRefactorer._alias_name, refactors.direct_imports.DirectImportRefactorer._format_alias, refactors.direct_imports.DirectImportRefactorer._remove_statement_lines
- **Inherits**: DirectRefactorBase

### awareness.AwarenessManager
> Facade that combines all awareness layers into one snapshot.
- **Methods**: 13
- **Key Methods**: awareness.AwarenessManager.__init__, awareness.AwarenessManager._memory_fingerprint, awareness.AwarenessManager._git_head, awareness.AwarenessManager._build_cache_key, awareness.AwarenessManager.build_snapshot, awareness.AwarenessManager.build_context, awareness.AwarenessManager.build_prompt_context, awareness.AwarenessManager.history, awareness.AwarenessManager.ecosystem, awareness.AwarenessManager.health

### analyzers.toon_analyzer.ToonAnalyzer
> Analizator plików toon — przetwarza dane z code2llm.
- **Methods**: 13
- **Key Methods**: analyzers.toon_analyzer.ToonAnalyzer.__init__, analyzers.toon_analyzer.ToonAnalyzer.analyze_project, analyzers.toon_analyzer.ToonAnalyzer.analyze_from_toon_content, analyzers.toon_analyzer.ToonAnalyzer._find_toon_files, analyzers.toon_analyzer.ToonAnalyzer._select_project_key, analyzers.toon_analyzer.ToonAnalyzer._process_project_ton, analyzers.toon_analyzer.ToonAnalyzer._convert_modules_to_metrics, analyzers.toon_analyzer.ToonAnalyzer._process_hotspots, analyzers.toon_analyzer.ToonAnalyzer._process_alerts, analyzers.toon_analyzer.ToonAnalyzer._process_duplicates

### analyzers.sumd_bridge.SumdAnalyzer
> Native project analyzer using sumd extractor patterns.

Pure-Python implementation that doesn't requ
- **Methods**: 11
- **Key Methods**: analyzers.sumd_bridge.SumdAnalyzer.__init__, analyzers.sumd_bridge.SumdAnalyzer.analyze, analyzers.sumd_bridge.SumdAnalyzer.generate_map_toon, analyzers.sumd_bridge.SumdAnalyzer._collect_modules, analyzers.sumd_bridge.SumdAnalyzer._detect_language, analyzers.sumd_bridge.SumdAnalyzer._analyze_py_file, analyzers.sumd_bridge.SumdAnalyzer._extract_function_info, analyzers.sumd_bridge.SumdAnalyzer._extract_class_info, analyzers.sumd_bridge.SumdAnalyzer._calculate_cc, analyzers.sumd_bridge.SumdAnalyzer._identify_hotspots

### history.HistoryReader
> Read-only access to .redsl/history.jsonl for querying and dedup.
- **Methods**: 10
- **Key Methods**: history.HistoryReader.__init__, history.HistoryReader.load_events, history.HistoryReader.filter_by_file, history.HistoryReader.filter_by_type, history.HistoryReader.has_recent_proposal, history.HistoryReader.has_recent_ticket, history.HistoryReader._format_event_header, history.HistoryReader._format_event_details, history.HistoryReader._maybe_add_cycle_header, history.HistoryReader.generate_decision_report

### llm.LLMLayer
> Warstwa abstrakcji nad LLM z obsługą:
- wywołań tekstowych
- odpowiedzi JSON
- zliczania tokenów
- f
- **Methods**: 10
- **Key Methods**: llm.LLMLayer.__init__, llm.LLMLayer.set_chat_log, llm.LLMLayer._record_chat, llm.LLMLayer._load_provider_key, llm.LLMLayer._resolve_provider_key, llm.LLMLayer._build_completion_kwargs, llm.LLMLayer.call, llm.LLMLayer.call_json, llm.LLMLayer.reflect, llm.LLMLayer.total_calls

### awareness.timeline_toon.ToonCollector
> Collects and processes toon files from git history.
- **Methods**: 10
- **Key Methods**: awareness.timeline_toon.ToonCollector.__init__, awareness.timeline_toon.ToonCollector.snapshot_for_commit, awareness.timeline_toon.ToonCollector._collect_toon_contents, awareness.timeline_toon.ToonCollector._empty_toon_contents, awareness.timeline_toon.ToonCollector._store_toon_content, awareness.timeline_toon.ToonCollector._toon_bucket, awareness.timeline_toon.ToonCollector._sorted_toon_candidates, awareness.timeline_toon.ToonCollector._toon_candidate_priority, awareness.timeline_toon.ToonCollector._is_duplication_file, awareness.timeline_toon.ToonCollector._is_validation_file

### analyzers.semantic_chunker.SemanticChunker
> Buduje semantyczne chunki kodu dla LLM.
- **Methods**: 10
- **Key Methods**: analyzers.semantic_chunker.SemanticChunker._locate_function_data, analyzers.semantic_chunker.SemanticChunker._gather_chunk_contexts, analyzers.semantic_chunker.SemanticChunker.chunk_function, analyzers.semantic_chunker.SemanticChunker._parse_source, analyzers.semantic_chunker.SemanticChunker._build_chunk, analyzers.semantic_chunker.SemanticChunker.chunk_file, analyzers.semantic_chunker.SemanticChunker._find_nodes, analyzers.semantic_chunker.SemanticChunker._extract_relevant_imports, analyzers.semantic_chunker.SemanticChunker._extract_class_context, analyzers.semantic_chunker.SemanticChunker._extract_neighbors

### commands.multi_project.MultiProjectReport
> Zbiorczy raport z analizy wielu projektów.
- **Methods**: 9
- **Key Methods**: commands.multi_project.MultiProjectReport.total_projects, commands.multi_project.MultiProjectReport.successful, commands.multi_project.MultiProjectReport.failed, commands.multi_project.MultiProjectReport.aggregate_avg_cc, commands.multi_project.MultiProjectReport.aggregate_critical, commands.multi_project.MultiProjectReport.aggregate_files, commands.multi_project.MultiProjectReport.worst_projects, commands.multi_project.MultiProjectReport.summary, commands.multi_project.MultiProjectReport.to_dict

### llm.selection.selector.ModelSelector
> Wybiera najtańszy model spełniający wymagania.
- **Methods**: 9
- **Key Methods**: llm.selection.selector.ModelSelector.__init__, llm.selection.selector.ModelSelector.candidates, llm.selection.selector.ModelSelector._apply_known_good_override, llm.selection.selector.ModelSelector._check_gate, llm.selection.selector.ModelSelector.pick, llm.selection.selector.ModelSelector._get_passing_candidates, llm.selection.selector.ModelSelector._filter_by_tier, llm.selection.selector.ModelSelector._get_passing_candidates_for_tier, llm.selection.selector.ModelSelector._next_tier

### refactors.engine.RefactorEngine
> Silnik refaktoryzacji z pętlą refleksji.

1. Generuj propozycję (LLM)
2. Reflektuj (self-critique)
3
- **Methods**: 9
- **Key Methods**: refactors.engine.RefactorEngine.__init__, refactors.engine.RefactorEngine.estimate_confidence, refactors.engine.RefactorEngine._parse_confidence, refactors.engine.RefactorEngine._resolve_confidence, refactors.engine.RefactorEngine.generate_proposal, refactors.engine.RefactorEngine.reflect_on_proposal, refactors.engine.RefactorEngine.validate_proposal, refactors.engine.RefactorEngine.apply_proposal, refactors.engine.RefactorEngine._save_proposal

### awareness.ecosystem.EcosystemGraph
> Basic ecosystem graph for semcod-style project collections.
- **Methods**: 9
- **Key Methods**: awareness.ecosystem.EcosystemGraph.build, awareness.ecosystem.EcosystemGraph.summarize, awareness.ecosystem.EcosystemGraph.project, awareness.ecosystem.EcosystemGraph.impacted_projects, awareness.ecosystem.EcosystemGraph._build_node, awareness.ecosystem.EcosystemGraph._link_dependencies, awareness.ecosystem.EcosystemGraph._read_dependencies, awareness.ecosystem.EcosystemGraph._extract_dependency_tokens, awareness.ecosystem.EcosystemGraph._is_project_dir

### autonomy.growth_control.GrowthController
> Enforce growth budgets on a project.
- **Methods**: 8
- **Key Methods**: autonomy.growth_control.GrowthController.__init__, autonomy.growth_control.GrowthController.check_growth, autonomy.growth_control.GrowthController.suggest_consolidation, autonomy.growth_control.GrowthController._measure_weekly_growth, autonomy.growth_control.GrowthController._find_untested_new_modules, autonomy.growth_control.GrowthController._find_oversized_files, autonomy.growth_control.GrowthController._find_tiny_modules, autonomy.growth_control.GrowthController._group_by_prefix

### memory.AgentMemory
> Kompletny system pamięci z trzema warstwami.

- episodic: „co zrobiłem" — historia refaktoryzacji
- 
- **Methods**: 8
- **Key Methods**: memory.AgentMemory.__init__, memory.AgentMemory.remember_action, memory.AgentMemory.recall_similar_actions, memory.AgentMemory.learn_pattern, memory.AgentMemory.recall_patterns, memory.AgentMemory.store_strategy, memory.AgentMemory.recall_strategies, memory.AgentMemory.stats

## Data Transformation Functions

Key functions that process and transform data:

### commands.doctor_fstring_fixers._write_if_parses
- **Output to**: path.write_text, ast.parse

### commands._guard_fixers._process_guard_and_indent
> Process lines to remove guard blocks and fix excess indentation.
- **Output to**: len, None.rstrip, _GUARD_RE.match, new_lines.append, commands._guard_fixers._handle_guard

### commands.github_source._parse_next_link
> Parse GitHub Link header to find next page URL.
- **Output to**: link_header.split, part.strip, None.strip, url_part.startswith, url_part.endswith

### commands.cli_doctor._format_check_report
> Format doctor check report as text.
- **Output to**: None.join, lines.append, lines.append, lines.append

### commands.cli_doctor._format_heal_report
> Format doctor heal report as text.
- **Output to**: lines.append, None.join, lines.append, lines.append, lines.append

### commands.cli_doctor._format_batch_report
> Format doctor batch report as text.
- **Output to**: lines.append, None.join, len, len, len

### commands._indent_fixers._process_def_block
> Handle a def/class/try block: fix body indent or strip excess indent.
- **Output to**: new_lines.append, commands._indent_fixers._scan_next_nonblank, len, len, len

### commands.cli_autonomy._format_gate_details
> Format quality gate details as text.
- **Output to**: None.join, lines.append, lines.append, lines.append, verdict.metrics_before.get

### commands.cli_autonomy._format_gate_fix_result
> Format gate fix result as text.
- **Output to**: lines.append, lines.append, None.join, lines.append, len

### commands.cli_autonomy._format_improve_result
> Format improve cycle result as text.
- **Output to**: result.get, result.get, None.join, lines.append, lines.append

### commands.cli_autonomy._format_autonomy_status
> Format autonomy metrics as human-readable text.
- **Output to**: None.join, lines.append, lines.append

### commands.cli_autonomy._format_growth_report
> Format growth check result as text.
- **Output to**: None.join, lines.append, lines.append, lines.append, lines.append

### commands.batch_pyqual.reporting._format_summary_verdicts
> Format verdict and project count lines.
- **Output to**: None.join

### commands.batch_pyqual.reporting._format_summary_config_and_gates
> Format config, gates, and fix lines.
- **Output to**: lines.append, lines.append, lines.append, None.join, lines.append

### commands.batch_pyqual.reporting._format_summary_pipeline_and_totals
> Format pipeline, git, and size lines.
- **Output to**: lines.append, lines.append, None.join, lines.append, lines.append

### commands.batch_pyqual.reporting._format_project_row
> Format a single project row for the details table.

### commands.batch._process_batch_project
> Process a single project in the batch.
- **Output to**: print, print, print, commands.batch.measure_todo_reduction, print

### commands.hybrid._process_single_project
> Process a single project and return results.
- **Output to**: commands.hybrid._count_todo_issues, commands.hybrid.run_hybrid_quality_refactor, commands.hybrid._regenerate_todo, commands.hybrid._count_todo_issues, print

### commands.autofix.runner._format_project_status
> Format brief status line for a project result.
- **Output to**: None.join, status_parts.append, status_parts.append, status_parts.append, status_parts.append

### commands.sumr_planfile.parsers.parse_sumr
> Parse a SUMR.md file and extract refactoring-relevant data.
- **Output to**: path.read_text, _METADATA_NAME_RE.search, _METADATA_VERSION_RE.search, _REFACTOR_SECTION_RE.search, sorted

### commands.sumr_planfile.parsers.parse_refactor_plan_yaml
> Parse refactor_plan.yaml content into raw task dicts.

The format is a multi-document YAML (``---`` 
- **Output to**: list, yaml.safe_load_all, doc.get, doc.get, isinstance

### commands.batch_pyqual.runner._format_project_status
> Format project result status into readable parts.
- **Output to**: parts.extend, parts.extend, parts.extend, parts.append, None.join

### commands.autofix.pipeline._process_project
> Full autofix pipeline for a single project.
- **Output to**: ProjectFixResult, commands.autofix.pipeline._stage_collect_metrics, commands.autofix.pipeline._stage_ensure_todo, commands.autofix.pipeline._stage_apply_fixes, commands.autofix.pipeline._stage_quality_gate_check

### commands.pyqual._format_pyqual_issues
> Format pyqual issues section.
- **Output to**: summary.get, summary.get, summary.get, summary.get, summary.get

### commands.pyqual._format_pyqual_metrics
> Format pyqual metrics section.
- **Output to**: metrics.get, metrics.get, metrics.get

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `cli.planfile.planfile_validate` - 66 calls
- `cli.models.estimate_cost` - 44 calls
- `cli.workflow.workflow_show` - 44 calls
- `cli.events.events_cycles` - 42 calls
- `examples.pyqual_example.run_pyqual_example` - 41 calls
- `examples.pr_bot.run_pr_bot_example` - 40 calls
- `cli.events.events_summary` - 35 calls
- `execution.planfile_updater.add_decision_tasks` - 35 calls
- `examples.custom_rules.run_custom_rules_example` - 34 calls
- `execution.cycle.run_cycle` - 34 calls
- `examples.badge.run_badge_example` - 33 calls
- `analyzers.sumd_bridge.SumdAnalyzer.generate_map_toon` - 32 calls
- `examples.basic_analysis.run_basic_analysis_example` - 31 calls
- `cli.config.config_apply` - 30 calls
- `cli.events.events_show` - 30 calls
- `cli.refactor.refactor` - 29 calls
- `llm.registry.sources.base.OpenRouterSource.fetch` - 29 calls
- `cli.workflow.workflow_scan` - 29 calls
- `cli.planfile.source_add` - 28 calls
- `refactors.engine.RefactorEngine.generate_proposal` - 28 calls
- `examples.full_pipeline.run_full_pipeline_example` - 27 calls
- `examples.api_integration.run_api_integration_example` - 26 calls
- `config_standard.applier.ConfigApplier.apply` - 26 calls
- `commands.pyqual.run_pyqual_fix` - 24 calls
- `cli.config.config_diff` - 24 calls
- `cli.llm_banner.print_llm_banner` - 23 calls
- `cli.config.config_init` - 23 calls
- `cli.config.config_history` - 23 calls
- `commands.sumr_planfile.core.generate_planfile` - 21 calls
- `cli.config.config_clone` - 21 calls
- `commands.sumr_planfile.parsers.parse_sumr` - 20 calls
- `cli.model_policy.check_model` - 20 calls
- `cli.config.config_rollback` - 20 calls
- `awareness.health_model.HealthModel.assess` - 20 calls
- `awareness.AwarenessManager.build_snapshot` - 20 calls
- `validation.vallm_bridge.validate_proposal` - 20 calls
- `commands.github_source.resolve_auth_ref` - 19 calls
- `config_standard.store.ConfigStore.clone_from` - 19 calls
- `autonomy.metrics.collect_autonomy_metrics` - 19 calls
- `formatters.batch.format_batch_results` - 19 calls

## System Interactions

How components interact:

```mermaid
graph TD
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.