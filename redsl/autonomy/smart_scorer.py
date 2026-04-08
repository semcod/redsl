"""Smart scorer — multi-dimensional decision scoring.

Extends the base Rule.score() with four additional dimensions:
  1. Trend    — is the file getting worse over time?
  2. Ecosystem — how many projects depend on this file?
  3. Coupling  — how many modules import it (fan-in)?
  4. Confidence — can we actually fix this type of issue?
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from redsl.awareness.git_timeline import GitTimelineAnalyzer
    from redsl.awareness.ecosystem import EcosystemGraph
    from redsl.awareness.self_model import SelfModel
    from redsl.dsl.engine import Rule


def smart_score(
    rule: Rule,
    context: dict[str, Any],
    *,
    timeline: GitTimelineAnalyzer | None = None,
    ecosystem: EcosystemGraph | None = None,
    self_model: SelfModel | None = None,
    coupling: dict[str, Any] | None = None,
) -> float:
    """Compute a multi-dimensional score for a refactoring decision.

    Falls back to the base ``rule.score(context)`` when no extra signals
    are provided.
    """
    base = rule.score(context)
    if base <= 0:
        return 0.0

    trend_mult = _trend_multiplier(context, timeline)
    eco_mult = _ecosystem_multiplier(context, ecosystem)
    coupling_mult = _coupling_multiplier(context, coupling)
    confidence_mult = _confidence_multiplier(context, rule, self_model)

    return base * trend_mult * eco_mult * coupling_mult * confidence_mult


# ---------------------------------------------------------------------------
# Dimension helpers
# ---------------------------------------------------------------------------

def _trend_multiplier(
    context: dict[str, Any],
    timeline: GitTimelineAnalyzer | None,
) -> float:
    """Boost priority when CC is trending upward."""
    if timeline is None:
        return 1.0
    file_path = context.get("file_path", "")
    try:
        tl = timeline.build_timeline(depth=5)
        if len(tl) < 3:
            return 1.0
        cc_values = [p.avg_cc for p in tl]
        if cc_values[0] > cc_values[-1]:
            return 1.3
        if cc_values[0] < cc_values[-1]:
            return 0.8
    except Exception:
        pass
    return 1.0


def _ecosystem_multiplier(
    context: dict[str, Any],
    ecosystem: EcosystemGraph | None,
) -> float:
    """Boost priority for files that are part of public API bridges."""
    if ecosystem is None:
        return 1.0
    file_path = context.get("file_path", "")
    if file_path.startswith("_"):
        return 1.0
    if "bridge" in file_path:
        project = context.get("project_name", "")
        try:
            dep_count = len(ecosystem.get_impact_chain(project))
        except Exception:
            dep_count = 0
        return 1.0 + dep_count * 0.15
    return 1.0


def _coupling_multiplier(
    context: dict[str, Any],
    coupling: dict[str, Any] | None,
) -> float:
    """Boost priority for modules with high fan-in (many importers)."""
    if coupling is None:
        return 1.0
    file_module = context.get("file_path", "").replace("/", ".").replace(".py", "")
    fan_in = coupling.get(file_module, {}).get("fan_in", 0)
    if fan_in > 5:
        return 1.2
    return 1.0


def _confidence_multiplier(
    context: dict[str, Any],
    rule: Rule,
    self_model: SelfModel | None,
) -> float:
    """Reduce priority when the agent's self-model says it can't fix this."""
    if self_model is None:
        return 1.0
    action = rule.action.value
    try:
        assessment = self_model.should_attempt(action, context)
        if not assessment.get("recommend", True):
            return 0.1
        return assessment.get("confidence", 0.7)
    except Exception:
        return 1.0
