# System Architecture Analysis

## Overview

- **Project**: /home/tom/github/semcod/redsl/redsl
- **Primary Language**: python
- **Languages**: python: 124
- **Analysis Mode**: static
- **Total Functions**: 718
- **Total Classes**: 109
- **Modules**: 124
- **Entry Points**: 0

## Architecture by Module

### root.cli
- **Functions**: 24
- **File**: `cli.py`

### batch_1.cli
- **Functions**: 24
- **File**: `cli.py`

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

### analyzers.radon_analyzer
- **Functions**: 20
- **File**: `radon_analyzer.py`

### root.memory
- **Functions**: 18
- **Classes**: 4
- **File**: `__init__.py`

### analyzers.parsers.project_parser
- **Functions**: 18
- **Classes**: 1
- **File**: `project_parser.py`

### batch_1.memory
- **Functions**: 18
- **Classes**: 4
- **File**: `__init__.py`

### analyzers.incremental
- **Functions**: 17
- **Classes**: 2
- **File**: `incremental.py`

### commands.scan
- **Functions**: 16
- **Classes**: 1
- **File**: `scan.py`

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

### batch_1.awareness
- **Functions**: 16
- **Classes**: 2
- **File**: `__init__.py`

### refactors.direct_imports
- **Functions**: 15
- **Classes**: 1
- **File**: `direct_imports.py`

### analyzers.quality_visitor
- **Functions**: 15
- **Classes**: 1
- **File**: `quality_visitor.py`

### root.formatters
- **Functions**: 13
- **File**: `formatters.py`

### commands.doctor_indent_fixers
- **Functions**: 13
- **File**: `doctor_indent_fixers.py`

### autonomy.auto_fix
- **Functions**: 13
- **Classes**: 1
- **File**: `auto_fix.py`

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

### analyzers.quality_visitor.CodeQualityVisitor
> Detects common code quality issues in Python AST.
- **Methods**: 15
- **Key Methods**: analyzers.quality_visitor.CodeQualityVisitor.__init__, analyzers.quality_visitor.CodeQualityVisitor.visit_Import, analyzers.quality_visitor.CodeQualityVisitor.visit_ImportFrom, analyzers.quality_visitor.CodeQualityVisitor.visit_Name, analyzers.quality_visitor.CodeQualityVisitor.visit_Assign, analyzers.quality_visitor.CodeQualityVisitor.visit_Attribute, analyzers.quality_visitor.CodeQualityVisitor.visit_Constant, analyzers.quality_visitor.CodeQualityVisitor.visit_FunctionDef, analyzers.quality_visitor.CodeQualityVisitor.visit_AsyncFunctionDef, analyzers.quality_visitor.CodeQualityVisitor.visit_If
- **Inherits**: ast.NodeVisitor

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

### analyzers.analyzer.CodeAnalyzer
> Główny analizator kodu — fasada.

Deleguje do ToonAnalyzer (toon), PythonAnalyzer (AST) i PathResolv
- **Methods**: 8
- **Key Methods**: analyzers.analyzer.CodeAnalyzer.__init__, analyzers.analyzer.CodeAnalyzer.analyze_project, analyzers.analyzer.CodeAnalyzer.analyze_from_toon_content, analyzers.analyzer.CodeAnalyzer.resolve_file_path, analyzers.analyzer.CodeAnalyzer.extract_function_source, analyzers.analyzer.CodeAnalyzer.find_worst_function, analyzers.analyzer.CodeAnalyzer.resolve_metrics_paths, analyzers.analyzer.CodeAnalyzer._ast_cyclomatic_complexity

### dsl.rule_generator.RuleGenerator
> Generuje nowe reguły DSL z historii refaktoryzacji w pamięci agenta.
- **Methods**: 8
- **Key Methods**: dsl.rule_generator.RuleGenerator.__init__, dsl.rule_generator.RuleGenerator.generate, dsl.rule_generator.RuleGenerator.generate_from_history, dsl.rule_generator.RuleGenerator.save, dsl.rule_generator.RuleGenerator.load_and_register, dsl.rule_generator.RuleGenerator._extract_patterns, dsl.rule_generator.RuleGenerator._history_to_patterns, dsl.rule_generator.RuleGenerator._patterns_to_rules

### refactors.direct_guard.DirectGuardRefactorer
> Handles main guard wrapping for module-level execution code.
- **Methods**: 7
- **Key Methods**: refactors.direct_guard.DirectGuardRefactorer.__init__, refactors.direct_guard.DirectGuardRefactorer._is_main_guard_node, refactors.direct_guard.DirectGuardRefactorer._collect_guarded_lines, refactors.direct_guard.DirectGuardRefactorer._collect_module_execution_lines, refactors.direct_guard.DirectGuardRefactorer._insert_main_guard, refactors.direct_guard.DirectGuardRefactorer.fix_module_execution_block, refactors.direct_guard.DirectGuardRefactorer.get_applied_changes

