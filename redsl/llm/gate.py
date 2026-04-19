"""Model age policy gate - enforces model selection policy."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .registry.aggregator import RegistryAggregator
    from .registry.models import ModelInfo, PolicyDecision

log = logging.getLogger(__name__)


class ModelRejectedError(Exception):
    """Raised when model is rejected by policy."""

    pass


class ModelAgeGate:
    """Enforces model age and lifecycle policy before LLM calls."""

    def __init__(
        self,
        aggregator: RegistryAggregator,
        mode: str,  # PolicyMode value
        max_age_days: int,
        strict: bool,
        unknown_action: str,  # UnknownReleaseAction value
        min_sources_agree: int,
        blocklist: set[str],
        allowlist: set[str],
        fallback_map: dict[str, str],
    ):
        from .registry.models import PolicyMode, UnknownReleaseAction

        self.agg = aggregator
        self.mode = PolicyMode(mode)
        self.max_age_days = max_age_days
        self.strict = strict
        self.unknown_action = UnknownReleaseAction(unknown_action)
        self.min_sources_agree = min_sources_agree
        self.blocklist = blocklist
        self.allowlist = allowlist
        self.fallback_map = fallback_map

    def check(self, requested_model: str) -> PolicyDecision:
        """Check if model is allowed by policy."""
        from .registry.models import PolicyDecision, PolicyMode, UnknownReleaseAction

        norm = self._normalize(requested_model)

        # 1. Allowlist (hard override)
        if norm in self.allowlist:
            return PolicyDecision(
                allowed=True, model=norm, reason="allowlisted", age_days=None, sources_used=()
            )

        # 2. Blocklist (hard override)
        if norm in self.blocklist:
            return self._reject(norm, "blocklisted")

        # 3. Lookup in registry
        models = self.agg.get_all()
        info = models.get(norm)
        if info is None:
            return self._handle_unknown(norm, "not_in_registry")

        # 4. Deprecated?
        if info.deprecated:
            return self._reject(norm, f"deprecated ({list(info.sources)})")

        # 5. Min sources agreement
        sources_with_date = [
            s for s, d in info.source_dates.items() if d is not None
        ]
        if len(sources_with_date) < self.min_sources_agree:
            return self._handle_unknown(
                norm,
                f"only {len(sources_with_date)} source(s) provided date, need {self.min_sources_agree}",
            )

        # 6. Check age according to mode
        if info.release_date is None:
            return self._handle_unknown(norm, "no_release_date")

        allowed, reason = self._check_age(info, models)
        if not allowed:
            return self._reject(
                norm, reason, age_days=info.age_days, sources=info.sources
            )

        return PolicyDecision(
            allowed=True,
            model=norm,
            reason=f"ok (mode={self.mode.value}, age={info.age_days}d)",
            age_days=info.age_days,
            sources_used=info.sources,
        )

    def _check_age(
        self, info: ModelInfo, all_models: dict[str, ModelInfo]
    ) -> tuple[bool, str]:
        from .registry.models import PolicyMode

        if self.mode == PolicyMode.ABSOLUTE_AGE:
            if info.age_days > self.max_age_days:
                return False, f"age {info.age_days}d > max {self.max_age_days}d (absolute)"
            return True, "ok"

        if self.mode == PolicyMode.FRONTIER_LAG:
            latest = max(
                (m.release_date for m in all_models.values() if m.release_date),
                default=None,
            )
            if latest is None:
                return False, "cannot determine frontier date"
            lag = (latest - info.release_date).days
            if lag > self.max_age_days:
                return False, f"lag {lag}d behind frontier ({latest.date()}) > max {self.max_age_days}d"
            return True, f"lag {lag}d"

        if self.mode == PolicyMode.LIFECYCLE:
            # deprecated already checked earlier
            return True, "lifecycle_only"

        return False, f"unknown mode {self.mode}"

    def _handle_unknown(self, model: str, why: str) -> PolicyDecision:
        from .registry.models import PolicyDecision, UnknownReleaseAction

        if self.unknown_action == UnknownReleaseAction.ALLOW:
            log.warning("Unknown release for %s (%s), allowing by policy", model, why)
            return PolicyDecision(
                allowed=True, model=model, reason=f"unknown_allowed: {why}", age_days=None, sources_used=()
            )
        return self._reject(model, f"unknown: {why}")

    def _reject(
        self, model: str, reason: str, age_days=None, sources=()
    ) -> PolicyDecision:
        from .registry.models import PolicyDecision

        fallback = self.fallback_map.get(model)
        if self.strict or not fallback:
            if self.strict:
                raise ModelRejectedError(f"Model {model} rejected: {reason}")
            return PolicyDecision(
                allowed=False, model=model, reason=reason, age_days=age_days, sources_used=sources
            )
        log.warning("Model %s rejected (%s), falling back to %s", model, reason, fallback)
        return self.check(fallback)  # recursively check fallback

    def _normalize(self, model: str) -> str:
        """Normalize alias to 'provider/model' format."""
        if "/" in model:
            return model
        # Simple heuristics for common providers
        if model.startswith("gpt-") or model.startswith("o1-"):
            return f"openai/{model}"
        if model.startswith("claude-"):
            return f"anthropic/{model}"
        if model.startswith("gemini-"):
            return f"google/{model}"
        return model

    def list_allowed(self) -> list[str]:
        """List all models currently allowed by policy."""
        allowed = []
        for model_id in self.agg.get_all():
            try:
                decision = self.check(model_id)
                if decision.allowed:
                    allowed.append(model_id)
            except ModelRejectedError:
                pass  # Model rejected, skip
        return sorted(allowed)
