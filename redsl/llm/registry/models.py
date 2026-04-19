"""Model registry data types."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal
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


# =============================================================================
# Coding Model Selection - Pricing, Capabilities, Quality Signals
# =============================================================================

@dataclass(frozen=True)
class Pricing:
    """Ceny USD per token (nie per million!)."""

    prompt: Decimal | None = None       # input cost per token
    completion: Decimal | None = None   # output cost per token
    request: Decimal | None = None      # per-request flat fee
    image: Decimal | None = None        # per image (multimodal)

    @property
    def is_known(self) -> bool:
        return self.prompt is not None and self.completion is not None


@dataclass(frozen=True)
class Capabilities:
    """Features modelu istotne dla programowania."""

    context_length: int | None = None
    supports_tool_calling: bool = False
    supports_json_mode: bool = False
    supports_streaming: bool = True
    supports_vision: bool = False
    output_modalities: tuple[str, ...] = ("text",)
    max_output_tokens: int | None = None


@dataclass(frozen=True)
class QualitySignals:
    """Sygnały jakości z różnych benchmarków."""

    openrouter_category_programming: bool = False
    aider_polyglot_score: float | None = None
    livebench_coding_score: float | None = None
    in_known_good_list: bool = False

    @property
    def has_any(self) -> bool:
        return any([
            self.openrouter_category_programming,
            self.aider_polyglot_score is not None,
            self.livebench_coding_score is not None,
            self.in_known_good_list,
        ])


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
    # NOWE: rozszerzone pola dla selekcji modeli
    pricing: Pricing = field(default_factory=Pricing)
    capabilities: Capabilities = field(default_factory=Capabilities)
    quality: QualitySignals = field(default_factory=QualitySignals)

    @property
    def age_days(self) -> int | None:
        """Calculate age in days from release date."""
        if self.release_date is None:
            return None
        return (datetime.now(timezone.utc) - self.release_date).days


@dataclass
class PolicyDecision:
    """Result of policy check for a model."""

    allowed: bool
    model: str  # final model to use (may be fallback)
    reason: str
    age_days: int | None
    sources_used: tuple[str, ...]
