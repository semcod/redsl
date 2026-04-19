# System Architecture Analysis

## Overview

- **Project**: /home/tom/github/semcod/redsl
- **Primary Language**: python
- **Languages**: python: 196, shell: 2
- **Analysis Mode**: static
- **Total Functions**: 1122
- **Total Classes**: 132
- **Modules**: 198
- **Entry Points**: 570

## Architecture by Module

### redsl.commands.batch_pyqual.reporting
- **Functions**: 25
- **File**: `reporting.py`

### redsl.awareness.git_timeline
- **Functions**: 23
- **Classes**: 1
- **File**: `git_timeline.py`

### redsl.analyzers.radon_analyzer
- **Functions**: 23
- **File**: `radon_analyzer.py`

### redsl.main
- **Functions**: 23
- **File**: `main.py`

### redsl.commands.cli_autonomy
- **Functions**: 20
- **File**: `cli_autonomy.py`

### redsl.memory
- **Functions**: 18
- **Classes**: 4
- **File**: `__init__.py`

### redsl.analyzers.parsers.project_parser
- **Functions**: 18
- **Classes**: 1
- **File**: `project_parser.py`

### redsl.analyzers.quality_visitor
- **Functions**: 18
- **Classes**: 1
- **File**: `quality_visitor.py`

### redsl.analyzers.incremental
- **Functions**: 17
- **Classes**: 2
- **File**: `incremental.py`

### redsl.commands.doctor_detectors
- **Functions**: 16
- **File**: `doctor_detectors.py`

### archive.legacy_scripts.hybrid_llm_refactor
- **Functions**: 16
- **File**: `hybrid_llm_refactor.py`

### redsl.awareness
- **Functions**: 16
- **Classes**: 2
- **File**: `__init__.py`

### redsl.autonomy.scheduler
- **Functions**: 16
- **Classes**: 2
- **File**: `scheduler.py`

### redsl.llm.llx_router
- **Functions**: 15
- **Classes**: 1
- **File**: `llx_router.py`

### redsl.commands.hybrid
- **Functions**: 14
- **File**: `hybrid.py`

### redsl.cli.examples
- **Functions**: 14
- **File**: `examples.py`

### redsl.commands.batch_pyqual.pipeline
- **Functions**: 14
- **Classes**: 1
- **File**: `pipeline.py`

### redsl.refactors.direct_imports
- **Functions**: 14
- **Classes**: 1
- **File**: `direct_imports.py`

### redsl.history
- **Functions**: 13
- **Classes**: 3
- **File**: `history.py`

### redsl.commands.pyqual
- **Functions**: 13
- **Classes**: 1
- **File**: `__init__.py`

## Key Entry Points

Main execution flows into the system:

### archive.legacy_scripts.batch_refactor_semcod.main
> Process semcod projects.
- **Calls**: Path, semcod_root.iterdir, print, sorted, print, print, print, print

### archive.legacy_scripts.batch_quality_refactor.main
> Process semcod projects.
- **Calls**: Path, semcod_root.iterdir, print, sorted, print, print, print, sum

### redsl.analyzers.sumd_bridge.SumdAnalyzer.generate_map_toon
> Generate map.toon.yaml content compatible with redsl.

Args:
    project_dir: Path to project root

Returns:
    map.toon.yaml content as string
- **Calls**: self.analyze, None.isoformat, None.join, a, a, a, None.join, a

### archive.legacy_scripts.apply_semcod_refactor.main
> Apply reDSL to a semcod project.
- **Calls**: Path, logger.info, AgentConfig, RefactorOrchestrator, print, orchestrator.explain_decisions, print, len

### redsl.refactors.engine.RefactorEngine.generate_proposal
> Wygeneruj propozycję refaktoryzacji na podstawie decyzji DSL.
- **Calls**: PROMPTS.get, redsl.refactors.prompts.build_ecosystem_context, prompt_template.format, self.llm.call_json, response_data.get, self._resolve_confidence, RefactorProposal, logger.info

### redsl.analyzers.parsers.duplication_parser.DuplicationParser.parse_duplication_toon
> Parsuj duplication_toon — obsługuje formaty legacy i code2llm [hash] ! STRU.
- **Calls**: content.splitlines, line.strip, duplicates.append, re.search, stripped.startswith, re.search, duplicates.append, re.match

### archive.legacy_scripts.debug_decisions.debug_decisions
> Show all decisions generated for a project.
- **Calls**: print, print, print, AgentConfig.from_env, RefactorOrchestrator, CodeAnalyzer, analyzer.analyze_project, analysis.to_dsl_contexts

### archive.legacy_scripts.debug_llm_config.debug_llm
> Debug LLM configuration.
- **Calls**: print, print, print, print, print, print, print, AgentConfig.from_env

### redsl.cli.refactor.refactor
> Run refactoring on a project.
- **Calls**: click.command, click.argument, click.option, click.option, click.option, click.option, click.option, click.option

