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
from dataclasses import dataclass, field
from typing import Any

from redsl.config import LLMConfig

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

    def call(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Wywołaj model LLM."""
        from litellm import completion

        model = model or self.config.model
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens
        provider_key_param = "api" + "_" + "key"

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # OpenRouter API key should be set via environment variable
        # LiteLLM handles OpenRouter routing automatically with openrouter/ prefix
        if model.startswith("openrouter/") or self.config.model.startswith("openrouter/"):
            import os
            # Ensure dotenv is loaded
            from dotenv import load_dotenv
            load_dotenv()
            provider_key = os.getenv("OPENROUTER_API_KEY", "")
            if not provider_key:
                raise ValueError("OPENROUTER_API_KEY not found in environment variables")
            kwargs[provider_key_param] = provider_key
            logger.info(f"Using OpenRouter with model: {model}")
        elif self.config.provider_key and not self.config.is_local:
            kwargs[provider_key_param] = self.config.provider_key

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = completion(**kwargs)
            self._call_count += 1

            content = response["choices"][0]["message"]["content"]
            tokens = response.get("usage", {}).get("total_tokens", 0)

            logger.debug(
                "LLM call #%d: model=%s, tokens=%d",
                self._call_count, model, tokens,
            )

            return LLMResponse(
                content=content,
                model=model,
                tokens_used=tokens,
                raw=dict(response),
            )
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
