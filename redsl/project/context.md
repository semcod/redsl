# System Architecture Analysis

## Overview

- **Project**: /home/tom/github/semcod/redsl/redsl
- **Primary Language**: python
- **Languages**: python: 205
- **Analysis Mode**: static
- **Total Functions**: 983
- **Total Classes**: 122
- **Modules**: 205
- **Entry Points**: 0

## Architecture by Module

### awareness.git_timeline
- **Functions**: 23
- **Classes**: 1
- **File**: `git_timeline.py`

### root.main
- **Functions**: 22
- **File**: `main.py`

### batch_1.main
- **Functions**: 22
- **File**: `main.py`

### refactors_validation_examples.main
- **Functions**: 22
- **File**: `main.py`

### commands.batch_pyqual.reporting
- **Functions**: 20
- **File**: `reporting.py`

### analyzers.radon_analyzer
- **Functions**: 20
- **File**: `radon_analyzer.py`

### root.memory
- **Functions**: 18
- **Classes**: 4
- **File**: `__init__.py`

### analyzers.quality_visitor
- **Functions**: 18
- **Classes**: 1
- **File**: `quality_visitor.py`

### analyzers.parsers.project_parser
- **Functions**: 18
- **Classes**: 1
- **File**: `project_parser.py`

### batch_1.memory
- **Functions**: 18
- **Classes**: 4
- **File**: `__init__.py`

### refactors_validation_examples.memory
- **Functions**: 18
- **Classes**: 4
- **File**: `__init__.py`

### commands.cli_autonomy
- **Functions**: 17
- **File**: `cli_autonomy.py`

### analyzers.incremental
- **Functions**: 17
- **Classes**: 2
- **File**: `incremental.py`

### commands.doctor_detectors
- **Functions**: 16
- **File**: `doctor_detectors.py`

### autonomy.scheduler
- **Functions**: 16
- **Classes**: 2
- **File**: `scheduler.py`

### root.awareness
- **Functions**: 16
- **Classes**: 2
- **File**: `__init__.py`

### root.api
- **Functions**: 16
- **Classes**: 12
- **File**: `api.py`

### batch_1.awareness
- **Functions**: 16
- **Classes**: 2
- **File**: `__init__.py`

### batch_1.api
- **Functions**: 16
- **Classes**: 12
- **File**: `api.py`

### refactors_validation_examples.api
- **Functions**: 16
- **Classes**: 12
- **File**: `api.py`

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

### analyzers.quality_visitor.CodeQualityVisitor
> Detects common code quality issues in Python AST.
- **Methods**: 18
- **Key Methods**: analyzers.quality_visitor.CodeQualityVisitor.__init__, analyzers.quality_visitor.CodeQualityVisitor.visit_Import, analyzers.quality_visitor.CodeQualityVisitor.visit_ImportFrom, analyzers.quality_visitor.CodeQualityVisitor.visit_Name, analyzers.quality_visitor.CodeQualityVisitor.visit_Assign, analyzers.quality_visitor.CodeQualityVisitor.visit_Attribute, analyzers.quality_visitor.CodeQualityVisitor._get_root_name, analyzers.quality_visitor.CodeQualityVisitor.visit_Constant, analyzers.quality_visitor.CodeQualityVisitor._count_untyped_params, analyzers.quality_visitor.CodeQualityVisitor.visit_FunctionDef
- **Inherits**: ast.NodeVisitor

### analyzers.parsers.project_parser.ProjectParser
> Parser sekcji project_toon.
- **Methods**: 18
- **Key Methods**: analyzers.parsers.project_parser.ProjectParser.parse_project_toon, analyzers.parsers.project_parser.ProjectParser._parse_header_lines, analyzers.parsers.project_parser.ProjectParser._detect_section_change, analyzers.parsers.project_parser.ProjectParser._parse_section_line, analyzers.parsers.project_parser.ProjectParser._parse_health_line, analyzers.parsers.project_parser.ProjectParser._parse_alerts_line, analyzers.parsers.project_parser.ProjectParser._parse_hotspots_line, analyzers.parsers.project_parser.ProjectParser._parse_modules_line, analyzers.parsers.project_parser.ProjectParser._parse_layers_section_line, analyzers.parsers.project_parser.ProjectParser._parse_refactors_line

