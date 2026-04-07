"""
Orkiestrator — „pętla świadomości" agenta refaktoryzacji.

Realizuje cykl:
    PERCEIVE → DECIDE → PLAN → EXECUTE → REFLECT → REMEMBER → IMPROVE

Każdy cykl:
1. Analizuje projekt (toon.yaml, metryki)
2. Ewaluuje reguły DSL → lista decyzji
3. Konsultuje pamięć (czy robiliśmy coś podobnego?)
4. Generuje plan zmian przez LLM
5. Reflektuje (self-critique)
6. Waliduje i (opcjonalnie) aplikuje
7. Zapisuje doświadczenie do pamięci
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from redsl.analyzers import AnalysisResult, CodeAnalyzer
from redsl.analyzers import code2llm_bridge
from redsl.config import AgentConfig
from redsl.dsl import Decision, DSLEngine, RefactorAction
from redsl.llm import LLMLayer
from redsl.memory import AgentMemory
from redsl.refactors import RefactorEngine, RefactorProposal, RefactorResult
from redsl.refactors.direct import DirectRefactorEngine
from redsl.validation import regix_bridge

logger = logging.getLogger(__name__)


@dataclass
class CycleReport:
    """Raport z jednego cyklu refaktoryzacji."""

    cycle_number: int
    analysis_summary: str
    decisions_count: int
    proposals_generated: int
    proposals_applied: int
    proposals_rejected: int
    errors: list[str] = field(default_factory=list)
    results: list[RefactorResult] = field(default_factory=list)


class RefactorOrchestrator:
    """
    Główny orkiestrator — „mózg" systemu.

    Łączy:
    - CodeAnalyzer (percepcja)
    - DSLEngine (decyzje)
    - RefactorEngine (akcja)
    - LLMLayer (myślenie + refleksja)
    - AgentMemory (pamięć)
    """

    def __init__(self, config: AgentConfig | None = None) -> None:
        self.config = config or AgentConfig.from_env()
        self.analyzer = CodeAnalyzer()
        self.dsl_engine = DSLEngine()
        self.llm = LLMLayer(self.config.llm)
        self.memory = AgentMemory(self.config.memory.persist_dir)
        self.refactor_engine = RefactorEngine(self.llm, self.config.refactor)
        self.direct_refactor = DirectRefactorEngine()
        self._cycle_count = 0

    # ------------------------------------------------------------------
    # Główna pętla
    # ------------------------------------------------------------------

    def run_cycle(
        self,
        project_dir: Path,
        max_actions: int = 5,
        use_code2llm: bool = False,
        validate_regix: bool = False,
        rollback_on_regression: bool = False,
    ) -> CycleReport:
        """
        Jeden pełny cykl refaktoryzacji.

        1. PERCEIVE: analiza projektu
        2. DECIDE: ewaluacja reguł DSL
        3. PLAN + EXECUTE: generowanie i aplikowanie zmian
        4. REFLECT + REMEMBER: samoocena i zapis do pamięci
        """
        self._cycle_count += 1
        report = CycleReport(
            cycle_number=self._cycle_count,
            analysis_summary="",
            decisions_count=0,
            proposals_generated=0,
            proposals_applied=0,
            proposals_rejected=0,
        )

        try:
            # == PERCEIVE ==
            logger.info("=== CYCLE %d: PERCEIVE ===", self._cycle_count)
            if use_code2llm:
                analysis = code2llm_bridge.maybe_analyze(project_dir, self.analyzer) \
                    or self.analyzer.analyze_project(project_dir)
            else:
                analysis = self.analyzer.analyze_project(project_dir)
            report.analysis_summary = (
                f"{analysis.total_files} files, {analysis.total_lines} lines, "
                f"avg CC={analysis.avg_cc:.1f}, {analysis.critical_count} critical"
            )

            # == DECIDE ==
            logger.info("=== CYCLE %d: DECIDE ===", self._cycle_count)
            contexts = analysis.to_dsl_contexts()
            decisions = self.dsl_engine.top_decisions(contexts, limit=max_actions)
            report.decisions_count = len(decisions)

            if not decisions:
                logger.info("No refactoring decisions — code looks good!")
                return report

            # Regix snapshot PRZED zmianami (working tree baseline)
            regix_before: dict | None = None
            if validate_regix:
                regix_before = regix_bridge.snapshot(project_dir, ref="HEAD")
                if regix_before:
                    logger.info("regix: snapshot taken before cycle")

            # Konsultuj pamięć — czy robiliśmy coś podobnego?
            for decision in decisions:
                similar = self.memory.recall_similar_actions(
                    f"{decision.action.value} {decision.target_file}",
                    limit=3,
                )
                if similar:
                    logger.info(
                        "Memory: found %d similar past actions for %s",
                        len(similar), decision.target_file,
                    )

            # == PLAN + EXECUTE ==
            logger.info("=== CYCLE %d: PLAN + EXECUTE ===", self._cycle_count)
            for decision in decisions:
                if not decision.should_execute:
                    continue

                try:
                    result = self._execute_decision(decision, project_dir)
                    report.results.append(result)

                    if result.applied or result.validated:
                        report.proposals_generated += 1
                        if result.applied:
                            report.proposals_applied += 1
                    else:
                        report.proposals_rejected += 1
                        report.errors.extend(result.errors)

                except Exception as e:
                    logger.error("Failed to execute decision %s: %s", decision.rule_name, e)
                    report.errors.append(f"{decision.rule_name}: {e}")

            # == VALIDATE (regix regression check) ==
            if validate_regix and report.proposals_applied > 0:
                logger.info("=== CYCLE %d: VALIDATE (regix) ===", self._cycle_count)
                self._validate_with_regix(project_dir, regix_before, rollback_on_regression, report)

            # == REFLECT (na poziomie cyklu) ==
            logger.info("=== CYCLE %d: REFLECT ===", self._cycle_count)
            self._reflect_on_cycle(report)

        except Exception as e:
            logger.error("Cycle %d failed: %s", self._cycle_count, e)
            report.errors.append(str(e))

        return report

    def run_from_toon_content(
        self,
        project_toon: str = "",
        duplication_toon: str = "",
        validation_toon: str = "",
        source_files: dict[str, str] | None = None,
        max_actions: int = 5,
    ) -> CycleReport:
        """
        Uruchom cykl z bezpośredniego contentu toon (bez plików na dysku).
        Przydatne do integracji z API.
        """
        self._cycle_count += 1
        report = CycleReport(
            cycle_number=self._cycle_count,
            analysis_summary="",
            decisions_count=0,
            proposals_generated=0,
            proposals_applied=0,
            proposals_rejected=0,
        )

        # PERCEIVE
        analysis = self.analyzer.analyze_from_toon_content(
            project_toon=project_toon,
            duplication_toon=duplication_toon,
            validation_toon=validation_toon,
        )
        report.analysis_summary = (
            f"{analysis.total_files} files, {analysis.total_lines} lines"
        )

        # DECIDE
        contexts = analysis.to_dsl_contexts()
        decisions = self.dsl_engine.top_decisions(contexts, limit=max_actions)
        report.decisions_count = len(decisions)

        # PLAN
        for decision in decisions:
            if not decision.should_execute:
                continue

            source = (source_files or {}).get(decision.target_file, "# source not provided")

            try:
                proposal = self.refactor_engine.generate_proposal(decision, source)
                proposal = self.refactor_engine.reflect_on_proposal(proposal, source)
                result = self.refactor_engine.validate_proposal(proposal)
                report.results.append(result)
                report.proposals_generated += 1

                if result.validated:
                    # Zapisz propozycję (dry run)
                    self.refactor_engine._save_proposal(proposal)

            except Exception as e:
                logger.error("Failed: %s", e)
                report.errors.append(str(e))

        # REFLECT
        self._reflect_on_cycle(report)

        return report

    # ------------------------------------------------------------------
    # Wewnętrzne metody
    # ------------------------------------------------------------------

    def _execute_decision(
        self,
        decision: Decision,
        project_dir: Path,
    ) -> RefactorResult:
        """Wykonaj pojedynczą decyzję refaktoryzacji."""
        logger.info(
            "Executing: %s on %s (score=%.2f)",
            decision.action.value, decision.target_file, decision.score,
        )

        if decision.action in [
            RefactorAction.REMOVE_UNUSED_IMPORTS,
            RefactorAction.FIX_MODULE_EXECUTION_BLOCK,
            RefactorAction.EXTRACT_CONSTANTS,
            RefactorAction.ADD_RETURN_TYPES,
        ]:
            return self._execute_direct_refactor(decision, project_dir)

        source_path = self._resolve_source_path(decision, project_dir)
        source_code = self._load_source_code(source_path, decision)

        self._consult_memory(decision)

        proposal = self.refactor_engine.generate_proposal(decision, source_code)
        if self.config.refactor.reflection_rounds > 0:
            proposal = self.refactor_engine.reflect_on_proposal(proposal, source_code)

        result = self.refactor_engine.apply_proposal(proposal, project_dir)
        self._remember_decision_result(decision, proposal, result)
        return result

    def _resolve_source_path(self, decision: Decision, project_dir: Path) -> Path:
        """Rozwiąż ścieżkę do pliku źródłowego — fallback przez resolve_file_path."""
        source_path = project_dir / decision.target_file
        if not source_path.exists() and decision.target_function:
            resolved = self.analyzer.resolve_file_path(project_dir, decision.target_function)
            if resolved:
                source_path = project_dir / resolved
                logger.info("Resolved missing path %r → %s", decision.target_file, resolved)
        if not source_path.exists():
            resolved_mod = self.analyzer.resolve_file_path(project_dir, decision.target_file)
            if resolved_mod:
                source_path = project_dir / resolved_mod
        return source_path

    def _load_source_code(self, source_path: Path, decision: Decision) -> str:
        """Wczytaj kod źródłowy — wycinaj funkcję jeśli możliwe."""
        if not source_path.exists():
            logger.warning("Source file not found: %s", source_path)
            return f"# File not found: {decision.target_file}"

        func_name = self._resolve_target_function(source_path, decision)
        if func_name:
            func_src = self.analyzer.extract_function_source(source_path, func_name)
            if func_src:
                logger.info("Extracted function %r (%d chars)", func_name, len(func_src))
                return func_src
        return source_path.read_text(encoding="utf-8")

    def _resolve_target_function(self, source_path: Path, decision: Decision) -> str | None:
        """Ustal funkcję docelową — podaną lub auto-wykrytą (najwyższe CC)."""
        func_name = decision.target_function
        if not func_name and decision.context.get("cyclomatic_complexity", 0) > 15:
            worst = self.analyzer.find_worst_function(source_path)
            if worst:
                func_name = worst[0]
                logger.info(
                    "Auto-detected worst function in %s: %r (CC=%d)",
                    decision.target_file, func_name, worst[1],
                )
        return func_name

    def _consult_memory(self, decision: Decision) -> None:
        """Konsultuj pamięć — szukaj strategii dla podobnych akcji."""
        strategies = self.memory.recall_strategies(
            f"{decision.action.value} {decision.context.get('cyclomatic_complexity', 0)}",
            limit=2,
        )
        if strategies:
            logger.info("Found %d relevant strategies in memory", len(strategies))

    def _remember_decision_result(
        self, decision: Decision, proposal: RefactorProposal, result: RefactorResult
    ) -> None:
        """Zapisz doświadczenie do pamięci i ucz się wzorców."""
        self.memory.remember_action(
            action=decision.action.value,
            target=f"{decision.target_file}:{decision.target_function or 'module'}",
            result=proposal.summary,
            success=result.validated and len(result.errors) == 0,
            details={
                "confidence": proposal.confidence,
                "score": decision.score,
                "rule": decision.rule_name,
            },
        )
        if result.validated and proposal.confidence > 0.7:
            self.memory.learn_pattern(
                pattern=f"{decision.action.value} for CC={decision.context.get('cyclomatic_complexity', 0)}",
                context=f"{decision.target_file} — {proposal.summary}",
                effectiveness=proposal.confidence,
            )

    def _validate_with_regix(
        self,
        project_dir: Path,
        before_snapshot: dict | None,
        rollback_on_regression: bool,
        report: CycleReport,
    ) -> None:
        """Uruchom walidację regix po cyklu i zaktualizuj raport."""
        passed, regix_report = regix_bridge.validate_working_tree(
            project_dir,
            before_snapshot=before_snapshot,
            rollback_on_failure=rollback_on_regression,
        )
        if not passed:
            regressions = regix_report.get("regressions", [])
            report.errors.append(
                f"regix: regression detected — {len(regressions)} metric(s) degraded"
            )
            if rollback_on_regression:
                report.errors.append("regix: changes rolled back")
                report.proposals_applied = 0
        else:
            logger.info("regix: no regressions detected")

        gates = regix_bridge.check_gates(project_dir)
        if gates and not gates["passed"]:
            for failure in gates.get("failures", []):
                logger.warning("regix gate failure: %s", failure)

    def _execute_direct_refactor(
        self,
        decision: Decision,
        project_dir: Path,
    ) -> RefactorResult:
        """Execute simple refactorings directly without LLM."""
        source_path = project_dir / decision.target_file
        
        if not source_path.exists():
            return RefactorResult(
                proposal=None,
                applied=False,
                validated=False,
                errors=[f"File not found: {source_path}"],
            )
        
        success = False
        errors = []
        
        try:
            if decision.action == RefactorAction.REMOVE_UNUSED_IMPORTS:
                # Get unused imports from context
                unused_imports = decision.context.get("unused_import_list", [])
                success = self.direct_refactor.remove_unused_imports(source_path, unused_imports)
                
            elif decision.action == RefactorAction.FIX_MODULE_EXECUTION_BLOCK:
                success = self.direct_refactor.fix_module_execution_block(source_path)
                
            elif decision.action == RefactorAction.EXTRACT_CONSTANTS:
                # Get magic numbers from context
                magic_numbers = decision.context.get("magic_number_list", [])
                success = self.direct_refactor.extract_constants(source_path, magic_numbers)
                
            elif decision.action == RefactorAction.ADD_RETURN_TYPES:
                # Get functions missing return types from context
                functions_missing_return = decision.context.get("functions_missing_return", [])
                success = self.direct_refactor.add_return_types(source_path, functions_missing_return)
            
            if success:
                # Remember the action
                self.memory.remember_action(
                    action=decision.action.value,
                    target=str(source_path),
                    result=f"Direct refactor applied: {decision.action.value}",
                    success=True,
                    details={"score": decision.score, "rule": decision.rule_name},
                )
                
                return RefactorResult(
                    proposal=None,
                    applied=True,
                    validated=True,
                    errors=[],
                )
            else:
                errors.append(f"Direct refactor failed: {decision.action.value}")
                
        except Exception as e:
            errors.append(str(e))
            logger.error(f"Direct refactor error: {e}")
        
        return RefactorResult(
            proposal=None,
            applied=False,
            validated=False,
            errors=errors,
        )

    def _reflect_on_cycle(self, report: CycleReport) -> None:
        """Refleksja na poziomie całego cyklu — meta-myślenie."""
        if report.proposals_generated == 0:
            return

        success_rate = (
            report.proposals_applied / report.proposals_generated
            if report.proposals_generated > 0
            else 0
        )

        reflection_prompt = (
            f"Cycle {report.cycle_number} results:\n"
            f"- Decisions evaluated: {report.decisions_count}\n"
            f"- Proposals generated: {report.proposals_generated}\n"
            f"- Applied: {report.proposals_applied}\n"
            f"- Rejected: {report.proposals_rejected}\n"
            f"- Errors: {len(report.errors)}\n"
            f"- Success rate: {success_rate:.0%}\n\n"
            f"Errors: {'; '.join(report.errors[:5])}\n\n"
            f"What should I improve in my refactoring strategy?"
        )

        try:
            reflection = self.llm.call([
                {"role": "system", "content": self.config.identity},
                {"role": "user", "content": reflection_prompt},
            ])

            # Zapamiętaj refleksję jako strategię
            self.memory.store_strategy(
                strategy_name=f"cycle_{report.cycle_number}_reflection",
                steps=[
                    f"Success rate: {success_rate:.0%}",
                    f"Key insight: {reflection.content[:200]}",
                ],
                tags=["meta-reflection", f"cycle-{report.cycle_number}"],
            )

            logger.info("Cycle reflection: %s", reflection.content[:200])

        except Exception as e:
            logger.warning("Reflection failed: %s", e)

    # ------------------------------------------------------------------
    # Publiczne API
    # ------------------------------------------------------------------

    def explain_decisions(self, project_dir: Path, limit: int = 10) -> str:
        """Wyjaśnij decyzje refaktoryzacji bez ich wykonywania."""
        from redsl.refactors import RefactorEngine

        analysis = self.analyzer.analyze_project(project_dir)
        contexts = analysis.to_dsl_contexts()
        decisions = self.dsl_engine.top_decisions(contexts, limit=limit)

        if not decisions:
            return "Brak decyzji refaktoryzacji — kod wygląda dobrze."

        lines = [f"Top {len(decisions)} decyzji refaktoryzacji:\n"]
        for i, d in enumerate(decisions, 1):
            confidence = RefactorEngine.estimate_confidence(d)
            lines.append(f"{i}. {self.dsl_engine.explain(d)}")
            lines.append(f"Confidence (metric): {confidence:.2f}")

            # Podgląd kodu źródłowego
            src_path = project_dir / d.target_file
            if not src_path.exists() and d.target_function:
                resolved = self.analyzer.resolve_file_path(project_dir, d.target_function)
                if resolved:
                    src_path = project_dir / resolved
            if src_path.exists():
                func = d.target_function
                if not func:
                    worst = self.analyzer.find_worst_function(src_path)
                    func = worst[0] if worst else None
                if func:
                    src = self.analyzer.extract_function_source(src_path, func)
                    preview = src[:400].rstrip()
                    if len(src) > 400:
                        preview += f"\n    ... (+{len(src)-400} chars)"
                    lines.append(f"Źródło ({src_path.name}::{func}):\n{preview}")
            lines.append("")

        return "\n".join(lines)

    def get_memory_stats(self) -> dict[str, Any]:
        """Statystyki pamięci agenta."""
        return {
            "memory": self.memory.stats(),
            "total_cycles": self._cycle_count,
            "total_llm_calls": self.llm.total_calls,
        }

    def add_custom_rules(self, rules_yaml: list[dict]) -> None:
        """Dodaj niestandardowe reguły DSL."""
        self.dsl_engine.add_rules_from_yaml(rules_yaml)
