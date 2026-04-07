"""Testy systemu pamięci — episodic, semantic, procedural."""

import pytest
from app.memory import AgentMemory, InMemoryCollection, MemoryEntry, MemoryLayer


def _make_inmemory_layer(name: str) -> MemoryLayer:
    """Tworzenie warstwy pamięci z in-memory fallback (bez ChromaDB)."""
    layer = MemoryLayer(name, "/tmp/test_memory")
    layer._collection = InMemoryCollection(name)
    return layer


class TestMemoryLayer:
    def test_store_and_recall(self):
        layer = _make_inmemory_layer("test_layer")
        layer.store(MemoryEntry(content="Test action: split function X"))
        layer.store(MemoryEntry(content="Test action: deduplicate module Y"))

        results = layer.recall("split function", limit=2)
        assert len(results) > 0

    def test_count(self):
        layer = _make_inmemory_layer("test_count")
        assert layer.count() == 0
        layer.store(MemoryEntry(content="entry 1"))
        assert layer.count() == 1


class TestAgentMemory:
    def setup_method(self):
        self.memory = AgentMemory("/tmp/test_agent_memory")
        # Force in-memory fallback
        self.memory.episodic._collection = InMemoryCollection("episodic")
        self.memory.semantic._collection = InMemoryCollection("semantic")
        self.memory.procedural._collection = InMemoryCollection("procedural")

    def test_remember_action(self):
        self.memory.remember_action(
            action="extract_functions",
            target="parser_rules.py:_extract_entities",
            result="Split into 4 smaller functions",
            success=True,
            details={"cc_before": 36, "cc_after": 8},
        )
        results = self.memory.recall_similar_actions("extract functions parser", limit=3)
        assert len(results) > 0

    def test_learn_pattern(self):
        self.memory.learn_pattern(
            pattern="extract_functions for CC>30",
            context="Worked well on deeply nested if/else chains",
            effectiveness=0.85,
        )
        results = self.memory.recall_patterns("high complexity functions", limit=3)
        assert len(results) > 0

    def test_store_strategy(self):
        self.memory.store_strategy(
            strategy_name="handle_god_module",
            steps=[
                "Identify responsibility clusters",
                "Extract routes to routes.py",
                "Extract business logic to services.py",
                "Create __init__.py with re-exports",
            ],
            tags=["structure", "split"],
        )
        results = self.memory.recall_strategies("split large module", limit=2)
        assert len(results) > 0

    def test_stats(self):
        stats = self.memory.stats()
        assert "episodic" in stats
        assert "semantic" in stats
        assert "procedural" in stats