### redsl.execution.cycle.run_cycle
> Run a complete refactoring cycle.
- **Calls**: redsl.execution.cycle._new_cycle_report, logger.info, redsl.execution.cycle._analyze_project, redup_bridge.is_available, redsl.execution.cycle._summarize_analysis, logger.info, archive.legacy_scripts.hybrid_llm_refactor._select_decisions, len

### redsl.awareness.timeline_analysis.TimelineAnalyzer._analyze_series
- **Calls**: float, TimelineAnalyzer._linear_regression, max, max, min, TrendAnalysis, TrendAnalysis, float

### redsl.analyzers.python_analyzer.PythonAnalyzer._scan_top_nodes
> Iteruj po węzłach top-level i class-level, zbieraj CC, nesting i alerty.
- **Calls**: rel_path.endswith, ast.iter_child_nodes, isinstance, ast.iter_child_nodes, isinstance, isinstance, redsl.analyzers.python_analyzer.ast_cyclomatic_complexity, redsl.analyzers.python_analyzer.ast_max_nesting_depth

### redsl.awareness.AwarenessManager.build_snapshot
- **Calls**: None.resolve, self._build_cache_key, GitTimelineAnalyzer, timeline_analyzer.build_timeline, timeline_analyzer.analyze_trends, ChangePatternLearner, pattern_learner.learn_from_timeline, self.health_model.assess

### redsl.validation.vallm_bridge.validate_proposal
> Waliduj wszystkie zmiany w propozycji refaktoryzacji.

Args:
    proposal: Propozycja z listą FileChange.
    project_dir: Opcjonalny katalog projektu
- **Calls**: redsl.validation.vallm_bridge.is_available, Path, redsl.analyzers.incremental.EvolutionaryCache.set, redsl.validation.vallm_bridge.validate_patch, scores.append, tempfile.mkdtemp, shutil.rmtree, failures.append

### redsl.awareness.health_model.HealthModel.assess
- **Calls**: trends.get, trends.get, trends.get, self._bounded_score, self._bounded_score, self._bounded_score, self._bounded_score, self._status_for_score

### redsl.analyzers.parsers.project_parser.ProjectParser._parse_emoji_alert_line
> T001: Parsuj linie code2llm v2: 🟡 CC func_name CC=41 (limit:10)
- **Calls**: None.strip, re.match, match.group, re.search, re.search, alert_type_map.get, match.group, int

### redsl.commands.pyqual.run_pyqual_fix
> Run automatic fixes based on pyqual analysis.
- **Calls**: PyQualAnalyzer, pyqual_analyzer.analyze_project, print, AgentConfig, RefactorOrchestrator, CodeAnalyzer, code_analyzer.analyze_project, analysis.to_dsl_contexts

### redsl.analyzers.toon_analyzer.ToonAnalyzer.analyze_from_toon_content
> Analizuj z bezpośredniego contentu toon (bez plików).
- **Calls**: AnalysisResult, len, sum, self.parser.parse_project_toon, data.get, data.get, data.get, self.parser.parse_duplication_toon

### redsl.analyzers.toon_analyzer.ToonAnalyzer._process_project_ton
> Parsuj plik project_toon i zaktualizuj result.
- **Calls**: toon_file.read_text, project_data.get, health.get, health.get, health.get, project_data.get, health.get, health.get

### redsl.commands.doctor_detectors.detect_version_mismatch
> Find tests that hardcode a version string that differs from VERSION file.
- **Calls**: None.strip, re.compile, re.compile, redsl.commands.doctor_detectors._python_files, version_file.exists, tests_dir.is_dir, enumerate, version_file.read_text

### redsl.commands.batch_pyqual.runner.run_pyqual_batch
> Run ReDSL + pyqual on all projects in workspace.
- **Calls**: redsl.commands.batch_pyqual.discovery._filter_packages, redsl.commands.batch_pyqual.runner._pyqual_cli_available, _resolve_profile, redsl.commands.batch_pyqual.runner._print_batch_header, enumerate, redsl.commands.autofix.reporting._build_summary, redsl.commands.hybrid._print_summary, redsl.commands.batch_pyqual.reporting._save_report

### redsl.history.HistoryReader.generate_decision_report
> Generate a Markdown report of all decisions, thoughts and outcomes.
- **Calls**: self.load_events, lines.append, None.join, ev.get, ev.get, ev.get, ev.get, lines.append

### redsl.commands.pyqual.ast_analyzer.AstAnalyzer._analyze_file
> Przeanalizuj jeden plik AST.
- **Calls**: CodeQualityVisitor, visitor.visit, visitor.get_unused_imports, ast.walk, unused_imports.append, magic_numbers.append, print_statements.append, isinstance

### redsl.cli.batch.batch_pyqual_run
> Multi-project quality pipeline: ReDSL analysis + pyqual gates + optional push.
- **Calls**: batch.command, click.argument, click.option, click.option, click.option, click.option, click.option, click.option

### redsl.autonomy.growth_control.check_module_budget
> Check whether a module stays within its complexity budget.
- **Calls**: Path, BUDGETS.get, len, redsl.autonomy.growth_control._infer_module_type, file_path.read_text, source.splitlines, violations.append, ast.parse