### autonomy.scheduler.Scheduler
> Periodic quality-improvement loop.
- **Methods**: 16
- **Key Methods**: autonomy.scheduler.Scheduler.__init__, autonomy.scheduler.Scheduler.run, autonomy.scheduler.Scheduler.stop, autonomy.scheduler.Scheduler.run_once, autonomy.scheduler.Scheduler._has_changes_since_last_check, autonomy.scheduler.Scheduler._git_head, autonomy.scheduler.Scheduler._analyze, autonomy.scheduler.Scheduler._check_trends, autonomy.scheduler.Scheduler._check_proactive, autonomy.scheduler.Scheduler._generate_proposals

### refactors.direct_imports.DirectImportRefactorer
> Handles import-related direct refactoring.
- **Methods**: 15
- **Key Methods**: refactors.direct_imports.DirectImportRefactorer.__init__, refactors.direct_imports.DirectImportRefactorer.remove_unused_imports, refactors.direct_imports.DirectImportRefactorer._collect_unused_import_edits, refactors.direct_imports.DirectImportRefactorer._collect_import_edits, refactors.direct_imports.DirectImportRefactorer._collect_import_from_edits, refactors.direct_imports.DirectImportRefactorer._is_star_import, refactors.direct_imports.DirectImportRefactorer._build_import_from_replacement, refactors.direct_imports.DirectImportRefactorer._alias_name, refactors.direct_imports.DirectImportRefactorer._format_alias, refactors.direct_imports.DirectImportRefactorer._remove_statement_lines

### awareness.AwarenessManager
> Facade that combines all awareness layers into one snapshot.
- **Methods**: 13
- **Key Methods**: awareness.AwarenessManager.__init__, awareness.AwarenessManager._memory_fingerprint, awareness.AwarenessManager._git_head, awareness.AwarenessManager._build_cache_key, awareness.AwarenessManager.build_snapshot, awareness.AwarenessManager.build_context, awareness.AwarenessManager.build_prompt_context, awareness.AwarenessManager.history, awareness.AwarenessManager.ecosystem, awareness.AwarenessManager.health

### analyzers.toon_analyzer.ToonAnalyzer
> Analizator plików toon — przetwarza dane z code2llm.
- **Methods**: 13
- **Key Methods**: analyzers.toon_analyzer.ToonAnalyzer.__init__, analyzers.toon_analyzer.ToonAnalyzer.analyze_project, analyzers.toon_analyzer.ToonAnalyzer.analyze_from_toon_content, analyzers.toon_analyzer.ToonAnalyzer._find_toon_files, analyzers.toon_analyzer.ToonAnalyzer._select_project_key, analyzers.toon_analyzer.ToonAnalyzer._process_project_ton, analyzers.toon_analyzer.ToonAnalyzer._convert_modules_to_metrics, analyzers.toon_analyzer.ToonAnalyzer._process_hotspots, analyzers.toon_analyzer.ToonAnalyzer._process_alerts, analyzers.toon_analyzer.ToonAnalyzer._process_duplicates

### awareness.timeline_toon.ToonCollector
> Collects and processes toon files from git history.
- **Methods**: 10
- **Key Methods**: awareness.timeline_toon.ToonCollector.__init__, awareness.timeline_toon.ToonCollector.snapshot_for_commit, awareness.timeline_toon.ToonCollector._collect_toon_contents, awareness.timeline_toon.ToonCollector._empty_toon_contents, awareness.timeline_toon.ToonCollector._store_toon_content, awareness.timeline_toon.ToonCollector._toon_bucket, awareness.timeline_toon.ToonCollector._sorted_toon_candidates, awareness.timeline_toon.ToonCollector._toon_candidate_priority, awareness.timeline_toon.ToonCollector._is_duplication_file, awareness.timeline_toon.ToonCollector._is_validation_file

