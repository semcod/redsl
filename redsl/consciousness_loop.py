"""
Pętla ciągłej egzystencji agenta — „background consciousness loop".

Agent:
1. Cyklicznie analizuje projekt
2. Podejmuje decyzje
3. Generuje propozycje
4. Reflektuje nad swoimi działaniami
5. Uczy się z doświadczeń
6. Sam inicjuje myśli i plany

Uruchomienie:
    python -m app.consciousness_loop --project ./my-project --interval 60
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from redsl.config import AgentConfig
from redsl.execution import get_memory_stats
from redsl.orchestrator import RefactorOrchestrator

logger = logging.getLogger(__name__)


class ConsciousnessLoop:
    """
    Ciągła pętla „świadomości" agenta.

    Agent nie czeka na polecenia — sam analizuje, myśli i planuje.
    """

    def __init__(
        self,
        project_dir: Path,
        interval_seconds: int = 60,
        config: AgentConfig | None = None,
    ) -> None:
        self.project_dir = project_dir
        self.interval = interval_seconds
        self.orchestrator = RefactorOrchestrator(config or AgentConfig.from_env())
        self._running = False
        self._thoughts: list[str] = []
        self._max_actions: int = 3

    async def run(self) -> None:
        """Główna pętla — działa w tle, cyklicznie."""
        self._running = True
        logger.info(
            "Consciousness loop started: project=%s, interval=%ds",
            self.project_dir, self.interval,
        )

        cycle = 0
        while self._running:
            cycle += 1
            now = datetime.now(timezone.utc).isoformat()

            try:
                # == INNER THOUGHT ==
                logger.info("[Cycle %d] Generating inner thought...", cycle)
                thought = await self._inner_thought(cycle)
                self._thoughts.append(thought)

                # == PERFORMANCE PROFILING (every 10 cycles) ==
                if cycle % 10 == 0:
                    await self._profile_performance(cycle)

                # == REFACTOR CYCLE ==
                logger.info("[Cycle %d] Running refactor cycle...", cycle)
                report = self.orchestrator.run_cycle(
                    self.project_dir,
                    max_actions=self._max_actions,
                )

                logger.info(
                    "[Cycle %d] Result: %d decisions, %d applied, %d errors",
                    cycle, report.decisions_count,
                    report.proposals_applied, len(report.errors),
                )

                # == SELF-ASSESSMENT ==
                if cycle % 5 == 0:
                    await self._self_assessment(cycle)

            except Exception as e:
                logger.error("[Cycle %d] Error: %s", cycle, e)

            await asyncio.sleep(self.interval)

    async def _inner_thought(self, cycle: int) -> str:
        """Agent generuje wewnętrzną myśl — „co powinienem teraz zrobić?"."""
        past_actions = self.orchestrator.memory.recall_similar_actions(
            "recent refactoring actions", limit=5
        )
        context = "\n".join(e.content for e in past_actions) if past_actions else "No past actions."

        memory_stats = get_memory_stats(self.orchestrator)

        response = self.orchestrator.llm.call([
            {"role": "system", "content": self.orchestrator.config.identity},
            {"role": "user", "content": (
                f"Cycle: {cycle}\n"
                f"Memory stats: {memory_stats}\n"
                f"Recent actions:\n{context}\n\n"
                f"What should I focus on next? What patterns am I noticing? "
                f"What could I improve in my approach?"
            )},
        ])

        thought = response.content
        logger.info("[Inner thought] %s", thought[:200])

        # Zapisz myśl do pamięci
        self.orchestrator.memory.store_strategy(
            strategy_name=f"inner_thought_cycle_{cycle}",
            steps=[thought[:500]],
            tags=["inner-thought", f"cycle-{cycle}"],
        )

        return thought

    async def _self_assessment(self, cycle: int) -> None:
        """Co 5 cykli — głębsza autoewaluacja."""
        strategies = self.orchestrator.memory.recall_strategies(
            "effectiveness improvement learning", limit=10
        )
        context = "\n".join(e.content for e in strategies) if strategies else "No strategies yet."

        response = self.orchestrator.llm.call([
            {"role": "system", "content": (
                "You are evaluating your own performance as a refactoring agent. "
                "Be honest about your strengths and weaknesses."
            )},
            {"role": "user", "content": (
                f"After {cycle} cycles, review your performance:\n"
                f"Past strategies and insights:\n{context}\n\n"
                f"1. What am I doing well?\n"
                f"2. What am I doing poorly?\n"
                f"3. What new strategy should I try?"
            )},
        ])

        logger.info("[Self-assessment] %s", response.content[:300])

        self.orchestrator.memory.learn_pattern(
            pattern="self-assessment",
            context=response.content[:500],
            effectiveness=0.5,  # Will be updated based on future results
        )

    async def _profile_performance(self, cycle: int) -> None:
        """Co 10 cykli — zmierz performance i zapisz do pamięci. Skaluj max_actions."""
        try:
            from redsl.diagnostics.perf_bridge import generate_optimization_report, profile_refactor_cycle
            perf = profile_refactor_cycle(self.project_dir)
            perf_report = generate_optimization_report(self.project_dir)
            logger.info("[Perf cycle %d] %s", cycle, perf_report[:300])

            self.orchestrator.memory.store_strategy(
                strategy_name=f"perf_cycle_{cycle}",
                steps=[perf_report],
                tags=["performance", "diagnostic"],
            )

            if perf.total_time_ms > 60_000:
                self._max_actions = max(1, self._max_actions - 1)
                logger.warning(
                    "[Perf cycle %d] Cycle too slow (%.0fms) — reducing max_actions to %d",
                    cycle, perf.total_time_ms, self._max_actions,
                )
        except Exception as exc:
            logger.debug("[Perf cycle %d] Profiling failed (non-critical): %s", cycle, exc)

    def stop(self) -> None:
        """Zatrzymaj pętlę."""
        self._running = False
        logger.info("Consciousness loop stopping...")


async def main_loop():
    """Punkt wejścia dla pętli ciągłej."""
    project_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    interval = int(sys.argv[4]) if len(sys.argv) > 4 else 60

    loop = ConsciousnessLoop(
        project_dir=Path(project_dir),
        interval_seconds=interval,
    )

    try:
        await loop.run()
    except KeyboardInterrupt:
        loop.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main_loop())
