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

import logging
from dataclasses import dataclass, field
from pathlib import Path

from redsl.analyzers import CodeAnalyzer, SemanticChunker
from redsl.config import AgentConfig
from redsl.awareness import AwarenessManager, SelfModel
from redsl.dsl import DSLEngine, RuleGenerator
from redsl.execution import (
    _execute_decision,
    _execute_direct_refactor,
    _new_cycle_report,
    _reflect_on_cycle,
    estimate_cycle_cost,
    explain_decisions,
    get_memory_stats,
    run_cycle as _run_cycle,
    run_from_toon_content as _run_from_toon_content,
    execute_sandboxed,
)
from redsl.history import HistoryWriter
from redsl.llm import LLMLayer
from redsl.memory import AgentMemory
from redsl.refactors import RefactorEngine, RefactorResult
from redsl.refactors.direct import DirectRefactorEngine

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
        self.history = HistoryWriter(Path(self.config.refactor.output_dir).parent)
        self.self_model = SelfModel(self.memory)
        self.awareness_manager = AwarenessManager(
            memory=self.memory,
            analyzer=self.analyzer,
            default_depth=20,
        )
        self.refactor_engine = RefactorEngine(self.llm, self.config.refactor)
        self.direct_refactor = DirectRefactorEngine()
        self._chunker = SemanticChunker()
        self._rule_gen = RuleGenerator(self.memory)
        self._cycle_count = 0
        self._total_llm_cost: float = 0.0

    def run_cycle(
        self,
        project_dir: Path,
        max_actions: int = 5,
        use_code2llm: bool = False,
        validate_regix: bool = False,
        rollback_on_failure: bool = False,
        use_sandbox: bool = False,
    ) -> CycleReport:
        effective_max = self._resolve_limits(project_dir, max_actions)
        return _run_cycle(
            self,
            project_dir,
            max_actions=effective_max,
            use_code2llm=use_code2llm,
            validate_regix=validate_regix,
            rollback_on_failure=rollback_on_failure,
            use_sandbox=use_sandbox,
        )

    def run_from_toon_content(
        self,
        project_toon: str = "",
        duplication_toon: str = "",
        validation_toon: str = "",
        source_files: dict[str, str] | None = None,
        max_actions: int = 5,
    ) -> CycleReport:
        return _run_from_toon_content(
            self,
            project_toon=project_toon,
            duplication_toon=duplication_toon,
            validation_toon=validation_toon,
            source_files=source_files,
            max_actions=max_actions,
        )

    def add_custom_rules(self, rules_yaml: list[dict]) -> None:
        """Dodaj niestandardowe reguły DSL."""
        self.dsl_engine.add_rules_from_yaml(rules_yaml)

    @staticmethod
    def _resolve_limits(project_dir: Path, default_max: int) -> int:
        """Read max_actions from planfile.yaml strategy limits if available."""
        planfile_path = Path(project_dir) / "planfile.yaml"
        if not planfile_path.exists():
            return default_max
        try:
            import yaml
            data = yaml.safe_load(planfile_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return default_max
            limits = data.get("limits") or {}
            if not isinstance(limits, dict):
                return default_max
            max_actions = limits.get("max_actions") or limits.get("max_tickets")
            if max_actions is not None:
                resolved = int(max_actions)
                logger.info("planfile.yaml limits: max_actions=%d (was %d)", resolved, default_max)
                return resolved
        except Exception as exc:
            logger.debug("Could not read planfile.yaml limits: %s", exc)
        return default_max


# Backward-compatible shims: keep the long-standing orchestrator method API
# while the actual implementation lives in redsl.execution.* modules.
RefactorOrchestrator._new_cycle_report = _new_cycle_report  # type: ignore[attr-defined]
RefactorOrchestrator._execute_decision = _execute_decision  # type: ignore[attr-defined]
RefactorOrchestrator._execute_direct_refactor = _execute_direct_refactor  # type: ignore[attr-defined]
RefactorOrchestrator._reflect_on_cycle = _reflect_on_cycle  # type: ignore[attr-defined]
RefactorOrchestrator.execute_sandboxed = execute_sandboxed  # type: ignore[attr-defined]
RefactorOrchestrator.explain_decisions = explain_decisions  # type: ignore[attr-defined]
RefactorOrchestrator.get_memory_stats = get_memory_stats  # type: ignore[attr-defined]
RefactorOrchestrator.estimate_cycle_cost = estimate_cycle_cost  # type: ignore[attr-defined]