### commands.multi_project.MultiProjectReport
> Zbiorczy raport z analizy wielu projektów.
- **Methods**: 9
- **Key Methods**: commands.multi_project.MultiProjectReport.total_projects, commands.multi_project.MultiProjectReport.successful, commands.multi_project.MultiProjectReport.failed, commands.multi_project.MultiProjectReport.aggregate_avg_cc, commands.multi_project.MultiProjectReport.aggregate_critical, commands.multi_project.MultiProjectReport.aggregate_files, commands.multi_project.MultiProjectReport.worst_projects, commands.multi_project.MultiProjectReport.summary, commands.multi_project.MultiProjectReport.to_dict

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

### llm.LLMLayer
> Warstwa abstrakcji nad LLM z obsługą:
- wywołań tekstowych
- odpowiedzi JSON
- zliczania tokenów
- f
- **Methods**: 8
- **Key Methods**: llm.LLMLayer.__init__, llm.LLMLayer._load_provider_key, llm.LLMLayer._resolve_provider_key, llm.LLMLayer._build_completion_kwargs, llm.LLMLayer.call, llm.LLMLayer.call_json, llm.LLMLayer.reflect, llm.LLMLayer.total_calls

### analyzers.analyzer.CodeAnalyzer
> Główny analizator kodu — fasada.

Deleguje do ToonAnalyzer (toon), PythonAnalyzer (AST) i PathResolv
- **Methods**: 8
- **Key Methods**: analyzers.analyzer.CodeAnalyzer.__init__, analyzers.analyzer.CodeAnalyzer.analyze_project, analyzers.analyzer.CodeAnalyzer.analyze_from_toon_content, analyzers.analyzer.CodeAnalyzer.resolve_file_path, analyzers.analyzer.CodeAnalyzer.extract_function_source, analyzers.analyzer.CodeAnalyzer.find_worst_function, analyzers.analyzer.CodeAnalyzer.resolve_metrics_paths, analyzers.analyzer.CodeAnalyzer._ast_cyclomatic_complexity

### analyzers.semantic_chunker.SemanticChunker
> Buduje semantyczne chunki kodu dla LLM.
- **Methods**: 8
- **Key Methods**: analyzers.semantic_chunker.SemanticChunker.chunk_function, analyzers.semantic_chunker.SemanticChunker._parse_source, analyzers.semantic_chunker.SemanticChunker._build_chunk, analyzers.semantic_chunker.SemanticChunker.chunk_file, analyzers.semantic_chunker.SemanticChunker._find_nodes, analyzers.semantic_chunker.SemanticChunker._extract_relevant_imports, analyzers.semantic_chunker.SemanticChunker._extract_class_context, analyzers.semantic_chunker.SemanticChunker._extract_neighbors

### dsl.rule_generator.RuleGenerator
> Generuje nowe reguły DSL z historii refaktoryzacji w pamięci agenta.
- **Methods**: 8
- **Key Methods**: dsl.rule_generator.RuleGenerator.__init__, dsl.rule_generator.RuleGenerator.generate, dsl.rule_generator.RuleGenerator.generate_from_history, dsl.rule_generator.RuleGenerator.save, dsl.rule_generator.RuleGenerator.load_and_register, dsl.rule_generator.RuleGenerator._extract_patterns, dsl.rule_generator.RuleGenerator._history_to_patterns, dsl.rule_generator.RuleGenerator._patterns_to_rules

### history.HistoryReader
> Read-only access to .redsl/history.jsonl for querying and dedup.
- **Methods**: 7
- **Key Methods**: history.HistoryReader.__init__, history.HistoryReader.load_events, history.HistoryReader.filter_by_file, history.HistoryReader.filter_by_type, history.HistoryReader.has_recent_proposal, history.HistoryReader.has_recent_ticket, history.HistoryReader.generate_decision_report

