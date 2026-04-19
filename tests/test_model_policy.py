"""Tests for LLM Model Age Policy system."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from redsl.llm.gate import ModelAgeGate, ModelRejectedError
from redsl.llm.registry.aggregator import RegistryAggregator
from redsl.llm.registry.models import ModelInfo, PolicyDecision, PolicyMode, UnknownReleaseAction


class TestModelInfo:
    """Test ModelInfo dataclass."""

    def test_age_days_calculation(self):
        """Test age_days property."""
        release = datetime.utcnow() - timedelta(days=30)
        info = ModelInfo(
            id="openai/test-model",
            provider="openai",
            release_date=release,
        )
        assert info.age_days == 30

    def test_age_days_none_when_no_release_date(self):
        """Test age_days returns None when release_date is None."""
        info = ModelInfo(
            id="openai/test-model",
            provider="openai",
            release_date=None,
        )
        assert info.age_days is None


class TestModelAgeGate:
    """Test ModelAgeGate policy enforcement."""

    @pytest.fixture
    def mock_aggregator(self):
        """Create mock aggregator with test models."""
        agg = Mock(spec=RegistryAggregator)
        now = datetime.utcnow()

        # Create test models
        models = {
            "openai/new-model": ModelInfo(
                id="openai/new-model",
                provider="openai",
                release_date=now - timedelta(days=10),
                sources=("openrouter",),
                source_dates={"openrouter": now - timedelta(days=10)},
            ),
            "openai/old-model": ModelInfo(
                id="openai/old-model",
                provider="openai",
                release_date=now - timedelta(days=500),
                sources=("openrouter", "models_dev"),
                source_dates={
                    "openrouter": now - timedelta(days=500),
                    "models_dev": now - timedelta(days=500),
                },
            ),
            "openai/deprecated-model": ModelInfo(
                id="openai/deprecated-model",
                provider="openai",
                release_date=now - timedelta(days=100),
                deprecated=True,
                sources=("openrouter",),
                source_dates={"openrouter": now - timedelta(days=100)},
            ),
            "openai/single-source": ModelInfo(
                id="openai/single-source",
                provider="openai",
                release_date=now - timedelta(days=50),
                sources=("openrouter",),
                source_dates={"openrouter": now - timedelta(days=50)},
            ),
        }

        agg.get_all.return_value = models
        agg.get.side_effect = lambda mid: models.get(mid)
        return agg

    def test_allowlisted_model_allowed(self, mock_aggregator):
        """Test allowlisted models bypass all checks."""
        gate = ModelAgeGate(
            aggregator=mock_aggregator,
            mode="frontier_lag",
            max_age_days=180,
            strict=True,
            unknown_action="deny",
            min_sources_agree=2,
            blocklist=set(),
            allowlist={"openai/old-model"},
            fallback_map={},
        )

        decision = gate.check("openai/old-model")
        assert decision.allowed is True
        assert "allowlisted" in decision.reason

    def test_blocklisted_model_rejected(self, mock_aggregator):
        """Test blocklisted models are rejected."""
        gate = ModelAgeGate(
            aggregator=mock_aggregator,
            mode="frontier_lag",
            max_age_days=180,
            strict=True,
            unknown_action="deny",
            min_sources_agree=2,
            blocklist={"openai/new-model"},
            allowlist=set(),
            fallback_map={},
        )

        with pytest.raises(ModelRejectedError, match="blocklisted"):
            gate.check("openai/new-model")

    def test_deprecated_model_rejected(self, mock_aggregator):
        """Test deprecated models are rejected."""
        gate = ModelAgeGate(
            aggregator=mock_aggregator,
            mode="frontier_lag",
            max_age_days=180,
            strict=True,
            unknown_action="deny",
            min_sources_agree=1,
            blocklist=set(),
            allowlist=set(),
            fallback_map={},
        )

        with pytest.raises(ModelRejectedError, match="deprecated"):
            gate.check("openai/deprecated-model")

    def test_min_sources_requirement(self, mock_aggregator):
        """Test minimum sources requirement."""
        gate = ModelAgeGate(
            aggregator=mock_aggregator,
            mode="frontier_lag",
            max_age_days=180,
            strict=True,
            unknown_action="deny",
            min_sources_agree=2,
            blocklist=set(),
            allowlist=set(),
            fallback_map={},
        )

        # single-source model should be rejected when min_sources=2
        with pytest.raises(ModelRejectedError, match="only 1 source"):
            gate.check("openai/single-source")

    def test_absolute_age_mode(self, mock_aggregator):
        """Test absolute_age mode."""
        gate = ModelAgeGate(
            aggregator=mock_aggregator,
            mode="absolute_age",
            max_age_days=30,
            strict=True,
            unknown_action="deny",
            min_sources_agree=1,
            blocklist=set(),
            allowlist=set(),
            fallback_map={},
        )

        # 10-day old model allowed
        decision = gate.check("openai/new-model")
        assert decision.allowed is True

        # 500-day old model rejected
        with pytest.raises(ModelRejectedError, match="age 500d"):
            gate.check("openai/old-model")

    def test_frontier_lag_mode(self, mock_aggregator):
        """Test frontier_lag mode."""
        gate = ModelAgeGate(
            aggregator=mock_aggregator,
            mode="frontier_lag",
            max_age_days=180,
            strict=True,
            unknown_action="deny",
            min_sources_agree=1,
            blocklist=set(),
            allowlist=set(),
            fallback_map={},
        )

        # 10-day old model allowed (newest is 10 days)
        decision = gate.check("openai/new-model")
        assert decision.allowed is True

    def test_lifecycle_mode(self, mock_aggregator):
        """Test lifecycle mode (only checks deprecation)."""
        gate = ModelAgeGate(
            aggregator=mock_aggregator,
            mode="lifecycle",
            max_age_days=180,
            strict=True,
            unknown_action="deny",
            min_sources_agree=1,
            blocklist=set(),
            allowlist=set(),
            fallback_map={},
        )

        # Old model allowed (not deprecated)
        decision = gate.check("openai/old-model")
        assert decision.allowed is True
        assert "lifecycle" in decision.reason

    def test_unknown_release_deny(self, mock_aggregator):
        """Test unknown release date with deny action."""
        gate = ModelAgeGate(
            aggregator=mock_aggregator,
            mode="frontier_lag",
            max_age_days=180,
            strict=True,
            unknown_action="deny",
            min_sources_agree=1,
            blocklist=set(),
            allowlist=set(),
            fallback_map={},
        )

        with pytest.raises(ModelRejectedError, match="not_in_registry"):
            gate.check("openai/unknown-model")

    def test_unknown_release_allow(self, mock_aggregator):
        """Test unknown release date with allow action."""
        gate = ModelAgeGate(
            aggregator=mock_aggregator,
            mode="frontier_lag",
            max_age_days=180,
            strict=True,
            unknown_action="allow",
            min_sources_agree=1,
            blocklist=set(),
            allowlist=set(),
            fallback_map={},
        )

        decision = gate.check("openai/unknown-model")
        assert decision.allowed is True
        assert "unknown_allowed" in decision.reason

    def test_fallback_chain(self, mock_aggregator):
        """Test fallback to alternative model."""
        gate = ModelAgeGate(
            aggregator=mock_aggregator,
            mode="frontier_lag",
            max_age_days=180,
            strict=False,  # non-strict
            unknown_action="deny",
            min_sources_agree=1,
            blocklist=set(),
            allowlist=set(),
            fallback_map={"openai/old-model": "openai/new-model"},
        )

        # Should fallback to new-model
        decision = gate.check("openai/old-model")
        assert decision.allowed is True
        assert decision.model == "openai/new-model"

    def test_model_normalization(self):
        """Test model name normalization."""
        from unittest.mock import Mock

        # Create fresh mock for this test
        now = datetime.utcnow()
        agg = Mock()
        models_dict = {
            "openai/gpt-4o-new": ModelInfo(
                id="openai/gpt-4o-new",
                provider="openai",
                release_date=now - timedelta(days=5),
                sources=("openrouter",),
                source_dates={"openrouter": now - timedelta(days=5)},
            ),
        }
        agg.get_all.return_value = models_dict
        agg.get.side_effect = lambda mid: models_dict.get(mid)

        gate = ModelAgeGate(
            aggregator=agg,
            mode="frontier_lag",
            max_age_days=180,
            strict=True,
            unknown_action="deny",
            min_sources_agree=1,
            blocklist=set(),
            allowlist=set(),
            fallback_map={},
        )

        # Bare gpt- names should be normalized to openai/gpt-*
        decision = gate.check("gpt-4o-new")
        assert decision.allowed is True
        assert decision.model == "openai/gpt-4o-new"


class TestRegistryAggregator:
    """Test RegistryAggregator."""

    def test_cache_save_and_load(self):
        """Test saving and loading cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"

            # Create mock source
            mock_source = Mock()
            mock_source.name = "test"
            mock_source.enabled = True
            now = datetime.utcnow()
            mock_source.fetch.return_value = [
                ModelInfo(
                    id="test/model",
                    provider="test",
                    release_date=now,
                    sources=("test",),
                    source_dates={"test": now},
                )
            ]

            agg = RegistryAggregator(
                sources=[mock_source],
                cache_path=cache_path,
                cache_ttl=3600,
                stale_grace=86400,
            )

            # Fetch and save
            models = agg.get_all()
            assert "test/model" in models

            # Verify cache file was created
            assert cache_path.exists()

            # Create new aggregator and load from cache using stale grace
            agg2 = RegistryAggregator(
                sources=[],  # No sources, should use stale cache
                cache_path=cache_path,
                cache_ttl=0,  # Cache considered stale immediately
                stale_grace=86400,  # But stale is OK for 1 day
            )
            # Force loading stale cache
            assert agg2._load_stale_cache() is True
            # Check that cache was loaded
            assert agg2._cache is not None
            assert "test/model" in agg2._cache

    def test_source_disagreement_warning(self, caplog):
        """Test warning when sources disagree on date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"
            now = datetime.utcnow()

            # Create mock sources with disagreeing dates
            source1 = Mock()
            source1.name = "source1"
            source1.enabled = True
            source1.fetch.return_value = [
                ModelInfo(
                    id="test/model",
                    provider="test",
                    release_date=now - timedelta(days=10),
                    sources=("source1",),
                    source_dates={"source1": now - timedelta(days=10)},
                )
            ]

            source2 = Mock()
            source2.name = "source2"
            source2.enabled = True
            source2.fetch.return_value = [
                ModelInfo(
                    id="test/model",
                    provider="test",
                    release_date=now - timedelta(days=30),
                    sources=("source2",),
                    source_dates={"source2": now - timedelta(days=30)},
                )
            ]

            import logging
            with caplog.at_level(logging.WARNING):
                agg = RegistryAggregator(
                    sources=[source1, source2],
                    cache_path=cache_path,
                    cache_ttl=3600,
                    stale_grace=86400,
                    disagreement_threshold_days=14,
                )
                agg.get_all()

            assert "disagree by 20 days" in caplog.text


class TestRegistrySources:
    """Test registry source implementations."""

    def test_openrouter_source_structure(self):
        """Test OpenRouterSource has correct structure."""
        from redsl.llm.registry.sources.base import OpenRouterSource

        source = OpenRouterSource()
        assert source.name == "openrouter"
        assert source.enabled is True
        assert source.URL == "https://openrouter.ai/api/v1/models"

    def test_models_dev_source_structure(self):
        """Test ModelsDevSource has correct structure."""
        from redsl.llm.registry.sources.base import ModelsDevSource

        source = ModelsDevSource()
        assert source.name == "models_dev"
        assert source.enabled is True
        assert source.URL == "https://models.dev/api.json"

    def test_openai_source_disabled_without_key(self):
        """Test OpenAI source is disabled without API key."""
        from redsl.llm.registry.sources.base import OpenAIProviderSource

        source = OpenAIProviderSource("")
        assert source.enabled is False

        source_with_key = OpenAIProviderSource("sk-test")
        assert source_with_key.enabled is True

    def test_anthropic_source_disabled_without_key(self):
        """Test Anthropic source is disabled without API key."""
        from redsl.llm.registry.sources.base import AnthropicProviderSource

        source = AnthropicProviderSource("")
        assert source.enabled is False

        source_with_key = AnthropicProviderSource("sk-test")
        assert source_with_key.enabled is True