### redsl.autonomy.scheduler.Scheduler.run
> Main scheduler loop — runs until stopped.
- **Calls**: logger.info, self._analyze, self._check_trends, self._check_proactive, asyncio.sleep, self._has_changes_since_last_check, logger.debug, self._report_findings

### redsl.dsl.engine.DSLEngine.add_rules_from_yaml
> Załaduj reguły z formatu YAML/dict.
- **Calls**: rd.get, when.items, rd.get, Rule, self.add_rule, isinstance, constraint.items, conditions.append

### redsl.commands.doctor_fixers.fix_module_level_exit
> Wrap bare sys.exit() calls in if __name__ == '__main__' guards.
- **Calls**: path.read_text, src.splitlines, line.strip, path.write_text, report.fixes_applied.append, report.errors.append, stripped.startswith, new_lines.append

### redsl.refactors.engine.RefactorEngine.validate_proposal
> Waliduj propozycję: syntax check + basic sanity + vallm pipeline (jeśli dostępny).
- **Calls**: RefactorResult, vallm_bridge.is_available, vallm_bridge.validate_proposal, len, code.strip, result.errors.append, compile, len

### redsl.refactors.direct_constants.DirectConstantsRefactorer.extract_constants
> Extract magic numbers into named constants.
- **Calls**: len, file_path.read_text, source.splitlines, self._build_value_to_names_map, ast.parse, self._find_import_end_line, lines.insert, self._replace_magic_numbers

## Process Flows

Key execution flows identified:

### Flow 1: main
```
main [archive.legacy_scripts.batch_refactor_semcod]
```

### Flow 2: generate_map_toon
```
generate_map_toon [redsl.analyzers.sumd_bridge.SumdAnalyzer]
```

### Flow 3: generate_proposal
```
generate_proposal [redsl.refactors.engine.RefactorEngine]
  └─ →> build_ecosystem_context
      └─> _format_trends
      └─> _format_alerts
```

### Flow 4: parse_duplication_toon
```
parse_duplication_toon [redsl.analyzers.parsers.duplication_parser.DuplicationParser]
```

### Flow 5: debug_decisions
```
debug_decisions [archive.legacy_scripts.debug_decisions]
```

### Flow 6: debug_llm
```
debug_llm [archive.legacy_scripts.debug_llm_config]
```

### Flow 7: refactor
```
refactor [redsl.cli.refactor]
```

### Flow 8: run_cycle
```
run_cycle [redsl.execution.cycle]
  └─> _new_cycle_report
  └─> _analyze_project
```

### Flow 9: _analyze_series
```
_analyze_series [redsl.awareness.timeline_analysis.TimelineAnalyzer]
```

### Flow 10: _scan_top_nodes
```
_scan_top_nodes [redsl.analyzers.python_analyzer.PythonAnalyzer]
```

## Key Classes

### redsl.awareness.git_timeline.GitTimelineAnalyzer
> Build a historical metric timeline from git commits — facade.

This is a thin facade that delegates 
- **Methods**: 23
- **Key Methods**: redsl.awareness.git_timeline.GitTimelineAnalyzer.__init__, redsl.awareness.git_timeline.GitTimelineAnalyzer.build_timeline, redsl.awareness.git_timeline.GitTimelineAnalyzer.analyze_trends, redsl.awareness.git_timeline.GitTimelineAnalyzer.predict_future_state, redsl.awareness.git_timeline.GitTimelineAnalyzer.find_degradation_sources, redsl.awareness.git_timeline.GitTimelineAnalyzer.summarize, redsl.awareness.git_timeline.GitTimelineAnalyzer._resolve_repo_root, redsl.awareness.git_timeline.GitTimelineAnalyzer._project_rel_path, redsl.awareness.git_timeline.GitTimelineAnalyzer._git_log, redsl.awareness.git_timeline.GitTimelineAnalyzer._snapshot_for_commit

### redsl.analyzers.parsers.project_parser.ProjectParser
> Parser sekcji project_toon.
- **Methods**: 18
- **Key Methods**: redsl.analyzers.parsers.project_parser.ProjectParser.parse_project_toon, redsl.analyzers.parsers.project_parser.ProjectParser._parse_header_lines, redsl.analyzers.parsers.project_parser.ProjectParser._detect_section_change, redsl.analyzers.parsers.project_parser.ProjectParser._parse_section_line, redsl.analyzers.parsers.project_parser.ProjectParser._parse_health_line, redsl.analyzers.parsers.project_parser.ProjectParser._parse_alerts_line, redsl.analyzers.parsers.project_parser.ProjectParser._parse_hotspots_line, redsl.analyzers.parsers.project_parser.ProjectParser._parse_modules_line, redsl.analyzers.parsers.project_parser.ProjectParser._parse_layers_section_line, redsl.analyzers.parsers.project_parser.ProjectParser._parse_refactors_line