### refactors.direct_constants.DirectConstantsRefactorer
> Handles magic number to constant extraction.
- **Methods**: 7
- **Key Methods**: refactors.direct_constants.DirectConstantsRefactorer.__init__, refactors.direct_constants.DirectConstantsRefactorer._build_value_to_names_map, refactors.direct_constants.DirectConstantsRefactorer._find_import_end_line, refactors.direct_constants.DirectConstantsRefactorer._replace_magic_numbers, refactors.direct_constants.DirectConstantsRefactorer.extract_constants, refactors.direct_constants.DirectConstantsRefactorer._generate_constant_name, refactors.direct_constants.DirectConstantsRefactorer.get_applied_changes

### awareness.timeline_git.GitTimelineProvider
> Provides git-based timeline data.
- **Methods**: 7
- **Key Methods**: awareness.timeline_git.GitTimelineProvider.__init__, awareness.timeline_git.GitTimelineProvider._resolve_repo_root, awareness.timeline_git.GitTimelineProvider._project_rel_path, awareness.timeline_git.GitTimelineProvider._git_log, awareness.timeline_git.GitTimelineProvider._git_show, awareness.timeline_git.GitTimelineProvider._is_duplication_file, awareness.timeline_git.GitTimelineProvider._is_validation_file

### awareness.timeline_analysis.TimelineAnalyzer
> Analyzes metric trends from timeline data.
- **Methods**: 7
- **Key Methods**: awareness.timeline_analysis.TimelineAnalyzer.analyze_trends, awareness.timeline_analysis.TimelineAnalyzer.predict_future_state, awareness.timeline_analysis.TimelineAnalyzer.find_degradation_sources, awareness.timeline_analysis.TimelineAnalyzer._build_series_map, awareness.timeline_analysis.TimelineAnalyzer._apply_trend_aliases, awareness.timeline_analysis.TimelineAnalyzer._linear_regression, awareness.timeline_analysis.TimelineAnalyzer._analyze_series

### analyzers.incremental.EvolutionaryCache
> Cache wyników analizy per-plik oparty o hash pliku.

Pozwala pomijać ponowną analizę niezmiennych pl
- **Methods**: 7
- **Key Methods**: analyzers.incremental.EvolutionaryCache.__init__, analyzers.incremental.EvolutionaryCache._load, analyzers.incremental.EvolutionaryCache.save, analyzers.incremental.EvolutionaryCache.get, analyzers.incremental.EvolutionaryCache.set, analyzers.incremental.EvolutionaryCache.invalidate, analyzers.incremental.EvolutionaryCache.clear

## Data Transformation Functions

Key functions that process and transform data:

### formatters.format_refactor_plan
> Format refactoring plan in specified format.
- **Output to**: formatters._format_yaml, formatters._format_json, formatters._format_text

### formatters._format_yaml
> Format as YAML.
- **Output to**: yaml.dump, formatters._get_timestamp, formatters._serialize_analysis, formatters._serialize_decision, len

### formatters._format_json
> Format as JSON.
- **Output to**: json.dumps, formatters._get_timestamp, formatters._serialize_analysis, formatters._serialize_decision, len

### formatters._format_text
> Format as rich text.
- **Output to**: output.append, formatters._count_decision_types, output.append, output.append, enumerate

### formatters._serialize_analysis
> Serialize analysis object to dict.
- **Output to**: len, len, str

### formatters._serialize_decision
> Serialize decision object to dict.
- **Output to**: hasattr, hasattr, hasattr, str, hasattr

### formatters.format_batch_results
> Format batch processing results.
- **Output to**: yaml.dump, json.dumps, enumerate, len, sum

### formatters.format_cycle_report_yaml
> Format full cycle report as YAML for stdout.
- **Output to**: yaml.dump, formatters._get_timestamp, formatters._serialize_analysis, formatters._serialize_decision, round

### formatters.format_plan_yaml
> Format dry-run plan as YAML for stdout.
- **Output to**: yaml.dump, formatters._get_timestamp, formatters._serialize_analysis, formatters._serialize_decision, len

### formatters._serialize_result
> Serialize a RefactorResult to dict.
- **Output to**: round

### formatters.format_debug_info
> Format debug information.
- **Output to**: yaml.dump, json.dumps, info.items, None.join, isinstance

### commands.doctor_indent_fixers._process_guard_and_indent
- **Output to**: len, None.rstrip, _GUARD_RE.match, new_lines.append, commands.doctor_indent_fixers._handle_guard

### commands.doctor_fstring_fixers._write_if_parses
- **Output to**: path.write_text, ast.parse

### commands.hybrid._process_single_project
> Process a single project and return results.
- **Output to**: commands.hybrid._count_todo_issues, commands.hybrid.run_hybrid_quality_refactor, commands.hybrid._regenerate_todo, commands.hybrid._count_todo_issues, print

### commands.pyqual.mypy_analyzer.MypyAnalyzer._parse_mypy_line
> Parsuj jedną linię wyjścia mypy.
- **Output to**: line.split, line.strip, len, int, None.strip

