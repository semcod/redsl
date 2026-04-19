"""Base class and implementations for model registry sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from ..models import ModelInfo


class ModelRegistrySource(ABC):
    """Abstract base class for model registry sources."""

    name: str
    enabled: bool = True

    @abstractmethod
    def fetch(self) -> list[ModelInfo]:
        """Fetch models from this source."""
        ...

    def _http_get(
        self,
        url: str,
        headers: dict | None = None,
        timeout: int = 10,
    ) -> dict:
        """Make HTTP GET request and return JSON."""
        with httpx.Client(timeout=timeout) as client:
            r = client.get(url, headers=headers or {})
            r.raise_for_status()
            return r.json()


class OpenRouterSource(ModelRegistrySource):
    """OpenRouter public API - no auth required, ~300+ models."""

    name = "openrouter"
    URL = "https://openrouter.ai/api/v1/models"

    def fetch(self) -> list[ModelInfo]:
        """Fetch models from OpenRouter."""
        from ..models import ModelInfo

        data = self._http_get(self.URL)
        out = []
        for m in data.get("data", []):
            created = m.get("created")
            release_date = datetime.utcfromtimestamp(created) if created else None
            model_id = m["id"]  # e.g., "openai/gpt-4o"
            provider = model_id.split("/")[0] if "/" in model_id else "unknown"
            out.append(
                ModelInfo(
                    id=model_id,
                    provider=provider,
                    release_date=release_date,
                    context_length=m.get("context_length"),
                    sources=(self.name,),
                    source_dates={self.name: release_date} if release_date else {},
                    raw=m,
                )
            )
        return out


class ModelsDevSource(ModelRegistrySource):
    """Models.dev community API - public, ~200+ models."""

    name = "models_dev"
    URL = "https://models.dev/api.json"

    def fetch(self) -> list[ModelInfo]:
        """Fetch models from models.dev."""
        from ..models import ModelInfo

        data = self._http_get(self.URL)
        out = []
        # Structure: { "providers": { "openai": { "models": { "gpt-4o": {...} } } } }
        for provider, pdata in data.get("providers", {}).items():
            for model_name, mdata in pdata.get("models", {}).items():
                rd_str = mdata.get("release_date")
                release_date = datetime.fromisoformat(rd_str) if rd_str else None
                model_id = f"{provider}/{model_name}"
                out.append(
                    ModelInfo(
                        id=model_id,
                        provider=provider,
                        release_date=release_date,
                        deprecated=mdata.get("deprecated", False),
                        context_length=mdata.get("context_length"),
                        sources=(self.name,),
                        source_dates={self.name: release_date} if release_date else {},
                        raw=mdata,
                    )
                )
        return out


class OpenAIProviderSource(ModelRegistrySource):
    """Native OpenAI API - requires key, authoritative for OpenAI models."""

    name = "openai_native"
    URL = "https://api.openai.com/v1/models"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.enabled = bool(api_key)

    def fetch(self) -> list[ModelInfo]:
        """Fetch models from OpenAI."""
        from ..models import ModelInfo

        if not self.api_key:
            return []
        data = self._http_get(
            self.URL, headers={"Authorization": f"Bearer {self.api_key}"}
        )
        out = []
        for m in data.get("data", []):
            created = m.get("created")
            release_date = datetime.utcfromtimestamp(created) if created else None
            model_id = f"openai/{m['id']}"
            out.append(
                ModelInfo(
                    id=model_id,
                    provider="openai",
                    release_date=release_date,
                    sources=(self.name,),
                    source_dates={self.name: release_date} if release_date else {},
                    raw=m,
                )
            )
        return out


class AnthropicProviderSource(ModelRegistrySource):
    """Native Anthropic API - requires key, authoritative for Claude models."""

    name = "anthropic_native"
    URL = "https://api.anthropic.com/v1/models"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.enabled = bool(api_key)

    def fetch(self) -> list[ModelInfo]:
        """Fetch models from Anthropic."""
        from ..models import ModelInfo

        if not self.api_key:
            return []
        data = self._http_get(
            self.URL,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        out = []
        for m in data.get("data", []):
            rd_str = m.get("created_at")
            release_date = (
                datetime.fromisoformat(rd_str.replace("Z", "+00:00"))
                if rd_str
                else None
            )
            model_id = f"anthropic/{m['id']}"
            out.append(
                ModelInfo(
                    id=model_id,
                    provider="anthropic",
                    release_date=release_date,
                    sources=(self.name,),
                    source_dates={self.name: release_date} if release_date else {},
                    raw=m,
                )
            )
        return out
