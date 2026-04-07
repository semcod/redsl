"""
Silnik refaktoryzacji — generowanie, walidacja i aplikowanie patchy.

Proces:
1. Na podstawie Decision z DSL Engine generuje prompt dla LLM
2. LLM zwraca propozycję zmian jako JSON + unified diff
3. Agent reflektuje nad propozycją (self-critique)
4. Walidacja: linter + testy + diff sanity check
5. Aplikacja patcha (lub zapis do review)

Backward compatibility re-exports - all symbols available from submodules.
"""

from __future__ import annotations

# Re-export all public symbols from submodules for backward compatibility
from .diff_manager import (
    create_checkpoint,
    generate_diff,
    preview_proposal,
    rollback_single_file,
    rollback_to_checkpoint,
)
from .engine import RefactorEngine
from .models import FileChange, RefactorProposal, RefactorResult

__all__ = [
    # Classes
    "RefactorEngine",
    "RefactorProposal",
    "FileChange",
    "RefactorResult",
    # Diff manager
    "generate_diff",
    "preview_proposal",
    "create_checkpoint",
    "rollback_to_checkpoint",
    "rollback_single_file",
]
