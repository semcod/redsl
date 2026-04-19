"""
Warstwa LLM — jednolity interfejs do wszystkich modeli.

Używa LiteLLM jako abstrakcji, co pozwala na:
- OpenAI (gpt-5.4-mini, gpt-4o)
- Anthropic (claude-3.5-sonnet)
- Ollama (llama3, mistral) — lokalne modele
- Azure, Gemini, itd.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

from redsl.config import LLMConfig
from .llx_router import _normalize_model_name

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Odpowiedź z modelu LLM."""

    content: str
    model: str
    tokens_used: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


class LLMLayer:
    """
    Warstwa abstrakcji nad LLM z obsługą:
    - wywołań tekstowych
    - odpowiedzi JSON
    - zliczania tokenów
    - fallbacku do innego modelu
    """

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self._call_count = 0

    def _load_provider_key(self, env_name: str, model: str, provider_name: str) -> str:
        from dotenv import load_dotenv

        load_dotenv()
        provider_key = os.getenv(env_name) or self.config.provider_key
        if not provider_key:
            raise ValueError(f"{env_name} not found in environment variables")
        logger.info(f"Using {provider_name} with model: {model}")
        return provider_key

    def _resolve_provider_key(self, model: str, config_model: str) -> str | None:
        if model.startswith("xai/") or config_model.startswith("xai/"):
            return self._load_provider_key("XAI_API_KEY", model, "xAI")
        if model.startswith("openrouter/") or config_model.startswith("openrouter/"):
            return self._load_provider_key("OPENROUTER_API_KEY", model, "OpenRouter")
        if self.config.provider_key and not self.config.is_local:
            return self.config.provider_key
        return None

    def _build_completion_kwargs(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool,
        config_model: str,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        provider_key = self._resolve_provider_key(model, config_model)
        if provider_key:
            kwargs["api_key"] = provider_key

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        return kwargs

    def call(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Wywołaj model LLM with age policy enforcement."""
        model = _normalize_model_name(model or self.config.model)
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens
        config_model = _normalize_model_name(self.config.model)

        # OpenRouter API key should be set via environment variable
        # LiteLLM handles OpenRouter routing automatically with openrouter/ prefix
        kwargs = self._build_completion_kwargs(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
            config_model=config_model,
        )

        logger.info("LLM call #%d → model=%s", self._call_count + 1, model)

        try:
            # Use safe_completion to enforce model age policy
            response = safe_completion(**kwargs)
            self._call_count += 1

            content = response["choices"][0]["message"]["content"]
            tokens = response.get("usage", {}).get("total_tokens", 0)

            logger.info(
                "LLM call #%d OK: model=%s, tokens=%d",
                self._call_count, model, tokens,
            )

            return LLMResponse(
                content=content,
                model=model,
                tokens_used=tokens,
                raw=dict(response),
            )
        except ModelRejectedError as e:
            logger.error("LLM call rejected by model policy: %s", e)
            raise
        except Exception as e:
            logger.error("LLM call failed: %s", e)
            raise

    def call_json(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
    ) -> dict[str, Any]:
        """Wywołaj model i sparsuj odpowiedź JSON."""
        response = self.call(messages, model=model, json_mode=True)

        text = response.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        try:
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                logger.warning("LLM returned non-dict JSON (%s), retrying...", type(parsed).__name__)
                raise json.JSONDecodeError("expected object", text, 0)
            return parsed
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from LLM response, retrying...")
            retry_msgs = messages + [
                {"role": "assistant", "content": response.content},
                {"role": "user", "content": "Please fix the JSON format. Return ONLY valid JSON object {}."},
            ]
            response2 = self.call(retry_msgs, model=model, json_mode=True)
            parsed2 = json.loads(response2.content.strip())
            return parsed2 if isinstance(parsed2, dict) else {}

    def reflect(self, original: str, context: str = "", model_override: str | None = None) -> str:
        """
        Pętla refleksji — model ocenia i poprawia swoją odpowiedź.
        To jest rdzeń „proto-świadomości" systemu.
        """
        # Krok 1: Krytyka
        critique_response = self.call([
            {
                "role": "system",
                "content": (
                    "You are a senior code reviewer. Critically evaluate the proposed "
                    "refactoring. Find potential issues: breaking changes, missing edge cases, "
                    "loss of functionality, naming problems, style violations."
                ),
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nProposed change:\n{original}\n\n"
                           f"List all issues and concerns.",
            },
        ], model=model_override or self.config.reflection_model, temperature=self.config.reflection_temperature)

        # Krok 2: Poprawa na podstawie krytyki
        improved_response = self.call([
            {
                "role": "system",
                "content": (
                    "You are a code refactoring expert. Improve the proposed change "
                    "based on the critique. Keep behavior identical. Fix all identified issues."
                ),
            },
            {
                "role": "user",
                "content": f"Original proposal:\n{original}\n\n"
                           f"Critique:\n{critique_response.content}\n\n"
                           f"Provide the improved version.",
            },
        ], model=model_override or self.config.reflection_model)

        logger.info("Reflection complete: critique + improvement applied")
        return improved_response.content

    @property
    def total_calls(self) -> int:
        return self._call_count


# =============================================================================
# Model Age Policy Gate Integration
# =============================================================================

import os
from pathlib import Path

from .gate import ModelAgeGate, ModelRejectedError
from .registry.aggregator import RegistryAggregator
from .registry.sources.base import (
    AnthropicProviderSource,
    ModelsDevSource,
    OpenAIProviderSource,
    OpenRouterSource,
)
from .registry.models import PolicyMode, UnknownReleaseAction

_gate: ModelAgeGate | None = None


def _build_gate() -> ModelAgeGate:
    """Build ModelAgeGate from environment configuration."""
    sources = []
    if os.getenv("LLM_REGISTRY_USE_OPENROUTER", "true").lower() == "true":
        sources.append(OpenRouterSource())
    if os.getenv("LLM_REGISTRY_USE_MODELS_DEV", "true").lower() == "true":
        sources.append(ModelsDevSource())
    if os.getenv("LLM_REGISTRY_USE_OPENAI", "false").lower() == "true":
        sources.append(OpenAIProviderSource(os.getenv("OPENAI_API_KEY", "")))
    if os.getenv("LLM_REGISTRY_USE_ANTHROPIC", "false").lower() == "true":
        sources.append(AnthropicProviderSource(os.getenv("ANTHROPIC_API_KEY", "")))

    cache_path = Path(
        os.getenv("LLM_REGISTRY_CACHE_PATH", "/tmp/redsl_registry.json")
    )

    agg = RegistryAggregator(
        sources=sources,
        cache_path=cache_path,
        cache_ttl=int(os.getenv("LLM_REGISTRY_CACHE_TTL_SECONDS", "21600")),
        stale_grace=int(os.getenv("LLM_REGISTRY_CACHE_STALE_GRACE_SECONDS", "604800")),
        disagreement_threshold_days=int(
            os.getenv("LLM_POLICY_SOURCE_DISAGREEMENT_DAYS", "14")
        ),
    )

    fallback_map = dict(
        pair.split(":")
        for pair in os.getenv("LLM_MODEL_FALLBACK_MAP", "").split(",")
        if ":" in pair
    )

    return ModelAgeGate(
        aggregator=agg,
        mode=os.getenv("LLM_POLICY_MODE", "frontier_lag"),
        max_age_days=int(os.getenv("LLM_POLICY_MAX_AGE_DAYS", "180")),
        strict=os.getenv("LLM_POLICY_STRICT", "true").lower() == "true",
        unknown_action=os.getenv("LLM_POLICY_UNKNOWN_RELEASE", "deny"),
        min_sources_agree=int(os.getenv("LLM_POLICY_MIN_SOURCES_AGREE", "2")),
        blocklist=set(filter(None, os.getenv("LLM_MODEL_BLOCKLIST", "").split(","))),
        allowlist=set(filter(None, os.getenv("LLM_MODEL_ALLOWLIST", "").split(","))),
        fallback_map=fallback_map,
    )


def get_gate() -> ModelAgeGate:
    """Get or create the global ModelAgeGate singleton."""
    global _gate
    if _gate is None:
        _gate = _build_gate()
    return _gate


def safe_completion(model: str, **kwargs):
    """Drop-in replacement for litellm.completion with policy enforcement.

    Usage:
        from redsl.llm import safe_completion
        response = safe_completion(model="gpt-4o", messages=[...])

    Raises:
        ModelRejectedError: If model violates age/lifecycle policy (strict mode)
    """
    from litellm import completion

    decision = get_gate().check(model)
    if not decision.allowed:
        raise ModelRejectedError(decision.reason)
    return completion(model=decision.model, **kwargs)


def check_model_policy(model: str) -> dict:
    """Check if a model is allowed without making an LLM call.

    Returns dict with: allowed, model, reason, age_days, sources_used.
    """
    decision = get_gate().check(model)
    return {
        "allowed": decision.allowed,
        "model": decision.model,
        "reason": decision.reason,
        "age_days": decision.age_days,
        "sources_used": list(decision.sources_used),
    }


def list_allowed_models() -> list[str]:
    """List all models currently allowed by policy."""
    return get_gate().list_allowed()