### redsl.analyzers.quality_visitor.CodeQualityVisitor
> Detects common code quality issues in Python AST.
- **Methods**: 18
- **Key Methods**: redsl.analyzers.quality_visitor.CodeQualityVisitor.__init__, redsl.analyzers.quality_visitor.CodeQualityVisitor.visit_Import, redsl.analyzers.quality_visitor.CodeQualityVisitor.visit_ImportFrom, redsl.analyzers.quality_visitor.CodeQualityVisitor.visit_Name, redsl.analyzers.quality_visitor.CodeQualityVisitor.visit_Assign, redsl.analyzers.quality_visitor.CodeQualityVisitor.visit_Attribute, redsl.analyzers.quality_visitor.CodeQualityVisitor._get_root_name, redsl.analyzers.quality_visitor.CodeQualityVisitor.visit_Constant, redsl.analyzers.quality_visitor.CodeQualityVisitor._count_untyped_params, redsl.analyzers.quality_visitor.CodeQualityVisitor.visit_FunctionDef
- **Inherits**: ast.NodeVisitor

### redsl.autonomy.scheduler.Scheduler
> Periodic quality-improvement loop.
- **Methods**: 16
- **Key Methods**: redsl.autonomy.scheduler.Scheduler.__init__, redsl.autonomy.scheduler.Scheduler.run, redsl.autonomy.scheduler.Scheduler.stop, redsl.autonomy.scheduler.Scheduler.run_once, redsl.autonomy.scheduler.Scheduler._has_changes_since_last_check, redsl.autonomy.scheduler.Scheduler._git_head, redsl.autonomy.scheduler.Scheduler._analyze, redsl.autonomy.scheduler.Scheduler._check_trends, redsl.autonomy.scheduler.Scheduler._check_proactive, redsl.autonomy.scheduler.Scheduler._generate_proposals

### redsl.refactors.direct_imports.DirectImportRefactorer
> Handles import-related direct refactoring.
- **Methods**: 14
- **Key Methods**: redsl.refactors.direct_imports.DirectImportRefactorer.__init__, redsl.refactors.direct_imports.DirectImportRefactorer.remove_unused_imports, redsl.refactors.direct_imports.DirectImportRefactorer._collect_unused_import_edits, redsl.refactors.direct_imports.DirectImportRefactorer._collect_import_edits, redsl.refactors.direct_imports.DirectImportRefactorer._collect_import_from_edits, redsl.refactors.direct_imports.DirectImportRefactorer._is_star_import, redsl.refactors.direct_imports.DirectImportRefactorer._build_import_from_replacement, redsl.refactors.direct_imports.DirectImportRefactorer._alias_name, redsl.refactors.direct_imports.DirectImportRefactorer._format_alias, redsl.refactors.direct_imports.DirectImportRefactorer._remove_statement_lines
- **Inherits**: DirectRefactorBase

### redsl.awareness.AwarenessManager
> Facade that combines all awareness layers into one snapshot.
- **Methods**: 13
- **Key Methods**: redsl.awareness.AwarenessManager.__init__, redsl.awareness.AwarenessManager._memory_fingerprint, redsl.awareness.AwarenessManager._git_head, redsl.awareness.AwarenessManager._build_cache_key, redsl.awareness.AwarenessManager.build_snapshot, redsl.awareness.AwarenessManager.build_context, redsl.awareness.AwarenessManager.build_prompt_context, redsl.awareness.AwarenessManager.history, redsl.awareness.AwarenessManager.ecosystem, redsl.awareness.AwarenessManager.health

### redsl.analyzers.toon_analyzer.ToonAnalyzer
> Analizator plików toon — przetwarza dane z code2llm.
- **Methods**: 13
- **Key Methods**: redsl.analyzers.toon_analyzer.ToonAnalyzer.__init__, redsl.analyzers.toon_analyzer.ToonAnalyzer.analyze_project, redsl.analyzers.toon_analyzer.ToonAnalyzer.analyze_from_toon_content, redsl.analyzers.toon_analyzer.ToonAnalyzer._find_toon_files, redsl.analyzers.toon_analyzer.ToonAnalyzer._select_project_key, redsl.analyzers.toon_analyzer.ToonAnalyzer._process_project_ton, redsl.analyzers.toon_analyzer.ToonAnalyzer._convert_modules_to_metrics, redsl.analyzers.toon_analyzer.ToonAnalyzer._process_hotspots, redsl.analyzers.toon_analyzer.ToonAnalyzer._process_alerts, redsl.analyzers.toon_analyzer.ToonAnalyzer._process_duplicates

### redsl.analyzers.sumd_bridge.SumdAnalyzer
> Native project analyzer using sumd extractor patterns.

