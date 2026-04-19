"""Registry aggregator - merges multiple sources with caching."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
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
    ):
        self.sources = sources
        self.cache_path = cache_path
        self.cache_ttl = cache_ttl
        self.stale_grace = stale_grace
        self.disagreement_days = disagreement_threshold_days
        self._cache: dict[str, ModelInfo] | None = None
        self._cache_fetched_at: datetime | None = None

    def get_all(self) -> dict[str, ModelInfo]:
        """Get all models from cache or fetch from sources."""
        if self._cache_is_fresh():
            return self._cache
        try:
            merged = self._fetch_and_merge()
            self._save_cache(merged)
            self._cache, self._cache_fetched_at = merged, datetime.utcnow()
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

        return {mid: self._merge_model(mid, infos) for mid, infos in by_id.items()}

    def _merge_model(self, model_id: str, infos: list[ModelInfo]) -> ModelInfo:
        """Merge multiple ModelInfo entries for same model from different sources."""
        from .models import ModelInfo

        # Collect all dates from different sources
        source_dates = {}
        sources = []
        deprecated = False
        context_length = None

        for info in infos:
            sources.extend(info.sources)
            source_dates.update(info.source_dates)
            if info.deprecated:
                deprecated = True
            if info.context_length and not context_length:
                context_length = info.context_length

        # Check for disagreement between sources
        dates_only = [d for d in source_dates.values() if d is not None]
        if len(dates_only) >= 2:
            spread = (max(dates_only) - min(dates_only)).days
            if spread > self.disagreement_days:
                log.warning(
                    "Model %s: sources disagree by %d days: %s",
                    model_id,
                    spread,
                    {k: v.isoformat() for k, v in source_dates.items()},
                )

        # Conservative: earliest known date (model is not "younger" than this)
        release_date = min(dates_only) if dates_only else None

        return ModelInfo(
            id=model_id,
            provider=infos[0].provider,
            release_date=release_date,
            deprecated=deprecated,
            context_length=context_length,
            sources=tuple(set(sources)),
            source_dates=source_dates,
            raw=infos[0].raw,
        )

    def _cache_is_fresh(self) -> bool:
        """Check if in-memory cache is fresh."""
        if self._cache is None or self._cache_fetched_at is None:
            return False
        age = (datetime.utcnow() - self._cache_fetched_at).total_seconds()
        return age < self.cache_ttl

    def _save_cache(self, merged: dict[str, ModelInfo]) -> None:
        """Save merged models to disk cache."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        serialized = {
            "fetched_at": datetime.utcnow().isoformat(),
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
                }
                for mid, m in merged.items()
            },
        }
        self.cache_path.write_text(json.dumps(serialized, indent=2))
        log.info("Saved %d models to cache at %s", len(merged), self.cache_path)

    def _load_stale_cache(self) -> bool:
        """Load cache even if stale (when network fails)."""
        from .models import ModelInfo

        if not self.cache_path.exists():
            return False
        try:
            data = json.loads(self.cache_path.read_text())
            fetched_at = datetime.fromisoformat(data["fetched_at"])
            age = (datetime.utcnow() - fetched_at).total_seconds()
            if age > self.stale_grace:
                log.error(
                    "Cache too stale (%ds > %ds grace), refusing", age, self.stale_grace
                )
                return False
            self._cache = {
                mid: ModelInfo(
                    id=m["id"],
                    provider=m["provider"],
                    release_date=datetime.fromisoformat(m["release_date"])
                    if m["release_date"]
                    else None,
                    deprecated=m["deprecated"],
                    context_length=m["context_length"],
                    sources=tuple(m["sources"]),
                    source_dates={
                        k: datetime.fromisoformat(v)
                        for k, v in m["source_dates"].items()
                    },
                )
                for mid, m in data["models"].items()
            }
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