### refactors.direct_guard.DirectGuardRefactorer
> Handles main guard wrapping for module-level execution code.
- **Methods**: 7
- **Key Methods**: refactors.direct_guard.DirectGuardRefactorer.__init__, refactors.direct_guard.DirectGuardRefactorer._is_main_guard_node, refactors.direct_guard.DirectGuardRefactorer._collect_guarded_lines, refactors.direct_guard.DirectGuardRefactorer._collect_module_execution_lines, refactors.direct_guard.DirectGuardRefactorer._insert_main_guard, refactors.direct_guard.DirectGuardRefactorer.fix_module_execution_block, refactors.direct_guard.DirectGuardRefactorer.get_applied_changes

### refactors.direct_constants.DirectConstantsRefactorer
> Handles magic number to constant extraction.
- **Methods**: 7
- **Key Methods**: refactors.direct_constants.DirectConstantsRefactorer.__init__, refactors.direct_constants.DirectConstantsRefactorer._build_value_to_names_map, refactors.direct_constants.DirectConstantsRefactorer._find_import_end_line, refactors.direct_constants.DirectConstantsRefactorer._replace_magic_numbers, refactors.direct_constants.DirectConstantsRefactorer.extract_constants, refactors.direct_constants.DirectConstantsRefactorer._generate_constant_name, refactors.direct_constants.DirectConstantsRefactorer.get_applied_changes

## Data Transformation Functions

Key functions that process and transform data:

### commands.doctor_fstring_fixers._write_if_parses
- **Output to**: path.write_text, ast.parse

### commands._guard_fixers._process_guard_and_indent
> Process lines to remove guard blocks and fix excess indentation.
- **Output to**: len, None.rstrip, _GUARD_RE.match, new_lines.append, commands._guard_fixers._handle_guard

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

### commands.cli_doctor._format_check_report
> Format doctor check report as text.
- **Output to**: None.join, lines.append, lines.append, lines.append

### commands.cli_doctor._format_heal_report
> Format doctor heal report as text.
- **Output to**: lines.append, None.join, lines.append, lines.append, lines.append

### commands.cli_doctor._format_batch_report
> Format doctor batch report as text.
- **Output to**: lines.append, None.join, len, len, len

### commands.hybrid._process_single_project
> Process a single project and return results.
- **Output to**: commands.hybrid._count_todo_issues, commands.hybrid.run_hybrid_quality_refactor, commands.hybrid._regenerate_todo, commands.hybrid._count_todo_issues, print

### commands._indent_fixers._process_def_block
> Handle a def/class/try block: fix body indent or strip excess indent.
- **Output to**: new_lines.append, commands._indent_fixers._scan_next_nonblank, len, len, len

### commands.batch_pyqual.runner._format_project_status
> Format project result status into readable parts.
- **Output to**: parts.extend, parts.extend, parts.extend, parts.append, None.join

### commands.batch_pyqual.pipeline._validate_config
> Validate pyqual config.
- **Output to**: pyqual_bridge.validate_config, print, ctx.result.errors.append, print, print

### commands.batch_pyqual.pipeline.process_project
> Full ReDSL + pyqual pipeline for a single project.

This is the main entry point that orchestrates a
- **Output to**: commands.batch_pyqual.pipeline._init_project_context, commands.batch_pyqual.pipeline._validate_config, commands.batch_pyqual.pipeline._run_analysis_stage, commands.batch_pyqual.pipeline._run_redsl_fix_stage, commands.batch_pyqual.pipeline._run_gates_stage

### commands.autofix.pipeline._process_project
> Full autofix pipeline for a single project.
- **Output to**: ProjectFixResult, commands.autofix.pipeline._stage_collect_metrics, commands.autofix.pipeline._stage_ensure_todo, commands.autofix.pipeline._stage_apply_fixes, commands.autofix.pipeline._stage_quality_gate_check

### commands.pyqual.mypy_analyzer.MypyAnalyzer._parse_mypy_line
> Parsuj jedną linię wyjścia mypy.
- **Output to**: line.split, line.strip, len, int, None.strip

### commands.autonomy_pr.analyzer._parse_worktree_changes
> Parse `git status --porcelain` output into a list of file paths.
- **Output to**: status_output.splitlines, None.strip, len, paths.append

### examples._common.parse_scenario
- **Output to**: argparse.ArgumentParser, parser.add_argument, parser.parse_args

