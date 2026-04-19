"""Model registry data types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PolicyMode(str, Enum):
    """Policy mode for model age checking."""

    ABSOLUTE_AGE = "absolute_age"
    FRONTIER_LAG = "frontier_lag"
    LIFECYCLE = "lifecycle"


class UnknownReleaseAction(str, Enum):
    """Action when model release date is unknown."""

    DENY = "deny"
    ALLOW = "allow"
    CACHE = "cache"


@dataclass(frozen=True)
class ModelInfo:
    """Information about an LLM model."""

    id: str  # normalized: "openai/gpt-4o"
    provider: str
    release_date: datetime | None
    deprecated: bool = False
    context_length: int | None = None
    sources: tuple[str, ...] = ()  # which registries provided this
    source_dates: dict[str, datetime] = field(default_factory=dict)  # per-source
    raw: dict = field(default_factory=dict)

    @property
    def age_days(self) -> int | None:
        """Calculate age in days from release date."""
        if self.release_date is None:
            return None
        return (datetime.utcnow() - self.release_date).days


@dataclass
class PolicyDecision:
    """Result of policy check for a model."""

    allowed: bool
    model: str  # final model to use (may be fallback)
    reason: str
    age_days: int | None
    sources_used: tuple[str, ...]
