"""Cycle reflection helpers for the refactoring orchestrator."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redsl.orchestrator import CycleReport, RefactorOrchestrator

logger = logging.getLogger(__name__)


def _reflect_on_cycle(orchestrator: "RefactorOrchestrator", report: "CycleReport") -> None:
    """Reflect on an entire refactoring cycle and store the insight in memory."""
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
        reflection = orchestrator.llm.call([
            {"role": "system", "content": orchestrator.config.identity},
            {"role": "user", "content": reflection_prompt},
        ])

        orchestrator.history.record_event(
            "cycle_reflection",
            cycle_number=report.cycle_number,
            details={
                "decisions_count": report.decisions_count,
                "proposals_generated": report.proposals_generated,
                "proposals_applied": report.proposals_applied,
                "proposals_rejected": report.proposals_rejected,
                "reflection": reflection.content,
                "errors": report.errors[:5],
            },
        )

        orchestrator.memory.store_strategy(
            strategy_name=f"cycle_{report.cycle_number}_reflection",
            steps=[
                f"Success rate: {success_rate:.0%}",
                f"Key insight: {reflection.content[:200]}",
            ],
            tags=["meta-reflection", f"cycle-{report.cycle_number}"],
        )

        orchestrator.history.record_event(
            "cycle_reflection",
            cycle_number=report.cycle_number,
            thought=(
                f"Success rate: {success_rate:.0%}, "
                f"generated={report.proposals_generated}, applied={report.proposals_applied}, "
                f"rejected={report.proposals_rejected}, errors={len(report.errors)}"
            ),
            reflection=reflection.content[:2000],
        )

        logger.info("Cycle reflection: %s", reflection.content[:200])

    except Exception as e:
        logger.warning("Reflection failed: %s", e)

    _auto_learn_rules(orchestrator, report)


def _auto_learn_rules(orchestrator: "RefactorOrchestrator", report: "CycleReport") -> None:
    """Learn simple DSL rules from successful cycles."""
    if report.proposals_applied == 0:
        return

    try:
        rules = orchestrator._rule_gen.generate(min_support=3)
        if rules:
            learned_path = Path("config") / "learned_rules.yaml"
            learned_path.parent.mkdir(parents=True, exist_ok=True)
            orchestrator._rule_gen.save(rules, learned_path)
            registered = orchestrator._rule_gen.load_and_register(learned_path, orchestrator.dsl_engine)
            if registered:
                logger.info("Auto-learned %d new DSL rules", registered)
                orchestrator.history.record_event(
                    "rules_auto_learned",
                    cycle_number=report.cycle_number,
                    thought=f"Auto-learned {registered} new DSL rules from successful patterns",
                    details={"rules_count": registered},
                )
    except Exception as e:
        logger.debug("Auto-learn rules failed (non-critical): %s", e)
