"""Adaptive executor — adapts strategy at runtime based on failure patterns.

When an action type fails twice in the same session the executor:
  1. Skips further attempts of that type
  2. Records the pattern to memory
  3. Falls back to an alternative action
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from redsl.orchestrator import RefactorOrchestrator
    from redsl.dsl.engine import Decision

logger = logging.getLogger(__name__)

_FALLBACK_ACTIONS: dict[str, str] = {
    "extract_functions": "simplify_conditionals",
    "split_module": "reduce_fan_out",
    "deduplicate": "extract_functions",
}

_MAX_FAILURES = 2


class AdaptiveExecutor:
    """Execute decisions while adapting strategy on repeated failures."""

    def __init__(self, orchestrator: RefactorOrchestrator) -> None:
        self.orch = orchestrator
        self._session_failures: dict[str, int] = {}

    def execute_adaptive(
        self,
        decisions: list[Decision],
        project_dir: Path,
        max_actions: int = 5,
    ) -> list[Any]:
        """Execute decisions with runtime adaptation.

        Takes up to ``2 * max_actions`` candidates so it can skip failing
        action types and still hit the target.
        """
        project_dir = Path(project_dir).resolve()
        results: list[Any] = []

        for decision in decisions[: max_actions * 2]:
            if len(results) >= max_actions:
                break

            action = decision.action.value
            if self._session_failures.get(action, 0) >= _MAX_FAILURES:
                logger.info("Skipping %s — failed %dx this session", action, _MAX_FAILURES)
                continue

            from redsl.execution import _execute_decision

            result = _execute_decision(self.orch, decision, project_dir)
            applied = getattr(result, "applied", False)
            validated = getattr(result, "validated", True)

            if applied and validated:
                results.append(result)
                self._session_failures[action] = 0
            else:
                count = self._session_failures.get(action, 0) + 1
                self._session_failures[action] = count
                errors = getattr(result, "errors", [])
                logger.info("Action %s failed (%d/%d). Errors: %s", action, count, _MAX_FAILURES, errors[:2])

                if count >= _MAX_FAILURES:
                    self._adapt_strategy(action, errors)

        return results

    def _adapt_strategy(self, failed_action: str, errors: list[str]) -> None:
        """Record the failure pattern and suggest a fallback."""
        try:
            self.orch.memory.learn_pattern(
                pattern=f"session_failure:{failed_action}",
                context=f"Failed {_MAX_FAILURES}x in this session. Errors: {errors[:2]}",
                effectiveness=0.0,
            )
        except Exception:
            pass

        fallback = _FALLBACK_ACTIONS.get(failed_action)
        if fallback:
            logger.info("Fallback: %s -> %s", failed_action, fallback)
            try:
                self.orch.memory.store_strategy(
                    strategy_name=f"fallback_{failed_action}",
                    steps=[f"When {failed_action} fails, try {fallback} instead"],
                    tags=["adaptive", "fallback"],
                )
            except Exception:
                pass

    @property
    def session_failures(self) -> dict[str, int]:
        """Expose failure counts for inspection / testing."""
        return dict(self._session_failures)
