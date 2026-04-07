"""
System pamięci agenta — trzy warstwy:

1. EPISODIC  — historia refaktoryzacji (co zrobiłem, kiedy, jak poszło)
2. SEMANTIC  — wiedza o wzorcach i regułach (co działa, co nie)
3. PROCEDURAL — strategie i plany (jak podejść do danego typu problemu)

Używa ChromaDB jako vector store do similarity search.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Pojedynczy wpis w pamięci."""

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class MemoryLayer:
    """Warstwa pamięci oparta na ChromaDB."""

    def __init__(
        self,
        collection_name: str,
        persist_dir: str | Path = "/tmp/refactor_memory",
    ) -> None:
        self.collection_name = collection_name
        self.persist_dir = str(persist_dir)
        self._collection = None
        self._client = None

    def _get_collection(self):
        """Lazy init kolekcji ChromaDB."""
        if self._collection is None:
            try:
                import chromadb

                self._client = chromadb.PersistentClient(path=self.persist_dir)
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                )
                logger.info("Memory layer '%s' initialized", self.collection_name)
            except ImportError:
                logger.warning("chromadb not installed — using in-memory fallback")
                self._collection = InMemoryCollection(self.collection_name)
        return self._collection

    def store(self, entry: MemoryEntry) -> None:
        """Zapisz wpis do pamięci."""
        collection = self._get_collection()
        doc_id = f"{self.collection_name}_{datetime.now(timezone.utc).timestamp()}"

        metadata = {**entry.metadata, "timestamp": entry.timestamp}
        # ChromaDB wymaga prostych typów w metadata
        clean_meta = {
            k: str(v) if not isinstance(v, (str, int, float, bool)) else v
            for k, v in metadata.items()
        }

        collection.add(
            documents=[entry.content],
            metadatas=[clean_meta],
            ids=[doc_id],
        )
        logger.debug("Stored memory entry: %s", doc_id)

    def recall(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        """Przywołaj z pamięci wpisy podobne do zapytania."""
        collection = self._get_collection()

        results = collection.query(
            query_texts=[query],
            n_results=min(limit, collection.count() or 1),
        )

        entries = []
        if results and results["documents"]:
            for doc, meta in zip(
                results["documents"][0],
                results["metadatas"][0] if results["metadatas"] else [{}] * len(results["documents"][0]),
            ):
                entries.append(MemoryEntry(
                    content=doc,
                    metadata=dict(meta) if meta else {},
                    timestamp=meta.get("timestamp", "") if meta else "",
                ))

        return entries

    def count(self) -> int:
        """Liczba wpisów w pamięci."""
        collection = self._get_collection()
        return collection.count()

    def clear(self) -> None:
        """Wyczyść pamięć."""
        if self._client:
            try:
                self._client.delete_collection(self.collection_name)
                self._collection = None
                logger.info("Cleared memory layer '%s'", self.collection_name)
            except Exception:
                pass


class InMemoryCollection:
    """Fallback gdy ChromaDB nie jest dostępne."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._docs: list[dict] = []

    def add(self, documents, metadatas, ids):
        for doc, meta, doc_id in zip(documents, metadatas, ids):
            self._docs.append({"id": doc_id, "document": doc, "metadata": meta})

    def query(self, query_texts, n_results=5):
        # Prosty fallback — zwróć ostatnie N
        recent = self._docs[-n_results:]
        return {
            "documents": [[d["document"] for d in recent]],
            "metadatas": [[d["metadata"] for d in recent]],
        }

    def count(self):
        return len(self._docs)


# ---------------------------------------------------------------------------
# Trzy warstwy pamięci
# ---------------------------------------------------------------------------

class AgentMemory:
    """
    Kompletny system pamięci z trzema warstwami.

    - episodic: „co zrobiłem" — historia refaktoryzacji
    - semantic: „co wiem" — wzorce, reguły, lekcje
    - procedural: „jak to robić" — strategie, plany
    """

    def __init__(self, persist_dir: str | Path = "/tmp/refactor_memory") -> None:
        self.episodic = MemoryLayer("refactor_episodic", persist_dir)
        self.semantic = MemoryLayer("refactor_semantic", persist_dir)
        self.procedural = MemoryLayer("refactor_procedural", persist_dir)

    # -- Episodic: historia działań --

    def remember_action(
        self,
        action: str,
        target: str,
        result: str,
        success: bool,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Zapamiętaj wykonaną akcję refaktoryzacji."""
        content = (
            f"Action: {action}\n"
            f"Target: {target}\n"
            f"Result: {result}\n"
            f"Success: {success}"
        )
        self.episodic.store(MemoryEntry(
            content=content,
            metadata={
                "action": action,
                "target": target,
                "success": success,
                **(details or {}),
            },
        ))

    def recall_similar_actions(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        """Przywołaj podobne wcześniejsze akcje."""
        return self.episodic.recall(query, limit)

    # -- Semantic: wiedza --

    def learn_pattern(self, pattern: str, context: str, effectiveness: float) -> None:
        """Zapamiętaj wzorzec refaktoryzacji i jego skuteczność."""
        content = (
            f"Pattern: {pattern}\n"
            f"Context: {context}\n"
            f"Effectiveness: {effectiveness:.2f}"
        )
        self.semantic.store(MemoryEntry(
            content=content,
            metadata={"pattern": pattern, "effectiveness": effectiveness},
        ))

    def recall_patterns(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        """Przywołaj wzorce pasujące do sytuacji."""
        return self.semantic.recall(query, limit)

    # -- Procedural: strategie --

    def store_strategy(self, strategy_name: str, steps: list[str], tags: list[str] | None = None) -> None:
        """Zapamiętaj strategię refaktoryzacji."""
        content = (
            f"Strategy: {strategy_name}\n"
            f"Steps:\n" + "\n".join(f"  {i+1}. {s}" for i, s in enumerate(steps))
        )
        self.procedural.store(MemoryEntry(
            content=content,
            metadata={"strategy": strategy_name, "tags": json.dumps(tags or [])},
        ))

    def recall_strategies(self, query: str, limit: int = 3) -> list[MemoryEntry]:
        """Przywołaj strategie pasujące do sytuacji."""
        return self.procedural.recall(query, limit)

    # -- Statystyki --

    def stats(self) -> dict[str, int]:
        return {
            "episodic": self.episodic.count(),
            "semantic": self.semantic.count(),
            "procedural": self.procedural.count(),
        }