Pure-Python implementation that doesn't requ
- **Methods**: 11
- **Key Methods**: redsl.analyzers.sumd_bridge.SumdAnalyzer.__init__, redsl.analyzers.sumd_bridge.SumdAnalyzer.analyze, redsl.analyzers.sumd_bridge.SumdAnalyzer.generate_map_toon, redsl.analyzers.sumd_bridge.SumdAnalyzer._collect_modules, redsl.analyzers.sumd_bridge.SumdAnalyzer._detect_language, redsl.analyzers.sumd_bridge.SumdAnalyzer._analyze_py_file, redsl.analyzers.sumd_bridge.SumdAnalyzer._extract_function_info, redsl.analyzers.sumd_bridge.SumdAnalyzer._extract_class_info, redsl.analyzers.sumd_bridge.SumdAnalyzer._calculate_cc, redsl.analyzers.sumd_bridge.SumdAnalyzer._identify_hotspots

### redsl.awareness.timeline_toon.ToonCollector
> Collects and processes toon files from git history.
- **Methods**: 10
- **Key Methods**: redsl.awareness.timeline_toon.ToonCollector.__init__, redsl.awareness.timeline_toon.ToonCollector.snapshot_for_commit, redsl.awareness.timeline_toon.ToonCollector._collect_toon_contents, redsl.awareness.timeline_toon.ToonCollector._empty_toon_contents, redsl.awareness.timeline_toon.ToonCollector._store_toon_content, redsl.awareness.timeline_toon.ToonCollector._toon_bucket, redsl.awareness.timeline_toon.ToonCollector._sorted_toon_candidates, redsl.awareness.timeline_toon.ToonCollector._toon_candidate_priority, redsl.awareness.timeline_toon.ToonCollector._is_duplication_file, redsl.awareness.timeline_toon.ToonCollector._is_validation_file

### redsl.analyzers.semantic_chunker.SemanticChunker
> Buduje semantyczne chunki kodu dla LLM.
- **Methods**: 10
- **Key Methods**: redsl.analyzers.semantic_chunker.SemanticChunker._locate_function_data, redsl.analyzers.semantic_chunker.SemanticChunker._gather_chunk_contexts, redsl.analyzers.semantic_chunker.SemanticChunker.chunk_function, redsl.analyzers.semantic_chunker.SemanticChunker._parse_source, redsl.analyzers.semantic_chunker.SemanticChunker._build_chunk, redsl.analyzers.semantic_chunker.SemanticChunker.chunk_file, redsl.analyzers.semantic_chunker.SemanticChunker._find_nodes, redsl.analyzers.semantic_chunker.SemanticChunker._extract_relevant_imports, redsl.analyzers.semantic_chunker.SemanticChunker._extract_class_context, redsl.analyzers.semantic_chunker.SemanticChunker._extract_neighbors

### redsl.commands.multi_project.MultiProjectReport
> Zbiorczy raport z analizy wielu projektów.
- **Methods**: 9
- **Key Methods**: redsl.commands.multi_project.MultiProjectReport.total_projects, redsl.commands.multi_project.MultiProjectReport.successful, redsl.commands.multi_project.MultiProjectReport.failed, redsl.commands.multi_project.MultiProjectReport.aggregate_avg_cc, redsl.commands.multi_project.MultiProjectReport.aggregate_critical, redsl.commands.multi_project.MultiProjectReport.aggregate_files, redsl.commands.multi_project.MultiProjectReport.worst_projects, redsl.commands.multi_project.MultiProjectReport.summary, redsl.commands.multi_project.MultiProjectReport.to_dict

### redsl.refactors.engine.RefactorEngine
> Silnik refaktoryzacji z pętlą refleksji.

1. Generuj propozycję (LLM)
2. Reflektuj (self-critique)
3
- **Methods**: 9
- **Key Methods**: redsl.refactors.engine.RefactorEngine.__init__, redsl.refactors.engine.RefactorEngine.estimate_confidence, redsl.refactors.engine.RefactorEngine._parse_confidence, redsl.refactors.engine.RefactorEngine._resolve_confidence, redsl.refactors.engine.RefactorEngine.generate_proposal, redsl.refactors.engine.RefactorEngine.reflect_on_proposal, redsl.refactors.engine.RefactorEngine.validate_proposal, redsl.refactors.engine.RefactorEngine.apply_proposal, redsl.refactors.engine.RefactorEngine._save_proposal

### redsl.awareness.ecosystem.EcosystemGraph
> Basic ecosystem graph for semcod-style project collections.
- **Methods**: 9
- **Key Methods**: redsl.awareness.ecosystem.EcosystemGraph.build, redsl.awareness.ecosystem.EcosystemGraph.summarize, redsl.awareness.ecosystem.EcosystemGraph.project, redsl.awareness.ecosystem.EcosystemGraph.impacted_projects, redsl.awareness.ecosystem.EcosystemGraph._build_node, redsl.awareness.ecosystem.EcosystemGraph._link_dependencies, redsl.awareness.ecosystem.EcosystemGraph._read_dependencies, redsl.awareness.ecosystem.EcosystemGraph._extract_dependency_tokens, redsl.awareness.ecosystem.EcosystemGraph._is_project_dir

