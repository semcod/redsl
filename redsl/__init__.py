"""ReDSL — Refactor + DSL + Self-Learning. LLM-powered autonomous code refactoring."""

__version__ = "1.2.6"

from .orchestrator import RefactorOrchestrator
from .config import AgentConfig

__all__ = ["RefactorOrchestrator", "AgentConfig", "__version__"]
