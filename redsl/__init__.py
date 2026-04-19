"""ReDSL — Refactor + DSL + Self-Learning. LLM-powered autonomous code refactoring."""

__version__ = "1.2.33"

from .orchestrator import RefactorOrchestrator
from .config import AgentConfig
from .awareness import AwarenessManager, SelfModel

__all__ = [
    "RefactorOrchestrator",
    "AgentConfig",
    "AwarenessManager",
    "SelfModel",
    "__version__",
]