### redsl.autonomy.growth_control.GrowthController
> Enforce growth budgets on a project.
- **Methods**: 8
- **Key Methods**: redsl.autonomy.growth_control.GrowthController.__init__, redsl.autonomy.growth_control.GrowthController.check_growth, redsl.autonomy.growth_control.GrowthController.suggest_consolidation, redsl.autonomy.growth_control.GrowthController._measure_weekly_growth, redsl.autonomy.growth_control.GrowthController._find_untested_new_modules, redsl.autonomy.growth_control.GrowthController._find_oversized_files, redsl.autonomy.growth_control.GrowthController._find_tiny_modules, redsl.autonomy.growth_control.GrowthController._group_by_prefix

### redsl.llm.LLMLayer
> Warstwa abstrakcji nad LLM z obsługą:
- wywołań tekstowych
- odpowiedzi JSON
- zliczania tokenów
- f
- **Methods**: 8
- **Key Methods**: redsl.llm.LLMLayer.__init__, redsl.llm.LLMLayer._load_provider_key, redsl.llm.LLMLayer._resolve_provider_key, redsl.llm.LLMLayer._build_completion_kwargs, redsl.llm.LLMLayer.call, redsl.llm.LLMLayer.call_json, redsl.llm.LLMLayer.reflect, redsl.llm.LLMLayer.total_calls

### redsl.memory.AgentMemory
> Kompletny system pamięci z trzema warstwami.

- episodic: „co zrobiłem" — historia refaktoryzacji
- 
- **Methods**: 8
- **Key Methods**: redsl.memory.AgentMemory.__init__, redsl.memory.AgentMemory.remember_action, redsl.memory.AgentMemory.recall_similar_actions, redsl.memory.AgentMemory.learn_pattern, redsl.memory.AgentMemory.recall_patterns, redsl.memory.AgentMemory.store_strategy, redsl.memory.AgentMemory.recall_strategies, redsl.memory.AgentMemory.stats

### redsl.analyzers.analyzer.CodeAnalyzer
> Główny analizator kodu — fasada.

Deleguje do ToonAnalyzer (toon), PythonAnalyzer (AST) i PathResolv
- **Methods**: 8
- **Key Methods**: redsl.analyzers.analyzer.CodeAnalyzer.__init__, redsl.analyzers.analyzer.CodeAnalyzer.analyze_project, redsl.analyzers.analyzer.CodeAnalyzer.analyze_from_toon_content, redsl.analyzers.analyzer.CodeAnalyzer.resolve_file_path, redsl.analyzers.analyzer.CodeAnalyzer.extract_function_source, redsl.analyzers.analyzer.CodeAnalyzer.find_worst_function, redsl.analyzers.analyzer.CodeAnalyzer.resolve_metrics_paths, redsl.analyzers.analyzer.CodeAnalyzer._ast_cyclomatic_complexity

### redsl.dsl.rule_generator.RuleGenerator
> Generuje nowe reguły DSL z historii refaktoryzacji w pamięci agenta.
- **Methods**: 8
- **Key Methods**: redsl.dsl.rule_generator.RuleGenerator.__init__, redsl.dsl.rule_generator.RuleGenerator.generate, redsl.dsl.rule_generator.RuleGenerator.generate_from_history, redsl.dsl.rule_generator.RuleGenerator.save, redsl.dsl.rule_generator.RuleGenerator.load_and_register, redsl.dsl.rule_generator.RuleGenerator._extract_patterns, redsl.dsl.rule_generator.RuleGenerator._history_to_patterns, redsl.dsl.rule_generator.RuleGenerator._patterns_to_rules

### redsl.history.HistoryReader
> Read-only access to .redsl/history.jsonl for querying and dedup.
- **Methods**: 7
- **Key Methods**: redsl.history.HistoryReader.__init__, redsl.history.HistoryReader.load_events, redsl.history.HistoryReader.filter_by_file, redsl.history.HistoryReader.filter_by_type, redsl.history.HistoryReader.has_recent_proposal, redsl.history.HistoryReader.has_recent_ticket, redsl.history.HistoryReader.generate_decision_report

### redsl.awareness.timeline_git.GitTimelineProvider
> Provides git-based timeline data.
- **Methods**: 7
- **Key Methods**: redsl.awareness.timeline_git.GitTimelineProvider.__init__, redsl.awareness.timeline_git.GitTimelineProvider._resolve_repo_root, redsl.awareness.timeline_git.GitTimelineProvider._project_rel_path, redsl.awareness.timeline_git.GitTimelineProvider._git_log, redsl.awareness.timeline_git.GitTimelineProvider._git_show, redsl.awareness.timeline_git.GitTimelineProvider._is_duplication_file, redsl.awareness.timeline_git.GitTimelineProvider._is_validation_file

## Data Transformation Functions

Key functions that process and transform data:

### test_sample_project.sample.process_items
- **Output to**: results.append, results.append

### test_sample_project.sample.format_data
- **Output to**: formatted.append

### refactor_output.refactor_extract_functions_20260407_143102.00_app__models.process_data

### refactor_output.refactor_extract_functions_20260407_143102.00_app__models.validate_data

### redsl.commands.doctor_fstring_fixers._write_if_parses
- **Output to**: path.write_text, ast.parse

