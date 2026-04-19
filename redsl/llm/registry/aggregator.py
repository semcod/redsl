"""Registry aggregator - merges multiple sources with caching."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import ModelInfo
    from .sources.base import ModelRegistrySource

log = logging.getLogger(__name__)


class RegistryAggregator:
    """Aggregates model info from multiple sources with caching."""

    def __init__(
        self,
        sources: list[ModelRegistrySource],
        cache_path: Path,
        cache_ttl: int,
        stale_grace: int,
        disagreement_threshold_days: int = 14,
        enrichers: list | None = None,
    ):
        self.sources = sources
        self.cache_path = cache_path
        self.cache_ttl = cache_ttl
        self.stale_grace = stale_grace
        self.disagreement_days = disagreement_threshold_days
        self.enrichers = enrichers or []
        self._cache: dict[str, ModelInfo] | None = None
        self._cache_fetched_at: datetime | None = None

    def get_all(self) -> dict[str, ModelInfo]:
        """Get all models from cache or fetch from sources."""
        if self._cache_is_fresh():
            return self._cache
        try:
            merged = self._fetch_and_merge()
            self._save_cache(merged)
            self._cache, self._cache_fetched_at = merged, datetime.now(timezone.utc)
            return merged
        except Exception as e:
            log.warning("Registry fetch failed: %s. Falling back to stale cache.", e)
            if self._load_stale_cache():
                return self._cache
            raise

    def get(self, model_id: str) -> ModelInfo | None:
        """Get specific model by ID."""
        return self.get_all().get(model_id)

    def _fetch_and_merge(self) -> dict[str, ModelInfo]:
        """Fetch from all sources and merge by model_id."""
        from .models import ModelInfo

        by_id: dict[str, list[ModelInfo]] = {}
        for src in self.sources:
            if not src.enabled:
                log.debug("Source %s disabled, skipping", src.name)
                continue
            try:
                models = src.fetch()
                log.info("Source %s returned %d models", src.name, len(models))
                for m in models:
                    by_id.setdefault(m.id, []).append(m)
            except Exception as e:
                log.warning("Source %s failed: %s", src.name, e)

        merged = {mid: self._merge_model(mid, infos) for mid, infos in by_id.items()}

        # Run enrichers after merging
        for enricher in self.enrichers:
            try:
                log.debug("Running enricher: %s", getattr(enricher, 'name', type(enricher).__name__))
                merged = enricher.enrich(merged)
            except Exception as e:
                log.warning("Enricher failed: %s", e)

        return merged

    def _merge_model(self, model_id: str, infos: list[ModelInfo]) -> ModelInfo:
        """Merge multiple ModelInfo entries for same model from different sources."""
        from .models import ModelInfo

        base_info = infos[0]
        source_dates, sources = self._collect_source_info(infos)
        deprecated = any(info.deprecated for info in infos)
        context_length = self._merge_context_length(infos)

        merged_pricing = self._merge_pricing(infos)
        merged_capabilities = self._merge_capabilities(infos)
        merged_quality = self._merge_quality(infos)

        release_date = self._compute_release_date(source_dates, model_id)

        return ModelInfo(
            id=model_id,
            provider=base_info.provider,
            release_date=release_date,
            deprecated=deprecated,
            context_length=context_length,
            sources=tuple(set(sources)),
            source_dates=source_dates,
            raw=base_info.raw,
            pricing=merged_pricing,
            capabilities=merged_capabilities,
            quality=merged_quality,
        )

    def _collect_source_info(self, infos: list[ModelInfo]) -> tuple[dict, list]:
        """Collect source dates and sources from all infos."""
        source_dates = {}
        sources = []
        for info in infos:
            sources.extend(info.sources)
            source_dates.update(info.source_dates)
        return source_dates, sources

    def _merge_context_length(self, infos: list[ModelInfo]) -> int | None:
        """Find the first available context length."""
        for info in infos:
            if info.context_length:
                return info.context_length
        return None

    def _merge_pricing(self, infos: list[ModelInfo]) -> "Pricing":
        """Take first known pricing."""
        from .models import Pricing
        for info in infos:
            if info.pricing.is_known:
                return info.pricing
        return Pricing()

    def _merge_capabilities(self, infos: list[ModelInfo]) -> "Capabilities":
        """Merge capabilities taking highest context length."""
        from .models import Capabilities
        merged = Capabilities()
        for info in infos:
            cap = info.capabilities
            if cap.context_length and (not merged.context_length or cap.context_length > merged.context_length):
                merged = cap
        return merged

    def _merge_quality(self, infos: list[ModelInfo]) -> "QualitySignals":
        """Merge quality signals with OR flags and max scores."""
        from .models import QualitySignals
        merged = QualitySignals()
        for info in infos:
            q = info.quality
            merged = QualitySignals(
                openrouter_category_programming=merged.openrouter_category_programming or q.openrouter_category_programming,
                aider_polyglot_score=max(filter(None, [merged.aider_polyglot_score, q.aider_polyglot_score]), default=None),
                livebench_coding_score=max(filter(None, [merged.livebench_coding_score, q.livebench_coding_score]), default=None),
                in_known_good_list=merged.in_known_good_list or q.in_known_good_list,
            )
        return merged

    def _compute_release_date(self, source_dates: dict, model_id: str) -> "datetime | None":
        """Compute conservative release date from source dates."""
        from datetime import datetime
        dates_only = [d for d in source_dates.values() if d is not None]

        if len(dates_only) >= 2:
            spread = (max(dates_only) - min(dates_only)).days
            if spread > self.disagreement_days:
                log.warning(
                    "Model %s: sources disagree by %d days: %s",
                    model_id,
                    spread,
                    {k: v.isoformat() if isinstance(v, datetime) else v for k, v in source_dates.items()},
                )

        return min(dates_only) if dates_only else None

    def _cache_is_fresh(self) -> bool:
        """Check if in-memory cache is fresh."""
        if self._cache is None or self._cache_fetched_at is None:
            return False
        age = (datetime.now(timezone.utc) - self._cache_fetched_at).total_seconds()
        return age < self.cache_ttl

    def _save_cache(self, merged: dict[str, ModelInfo]) -> None:
        """Save merged models to disk cache."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

        def _decimal_to_str(d):
            return str(d) if d is not None else None

        serialized = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "models": {
                mid: {
                    "id": m.id,
                    "provider": m.provider,
                    "release_date": m.release_date.isoformat() if m.release_date else None,
                    "deprecated": m.deprecated,
                    "context_length": m.context_length,
                    "sources": list(m.sources),
                    "source_dates": {
                        k: v.isoformat() for k, v in m.source_dates.items()
                    },
                    "pricing": {
                        "prompt": _decimal_to_str(m.pricing.prompt),
                        "completion": _decimal_to_str(m.pricing.completion),
                        "request": _decimal_to_str(m.pricing.request),
                        "image": _decimal_to_str(m.pricing.image),
                    },
                    "capabilities": {
                        "context_length": m.capabilities.context_length,
                        "supports_tool_calling": m.capabilities.supports_tool_calling,
                        "supports_json_mode": m.capabilities.supports_json_mode,
                        "supports_streaming": m.capabilities.supports_streaming,
                        "supports_vision": m.capabilities.supports_vision,
                        "output_modalities": list(m.capabilities.output_modalities),
                        "max_output_tokens": m.capabilities.max_output_tokens,
                    },
                    "quality": {
                        "openrouter_category_programming": m.quality.openrouter_category_programming,
                        "aider_polyglot_score": m.quality.aider_polyglot_score,
                        "livebench_coding_score": m.quality.livebench_coding_score,
                        "in_known_good_list": m.quality.in_known_good_list,
                    },
                }
                for mid, m in merged.items()
            },
        }
        self.cache_path.write_text(json.dumps(serialized, indent=2))
        log.info("Saved %d models to cache at %s", len(merged), self.cache_path)

    def _load_stale_cache(self) -> bool:
        """Load cache even if stale (when network fails)."""
        from .models import ModelInfo, Pricing, Capabilities, QualitySignals

        if not self.cache_path.exists():
            return False
        try:
            data = json.loads(self.cache_path.read_text())
            fetched_at = datetime.fromisoformat(data["fetched_at"])
            age = (datetime.now(timezone.utc) - fetched_at).total_seconds()
            if age > self.stale_grace:
                log.error(
                    "Cache too stale (%ds > %ds grace), refusing", age, self.stale_grace
                )
                return False

            def _str_to_decimal(s):
                return Decimal(s) if s is not None else None

            self._cache = {}
            for mid, m in data["models"].items():
                # Handle old cache format without new fields
                pricing_data = m.get("pricing", {})
                caps_data = m.get("capabilities", {})
                quality_data = m.get("quality", {})

                self._cache[mid] = ModelInfo(
                    id=m["id"],
                    provider=m["provider"],
                    release_date=datetime.fromisoformat(m["release_date"])
                    if m.get("release_date")
                    else None,
                    deprecated=m.get("deprecated", False),
                    context_length=m.get("context_length"),
                    sources=tuple(m["sources"]),
                    source_dates={
                        k: datetime.fromisoformat(v)
                        for k, v in m["source_dates"].items()
                    },
                    raw={},
                    pricing=Pricing(
                        prompt=_str_to_decimal(pricing_data.get("prompt")),
                        completion=_str_to_decimal(pricing_data.get("completion")),
                        request=_str_to_decimal(pricing_data.get("request")),
                        image=_str_to_decimal(pricing_data.get("image")),
                    ),
                    capabilities=Capabilities(
                        context_length=caps_data.get("context_length"),
                        supports_tool_calling=caps_data.get("supports_tool_calling", False),
                        supports_json_mode=caps_data.get("supports_json_mode", False),
                        supports_streaming=caps_data.get("supports_streaming", True),
                        supports_vision=caps_data.get("supports_vision", False),
                        output_modalities=tuple(caps_data.get("output_modalities", ["text"])),
                        max_output_tokens=caps_data.get("max_output_tokens"),
                    ),
                    quality=QualitySignals(
                        openrouter_category_programming=quality_data.get("openrouter_category_programming", False),
                        aider_polyglot_score=quality_data.get("aider_polyglot_score"),
                        livebench_coding_score=quality_data.get("livebench_coding_score"),
                        in_known_good_list=quality_data.get("in_known_good_list", False),
                    ),
                )
            self._cache_fetched_at = fetched_at
            log.warning("Loaded stale cache from %s (age=%ds)", self.cache_path, age)
            return True
        except Exception as e:
            log.error("Cache load failed: %s", e)
            return False

    def refresh(self) -> dict[str, ModelInfo]:
        """Force refresh from sources, ignoring cache."""
        self._cache = None
        self._cache_fetched_at = None
        return self.get_all()
