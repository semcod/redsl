"""
Modele danych dla silnika refaktoryzacji.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from redsl.dsl import Decision


@dataclass
class FileChange:
    """Zmiana w pojedynczym pliku."""

    file_path: str
    original_code: str = ""
    refactored_code: str = ""
    patch: str = ""
    description: str = ""


@dataclass
class RefactorProposal:
    """Propozycja refaktoryzacji wygenerowana przez LLM."""

    decision: Decision
    refactor_type: str
    summary: str
    changes: list[FileChange] = field(default_factory=list)
    rationale: str = ""
    confidence: float = 0.0
    reflection_notes: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class RefactorResult:
    """Wynik zastosowania refaktoryzacji."""

    proposal: RefactorProposal
    applied: bool = False
    validated: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