### redsl.commands._guard_fixers._process_guard_and_indent
> Process lines to remove guard blocks and fix excess indentation.
- **Output to**: len, None.rstrip, _GUARD_RE.match, new_lines.append, redsl.commands._guard_fixers._handle_guard

### redsl.commands.cli_autonomy._format_gate_details
> Format quality gate details as text.
- **Output to**: None.join, lines.append, lines.append, lines.append, verdict.metrics_before.get

### redsl.commands.cli_autonomy._format_gate_fix_result
> Format gate fix result as text.
- **Output to**: lines.append, lines.append, None.join, lines.append, len

### redsl.commands.cli_autonomy._format_improve_result
> Format improve cycle result as text.
- **Output to**: result.get, result.get, None.join, lines.append, lines.append

### redsl.commands.cli_autonomy._format_autonomy_status
> Format autonomy metrics as human-readable text.
- **Output to**: None.join, lines.append, lines.append

### redsl.commands.cli_autonomy._format_growth_report
> Format growth check result as text.
- **Output to**: None.join, lines.append, lines.append, lines.append, lines.append

### redsl.commands.cli_doctor._format_check_report
> Format doctor check report as text.
- **Output to**: None.join, lines.append, lines.append, lines.append

### redsl.commands.cli_doctor._format_heal_report
> Format doctor heal report as text.
- **Output to**: lines.append, None.join, lines.append, lines.append, lines.append

### redsl.commands.cli_doctor._format_batch_report
> Format doctor batch report as text.
- **Output to**: lines.append, None.join, len, len, len

### redsl.commands.hybrid._process_single_project
> Process a single project and return results.
- **Output to**: redsl.commands.hybrid._count_todo_issues, redsl.commands.hybrid.run_hybrid_quality_refactor, redsl.commands.hybrid._regenerate_todo, redsl.commands.hybrid._count_todo_issues, print

### examples.03-full-pipeline.refactor_output.refactor_extract_functions_20260407_145021.00_orders__service.process_order
> Funkcja z CC=25 i fan-out=10 — idealny kandydat do refaktoryzacji.
- **Output to**: examples.03-full-pipeline.refactor_output.refactor_extract_functions_20260407_145021.00_orders__service._is_order_terminal, examples.03-full-pipeline.refactor_output.refactor_extract_functions_20260407_145021.00_orders__service._calculate_order_total, shipping.calculate, examples.03-full-pipeline.refactor_output.refactor_extract_functions_20260407_145021.00_orders__service._finalize_order, examples.03-full-pipeline.refactor_output.refactor_extract_functions_20260407_145021.00_orders__service._validate_order_and_user

### examples.03-full-pipeline.refactor_output.refactor_extract_functions_20260407_145021.00_orders__service._validate_order_and_user
> Validate that order and user exist.
- **Output to**: logger.error, logger.error

### examples.03-full-pipeline.refactor_output.refactor_extract_functions_20260407_145021.00_orders__service._process_physical_item
> Process physical item inventory and pricing logic.
- **Output to**: inventory.check, logger.warning, inventory.backorder, ValueError

### redsl.commands.batch._process_batch_project
> Process a single project in the batch.
- **Output to**: print, print, print, redsl.commands.batch.measure_todo_reduction, print

### redsl.commands.batch_pyqual.runner._format_project_status
> Format project result status into readable parts.
- **Output to**: parts.extend, parts.extend, parts.extend, parts.append, None.join

### redsl.commands._indent_fixers._process_def_block
> Handle a def/class/try block: fix body indent or strip excess indent.
- **Output to**: new_lines.append, redsl.commands._indent_fixers._scan_next_nonblank, len, len, len

### redsl.commands.autofix.runner._format_project_status
> Format brief status line for a project result.
- **Output to**: None.join, status_parts.append, status_parts.append, status_parts.append, status_parts.append

### redsl.commands.pyqual.mypy_analyzer.MypyAnalyzer._parse_mypy_line
> Parsuj jedną linię wyjścia mypy.
- **Output to**: line.split, line.strip, len, int, None.strip

### redsl.commands.autofix.pipeline._process_project
> Full autofix pipeline for a single project.
- **Output to**: ProjectFixResult, redsl.commands.autofix.pipeline._stage_collect_metrics, redsl.commands.autofix.pipeline._stage_ensure_todo, redsl.commands.autofix.pipeline._stage_apply_fixes, redsl.commands.autofix.pipeline._stage_quality_gate_check

### redsl.commands.autonomy_pr.analyzer._parse_worktree_changes
> Parse `git status --porcelain` output into a list of file paths.
- **Output to**: status_output.splitlines, None.strip, len, paths.append

## Behavioral Patterns

### recursion__flatten_radon_blocks
- **Type**: recursion
- **Confidence**: 0.90
- **Functions**: redsl.analyzers.radon_analyzer._flatten_radon_blocks

