"""Konfiguracja systemu refaktoryzacji."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class LLMConfig:
    """Konfiguracja warstwy LLM."""

    model: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_tokens: int = 4096
    reflection_model: str = field(default_factory=lambda: os.getenv("REFACTOR_LLM_MODEL", "gpt-4o-mini"))
    reflection_temperature: float = 0.2
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY", ""))

    @property
    def is_local(self) -> bool:
        return self.model.startswith("ollama/")


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
        return cls(
            llm=LLMConfig(
                model=os.getenv("REFACTOR_LLM_MODEL", "gpt-4o-mini"),
                api_key=os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY", ""),
            ),
            refactor=RefactorConfig(
                dry_run=os.getenv("REFACTOR_DRY_RUN", "true").lower() == "true",
                auto_approve=os.getenv("REFACTOR_AUTO_APPROVE", "false").lower() == "true",
            ),
        )