### diagnostics.perf_bridge._parse_metrun_output
> Parsuj wyjście `metrun inspect` (JSON lub plain text).
- **Output to**: stdout.strip, PerformanceReport, json.loads, PerformanceReport, Bottleneck

### diagnostics.perf_bridge._parse_profile_bottlenecks
- **Output to**: stats_output.splitlines, bottlenecks.sort, line.split, None.isdigit, len

### autonomy.review._parse_changed_files_from_diff
> Extract changed file paths from a unified diff.
- **Output to**: diff.splitlines, line.startswith, None.strip, path.endswith, paths.append

### formatters.cycle.format_cycle_report_yaml
> Format full cycle report as YAML for stdout.
- **Output to**: yaml.dump, formatters.core._get_timestamp, formatters.refactor._serialize_analysis, formatters.refactor._serialize_decision, round

### formatters.cycle.format_cycle_report_markdown
> Format a refactor cycle as a Markdown report.
- **Output to**: None.strftime, lines.extend, lines.extend, lines.extend, lines.extend

### formatters.cycle.format_plan_yaml
> Format dry-run plan as YAML for stdout.
- **Output to**: yaml.dump, formatters.core._get_timestamp, formatters.refactor._serialize_analysis, formatters.refactor._serialize_decision, len

### formatters.cycle._serialize_result
> Serialize a RefactorResult to dict.
- **Output to**: round

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `examples.memory_learning.run_memory_learning_example` - 78 calls
- `examples.audit.run_audit_example` - 69 calls
- `examples.pr_bot.run_pr_bot_example` - 69 calls
- `examples.badge.run_badge_example` - 50 calls
- `examples.awareness.run_awareness_example` - 41 calls
- `examples.pyqual_example.run_pyqual_example` - 41 calls
- `examples.custom_rules.run_custom_rules_example` - 34 calls
- `cli.refactor.refactor` - 32 calls
- `examples.basic_analysis.run_basic_analysis_example` - 31 calls
- `commands.batch.run_semcod_batch` - 30 calls
- `refactors.engine.RefactorEngine.generate_proposal` - 28 calls
- `commands.autonomy_pr.run_autonomous_pr` - 27 calls
- `examples.full_pipeline.run_full_pipeline_example` - 27 calls
- `refactors.prompts.build_ecosystem_context` - 27 calls
- `analyzers.parsers.duplication_parser.DuplicationParser.parse_duplication_toon` - 27 calls
- `examples.api_integration.run_api_integration_example` - 26 calls
- `execution.cycle.run_cycle` - 23 calls
- `commands.hybrid.run_hybrid_quality_refactor` - 21 calls
- `commands.autofix.runner.run_autofix_batch` - 21 calls
- `commands.pyqual.reporter.Reporter.calculate_metrics` - 21 calls
- `main.cmd_refactor` - 21 calls
- `cli.scan.scan` - 21 calls
- `awareness.AwarenessManager.build_snapshot` - 20 calls
- `awareness.health_model.HealthModel.assess` - 20 calls
- `validation.vallm_bridge.validate_proposal` - 20 calls
- `commands.pyqual.run_pyqual_fix` - 19 calls
- `autonomy.metrics.collect_autonomy_metrics` - 19 calls
- `formatters.batch.format_batch_results` - 19 calls
- `formatters.batch.format_batch_report_markdown` - 19 calls
- `refactors.body_restorer.repair_file` - 19 calls
- `analyzers.redup_bridge.scan_duplicates` - 19 calls
- `analyzers.toon_analyzer.ToonAnalyzer.analyze_from_toon_content` - 19 calls
- `cli.logging.setup_logging` - 19 calls
- `history.HistoryReader.generate_decision_report` - 18 calls
- `commands.planfile_bridge.create_ticket` - 18 calls
- `commands.doctor_detectors.detect_version_mismatch` - 18 calls
- `commands.batch_pyqual.runner.run_pyqual_batch` - 18 calls
- `autonomy.scheduler.Scheduler.run` - 18 calls
- `autonomy.growth_control.check_module_budget` - 18 calls
- `cli.batch.batch_pyqual_run` - 18 calls

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