### state_machine_DirectImportRefactorer
- **Type**: state_machine
- **Confidence**: 0.70
- **Functions**: redsl.refactors.direct_imports.DirectImportRefactorer.__init__, redsl.refactors.direct_imports.DirectImportRefactorer.remove_unused_imports, redsl.refactors.direct_imports.DirectImportRefactorer._collect_unused_import_edits, redsl.refactors.direct_imports.DirectImportRefactorer._collect_import_edits, redsl.refactors.direct_imports.DirectImportRefactorer._collect_import_from_edits

### state_machine_RefactorSandbox
- **Type**: state_machine
- **Confidence**: 0.70
- **Functions**: redsl.validation.sandbox.RefactorSandbox.__init__, redsl.validation.sandbox.RefactorSandbox.start, redsl.validation.sandbox.RefactorSandbox.apply_and_test, redsl.validation.sandbox.RefactorSandbox.stop, redsl.validation.sandbox.RefactorSandbox.__enter__

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `redsl.examples.memory_learning.run_memory_learning_example` - 78 calls
- `redsl.examples.audit.run_audit_example` - 69 calls
- `archive.legacy_scripts.batch_refactor_semcod.main` - 46 calls
- `redsl.examples.pyqual_example.run_pyqual_example` - 41 calls
- `redsl.examples.pr_bot.run_pr_bot_example` - 40 calls
- `archive.legacy_scripts.batch_quality_refactor.main` - 38 calls
- `redsl.examples.custom_rules.run_custom_rules_example` - 34 calls
- `redsl.examples.badge.run_badge_example` - 33 calls
- `redsl.analyzers.sumd_bridge.SumdAnalyzer.generate_map_toon` - 32 calls
- `redsl.examples.basic_analysis.run_basic_analysis_example` - 31 calls
- `redsl.commands.autonomy_pr.run_autonomous_pr` - 30 calls
- `archive.legacy_scripts.apply_semcod_refactor.main` - 29 calls
- `redsl.refactors.engine.RefactorEngine.generate_proposal` - 28 calls
- `redsl.examples.full_pipeline.run_full_pipeline_example` - 27 calls
- `redsl.analyzers.parsers.duplication_parser.DuplicationParser.parse_duplication_toon` - 27 calls
- `redsl.examples.api_integration.run_api_integration_example` - 26 calls
- `archive.legacy_scripts.debug_decisions.debug_decisions` - 25 calls
- `archive.legacy_scripts.batch_quality_refactor.apply_quality_refactors` - 25 calls
- `archive.legacy_scripts.debug_llm_config.debug_llm` - 24 calls
- `redsl.cli.refactor.refactor` - 24 calls
- `redsl.execution.cycle.run_cycle` - 23 calls
- `archive.legacy_scripts.hybrid_quality_refactor.apply_all_quality_changes` - 21 calls
- `redsl.awareness.AwarenessManager.build_snapshot` - 20 calls
- `redsl.validation.vallm_bridge.validate_proposal` - 20 calls
- `redsl.awareness.health_model.HealthModel.assess` - 20 calls
- `redsl.commands.pyqual.run_pyqual_fix` - 19 calls
- `redsl.autonomy.metrics.collect_autonomy_metrics` - 19 calls
- `redsl.formatters.batch.format_batch_results` - 19 calls
- `redsl.formatters.batch.format_batch_report_markdown` - 19 calls
- `redsl.refactors.body_restorer.repair_file` - 19 calls
- `redsl.analyzers.redup_bridge.scan_duplicates` - 19 calls
- `redsl.analyzers.toon_analyzer.ToonAnalyzer.analyze_from_toon_content` - 19 calls
- `redsl.cli.logging.setup_logging` - 19 calls
- `redsl.commands.planfile_bridge.create_ticket` - 18 calls
- `redsl.commands.doctor_detectors.detect_version_mismatch` - 18 calls
- `redsl.commands.batch_pyqual.runner.run_pyqual_batch` - 18 calls
- `redsl.history.HistoryReader.generate_decision_report` - 18 calls
- `redsl.cli.batch.batch_pyqual_run` - 18 calls
- `redsl.autonomy.growth_control.check_module_budget` - 18 calls
- `redsl.autonomy.scheduler.Scheduler.run` - 18 calls

## System Interactions

How components interact:

```mermaid
graph TD
    main --> Path
    main --> iterdir
    main --> print
    main --> sorted
    generate_map_toon --> analyze
    generate_map_toon --> isoformat
    generate_map_toon --> join
    generate_map_toon --> a
    main --> info
    main --> AgentConfig
    main --> RefactorOrchestrator
    generate_proposal --> get
    generate_proposal --> build_ecosystem_cont
    generate_proposal --> format
    generate_proposal --> call_json
    parse_duplication_to --> splitlines
    parse_duplication_to --> strip
    parse_duplication_to --> append
    parse_duplication_to --> search
    parse_duplication_to --> startswith
    debug_decisions --> print
    debug_decisions --> from_env
    debug_decisions --> RefactorOrchestrator
    debug_llm --> print
    refactor --> command
    refactor --> argument
    refactor --> option
    run_cycle --> _new_cycle_report
    run_cycle --> info
    run_cycle --> _analyze_project
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.