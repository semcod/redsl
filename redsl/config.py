"""Konfiguracja systemu refaktoryzacji."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


_DEFAULT_LLM_MODEL = "openrouter/openai/gpt-5-mini"
_DEFAULT_XAI_MODEL = "x-ai/grok-code-fast-1"


def _default_llm_model() -> str:
    explicit_model = os.getenv("LLM_MODEL") or os.getenv("REFACTOR_LLM_MODEL")
    if explicit_model:
        return explicit_model

    if os.getenv("OPENROUTER_API_KEY"):
        return _DEFAULT_LLM_MODEL
    if os.getenv("XAI_API_KEY"):
        return _DEFAULT_XAI_MODEL
    if os.getenv("OPENAI_API_KEY"):
        return "openai/gpt-5-mini"
    return _DEFAULT_LLM_MODEL


def _resolve_provider_key(model: str) -> str:
    normalized = model.lower()
    if normalized.startswith(("x-ai/", "xai/")):
        return os.getenv("XAI_API_KEY", "")
    if normalized.startswith("openrouter/"):
        return os.getenv("OPENROUTER_API_KEY", "")
    if normalized.startswith("openai/"):
        return os.getenv("OPENAI_API_KEY", "")
    return (
        os.getenv("OPENROUTER_API_KEY")
        or os.getenv("OPENAI_API_KEY", "")
        or os.getenv("XAI_API_KEY", "")
    )


@dataclass
class LLMConfig:
    """Konfiguracja warstwy LLM."""

    model: str = field(default_factory=_default_llm_model)
    temperature: float = 0.3
    max_tokens: int = 4096
    reflection_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL") or os.getenv("REFACTOR_LLM_MODEL") or _default_llm_model())
    reflection_temperature: float = 0.2
    provider_key: str = field(default_factory=lambda: _resolve_provider_key(_default_llm_model()))

    @property
    def is_local(self) -> bool:
        return self.model.startswith("ollama/")

    @property
    def api_key(self) -> str:
        return self.provider_key

    @api_key.setter
    def api_key(self, value: str) -> None:
        self.provider_key = value


@dataclass
class MemoryConfig:
    """Konfiguracja systemu pamięci."""

    persist_dir: Path = field(default_factory=lambda: Path("/tmp/refactor_memory"))
    episodic_collection: str = "refactor_episodic"
    semantic_collection: str = "refactor_semantic"
    procedural_collection: str = "refactor_procedural"
    max_recall: int = 5


@dataclass
class AnalyzerConfig:
    """Konfiguracja analizatora kodu."""

    cc_threshold: int = 15
    fan_out_threshold: int = 10
    god_module_lines: int = 400
    god_module_functions: int = 15
    duplicate_similarity: float = 0.95
    duplicate_min_lines: int = 10


@dataclass
class RefactorConfig:
    """Konfiguracja silnika refaktoryzacji."""

    max_patch_lines: int = 200
    dry_run: bool = True
    auto_approve: bool = False
    backup_enabled: bool = True
    max_iterations: int = 3
    reflection_rounds: int = 2
    output_dir: Path = field(default_factory=lambda: Path("./refactor_output"))


@dataclass
class AgentConfig:
    """Główna konfiguracja agenta."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    analyzer: AnalyzerConfig = field(default_factory=AnalyzerConfig)
    refactor: RefactorConfig = field(default_factory=RefactorConfig)

    identity: str = (
        "You are an autonomous code refactoring agent with memory and self-reflection. "
        "You analyze code quality metrics, identify improvement opportunities, and generate "
        "safe, behavior-preserving refactoring patches. You learn from past refactoring "
        "decisions and continuously improve your strategies."
    )

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Tworzenie konfiguracji z zmiennych środowiskowych."""
        model = _default_llm_model()
        return cls(
            llm=LLMConfig(
                model=model,
                reflection_model=os.getenv("REFACTOR_LLM_MODEL") or os.getenv("LLM_MODEL") or model,
                provider_key=_resolve_provider_key(model),
            ),
            refactor=RefactorConfig(
                dry_run=os.getenv("REFACTOR_DRY_RUN", "true").lower() == "true",
                auto_approve=os.getenv("REFACTOR_AUTO_APPROVE", "false").lower() == "true",
            ),
        )
