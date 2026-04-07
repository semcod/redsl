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

from app.analyzers import AnalysisResult, CodeAnalyzer
from app.config import AgentConfig
from app.dsl import Decision, DSLEngine
from app.llm import LLMLayer
from app.memory import AgentMemory
from app.refactors import RefactorEngine, RefactorProposal, RefactorResult

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
        self._cycle_count = 0

    # ------------------------------------------------------------------
    # Główna pętla
    # ------------------------------------------------------------------

    def run_cycle(
        self,
        project_dir: Path,
        max_actions: int = 5,
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

        # Wczytaj kod źródłowy
        source_path = project_dir / decision.target_file
        if source_path.exists():
            source_code = source_path.read_text(encoding="utf-8")
        else:
            source_code = f"# File not found: {decision.target_file}"
            logger.warning("Source file not found: %s", source_path)

        # Konsultuj pamięć — szukaj strategii
        strategies = self.memory.recall_strategies(
            f"{decision.action.value} {decision.context.get('cyclomatic_complexity', 0)}",
            limit=2,
        )
        if strategies:
            logger.info("Found %d relevant strategies in memory", len(strategies))

        # Generuj propozycję
        proposal = self.refactor_engine.generate_proposal(decision, source_code)

        # Refleksja (self-critique)
        if self.config.refactor.reflection_rounds > 0:
            proposal = self.refactor_engine.reflect_on_proposal(proposal, source_code)

        # Walidacja i aplikacja
        result = self.refactor_engine.apply_proposal(proposal, project_dir)

        # REMEMBER — zapisz doświadczenie
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

        # Jeśli sukces — zapisz wzorzec
        if result.validated and proposal.confidence > 0.7:
            self.memory.learn_pattern(
                pattern=f"{decision.action.value} for CC={decision.context.get('cyclomatic_complexity', 0)}",
                context=f"{decision.target_file} — {proposal.summary}",
                effectiveness=proposal.confidence,
            )

        return result

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
        analysis = self.analyzer.analyze_project(project_dir)
        contexts = analysis.to_dsl_contexts()
        decisions = self.dsl_engine.top_decisions(contexts, limit=limit)

        if not decisions:
            return "Brak decyzji refaktoryzacji — kod wygląda dobrze."

        lines = [f"Top {len(decisions)} decyzji refaktoryzacji:\n"]
        for i, d in enumerate(decisions, 1):
            lines.append(f"{i}. {self.dsl_engine.explain(d)}\n")

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