### diagnostics.perf_bridge._parse_metrun_output
> Parsuj wyjście `metrun inspect` (JSON lub plain text).
- **Output to**: stdout.strip, PerformanceReport, json.loads, PerformanceReport, Bottleneck

### diagnostics.perf_bridge._parse_profile_bottlenecks
- **Output to**: stats_output.splitlines, bottlenecks.sort, line.split, None.isdigit, len

### autonomy.review._parse_changed_files_from_diff
> Extract changed file paths from a unified diff.
- **Output to**: diff.splitlines, line.startswith, None.strip, path.endswith, paths.append

### execution.validation._validate_with_regix
> Validate changes with regix and update report.
- **Output to**: regix_bridge.validate_working_tree, regix_bridge.check_gates, regix_report.get, report.errors.append, logger.info

### refactors.engine.RefactorEngine._parse_confidence
> Normalize a confidence value coming back from the LLM.
- **Output to**: round, float

### refactors.engine.RefactorEngine.validate_proposal
> Waliduj propozycję: syntax check + basic sanity + vallm pipeline (jeśli dostępny).
- **Output to**: RefactorResult, vallm_bridge.is_available, vallm_bridge.validate_proposal, len, code.strip

### refactors.direct_imports.DirectImportRefactorer._format_alias

### validation.vallm_bridge.validate_patch
> Waliduj wygenerowany kod przez pipeline vallm.

Zapisuje kod do tymczasowego workspace, uruchamia va
- **Output to**: Path, Path, validation.vallm_bridge.is_available, tempfile.mkdtemp, validation.vallm_bridge._stage_validation_context

### validation.vallm_bridge.validate_proposal
> Waliduj wszystkie zmiany w propozycji refaktoryzacji.

Args:
    proposal: Propozycja z listą FileCh
- **Output to**: validation.vallm_bridge.is_available, Path, analyzers.incremental.EvolutionaryCache.set, validation.vallm_bridge.validate_patch, scores.append

### validation.pyqual_bridge.validate_config
> Run `pyqual validate` to check pyqual.yaml is well-formed.

Returns:
    (valid: bool, message: str)
- **Output to**: validation.pyqual_bridge.is_available, subprocess.run, logger.warning, str, output.strip

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `commands.cli_autonomy.register` - 114 calls
- `commands.cli_awareness.register` - 48 calls
- `commands.cli_doctor.register` - 48 calls
- `commands.pyqual.run_pyqual_analysis` - 35 calls
- `refactors.engine.RefactorEngine.generate_proposal` - 28 calls
- `commands.batch.run_semcod_batch` - 27 calls
- `refactors.prompts.build_ecosystem_context` - 27 calls
- `analyzers.semantic_chunker.SemanticChunker.chunk_function` - 27 calls
- `analyzers.parsers.duplication_parser.DuplicationParser.parse_duplication_toon` - 27 calls
- `cli.refactor` - 25 calls
- `main.cmd_refactor` - 21 calls
- `commands.hybrid.run_hybrid_quality_refactor` - 21 calls
- `commands.pyqual.reporter.Reporter.calculate_metrics` - 21 calls
- `cli.scan` - 21 calls
- `awareness.AwarenessManager.build_snapshot` - 20 calls
- `awareness.health_model.HealthModel.assess` - 20 calls
- `validation.vallm_bridge.validate_proposal` - 20 calls
- `cli.debug_decisions` - 20 calls
- `formatters.format_batch_results` - 19 calls
- `commands.pyqual.run_pyqual_fix` - 19 calls
- `execution.cycle.run_cycle` - 19 calls
- `refactors.body_restorer.repair_file` - 19 calls
- `analyzers.redup_bridge.scan_duplicates` - 19 calls
- `analyzers.toon_analyzer.ToonAnalyzer.analyze_from_toon_content` - 19 calls
- `commands.doctor_detectors.detect_version_mismatch` - 18 calls
- `autonomy.growth_control.check_module_budget` - 18 calls
- `autonomy.scheduler.Scheduler.run` - 18 calls
- `execution.reporter.explain_decisions` - 18 calls
- `dsl.engine.DSLEngine.add_rules_from_yaml` - 18 calls
- `commands.doctor_fixers.fix_module_level_exit` - 17 calls
- `refactors.engine.RefactorEngine.validate_proposal` - 17 calls
- `refactors.direct_constants.DirectConstantsRefactorer.extract_constants` - 17 calls
- `validation.sandbox.RefactorSandbox.apply_and_test` - 17 calls
- `commands.scan.render_markdown` - 16 calls
- `commands.pyqual.ruff_analyzer.RuffAnalyzer.analyze` - 16 calls
- `execution.sandbox_execution.execute_sandboxed` - 16 calls
- `llm.LLMLayer.call_json` - 16 calls
- `analyzers.parsers.validation_parser.ValidationParser.parse_validation_toon` - 16 calls
- `autonomy.quality_gate.run_quality_gate` - 15 calls
- `execution.cycle.run_from_toon_content` - 15 calls

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