"""Tests for Phase 2.2 (SemanticChunker) and Phase 3.3 (RuleGenerator)."""

from __future__ import annotations

from pathlib import Path

import pytest

from redsl.analyzers import SemanticChunk, SemanticChunker
from redsl.dsl import RuleGenerator, LearnedRule


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2.2 — SemanticChunker
# ─────────────────────────────────────────────────────────────────────────────

_SAMPLE_MODULE = '''\
"""Module docstring."""
import os
import sys
from pathlib import Path

CONSTANT = 42

class MyClass:
    """A class."""

    def simple_method(self):
        """Simple."""
        return 1

    def complex_method(self, x, y):
        """Complex method."""
        result = 0
        for i in range(x):
            if i % 2 == 0:
                result += i * os.path.sep.count("/")
        return result

def standalone_func(path: Path) -> str:
    """Standalone function using Path."""
    return str(path.resolve())

def _private_helper(n: int) -> int:
    return n * 2
'''


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    f = tmp_path / "sample.py"
    f.write_text(_SAMPLE_MODULE)
    return f


class TestSemanticChunkerBasic:
    def test_chunk_top_level_function(self, sample_file: Path):
        chunker = SemanticChunker()
        chunk = chunker.chunk_function(sample_file, "standalone_func")
        assert chunk is not None
        assert "standalone_func" in chunk.source
        assert chunk.target_function == "standalone_func"

    def test_chunk_method_in_class(self, sample_file: Path):
        chunker = SemanticChunker()
        chunk = chunker.chunk_function(sample_file, "complex_method")
        assert chunk is not None
        assert "complex_method" in chunk.source

    def test_returns_none_for_missing_function(self, sample_file: Path):
        chunker = SemanticChunker()
        chunk = chunker.chunk_function(sample_file, "nonexistent_func")
        assert chunk is None

    def test_returns_none_for_missing_file(self, tmp_path: Path):
        chunker = SemanticChunker()
        chunk = chunker.chunk_function(tmp_path / "missing.py", "foo")
        assert chunk is None

    def test_returns_none_for_syntax_error(self, tmp_path: Path):
        bad = tmp_path / "bad.py"
        bad.write_text("def broken(:\n    pass\n")
        chunker = SemanticChunker()
        assert chunker.chunk_function(bad, "broken") is None

    def test_chunk_includes_relevant_imports(self, sample_file: Path):
        chunker = SemanticChunker()
        chunk = chunker.chunk_function(sample_file, "standalone_func")
        assert chunk is not None
        assert "Path" in chunk.imports or "pathlib" in chunk.imports

    def test_chunk_excludes_irrelevant_imports(self, sample_file: Path):
        chunker = SemanticChunker()
        chunk = chunker.chunk_function(sample_file, "_private_helper")
        assert chunk is not None
        assert chunk.imports == "" or "sys" not in chunk.imports

    def test_chunk_includes_class_context_for_method(self, sample_file: Path):
        chunker = SemanticChunker()
        chunk = chunker.chunk_function(sample_file, "complex_method")
        assert chunk is not None
        assert "MyClass" in chunk.class_context

    def test_no_class_context_for_top_level_func(self, sample_file: Path):
        chunker = SemanticChunker()
        chunk = chunker.chunk_function(sample_file, "standalone_func")
        assert chunk is not None
        assert chunk.class_context == ""

    def test_file_path_stored(self, sample_file: Path):
        chunker = SemanticChunker()
        chunk = chunker.chunk_function(sample_file, "standalone_func")
        assert chunk is not None
        assert str(sample_file) == chunk.file_path


class TestSemanticChunkPrompt:
    def test_to_llm_prompt_contains_source(self, sample_file: Path):
        chunker = SemanticChunker()
        chunk = chunker.chunk_function(sample_file, "standalone_func")
        assert chunk is not None
        prompt = chunk.to_llm_prompt()
        assert "standalone_func" in prompt

    def test_to_llm_prompt_contains_imports(self, sample_file: Path):
        chunker = SemanticChunker()
        chunk = chunker.chunk_function(sample_file, "complex_method")
        assert chunk is not None
        chunk.imports = "import os"
        prompt = chunk.to_llm_prompt()
        assert "import os" in prompt

    def test_to_llm_prompt_notes_truncation(self, sample_file: Path):
        chunker = SemanticChunker()
        chunk = chunker.chunk_function(sample_file, "complex_method", max_lines=5)
        assert chunk is not None
        if chunk.truncated:
            prompt = chunk.to_llm_prompt()
            assert "truncated" in prompt.lower()


class TestSemanticChunkerFile:
    def test_chunk_file_returns_all_functions(self, sample_file: Path):
        chunker = SemanticChunker()
        chunks = chunker.chunk_file(sample_file)
        func_names = {c.target_function for c in chunks}
        assert "standalone_func" in func_names
        assert "_private_helper" in func_names

    def test_chunk_file_empty_on_syntax_error(self, tmp_path: Path):
        bad = tmp_path / "bad.py"
        bad.write_text("def broken(:\n")
        chunker = SemanticChunker()
        assert chunker.chunk_file(bad) == []


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3.3 — RuleGenerator
# ─────────────────────────────────────────────────────────────────────────────

_SAMPLE_HISTORY = [
    {"action": "EXTRACT_FUNCTIONS", "success": True, "details": {"cyclomatic_complexity": 18}},
    {"action": "EXTRACT_FUNCTIONS", "success": True, "details": {"cyclomatic_complexity": 22}},
    {"action": "EXTRACT_FUNCTIONS", "success": True, "details": {"cyclomatic_complexity": 16}},
    {"action": "EXTRACT_FUNCTIONS", "success": False, "details": {"cyclomatic_complexity": 8}},
    {"action": "SPLIT_MODULE", "success": True, "details": {"module_lines": 450}},
    {"action": "SPLIT_MODULE", "success": True, "details": {"module_lines": 600}},
    {"action": "SPLIT_MODULE", "success": True, "details": {"module_lines": 380}},
    {"action": "REMOVE_UNUSED_IMPORTS", "success": True, "details": {"unused_imports": 3}},
    {"action": "REMOVE_UNUSED_IMPORTS", "success": True, "details": {"unused_imports": 5}},
]


class TestRuleGeneratorFromHistory:
    def test_generates_rules_from_history(self):
        gen = RuleGenerator()
        rules = gen.generate_from_history(_SAMPLE_HISTORY, min_support=2)
        assert len(rules) > 0

    def test_generates_extract_functions_rule(self):
        gen = RuleGenerator()
        rules = gen.generate_from_history(_SAMPLE_HISTORY, min_support=2)
        actions = {r.action for r in rules}
        assert "EXTRACT_FUNCTIONS" in actions

    def test_generates_split_module_rule(self):
        gen = RuleGenerator()
        rules = gen.generate_from_history(_SAMPLE_HISTORY, min_support=2)
        actions = {r.action for r in rules}
        assert "SPLIT_MODULE" in actions

    def test_min_support_filters_rare_actions(self):
        gen = RuleGenerator()
        history = [{"action": "RARE_ACTION", "success": True, "details": {}} for _ in range(2)]
        rules = gen.generate_from_history(history, min_support=5)
        assert not any(r.action == "RARE_ACTION" for r in rules)

    def test_failed_refactors_not_counted(self):
        gen = RuleGenerator()
        history = [{"action": "EXTRACT_FUNCTIONS", "success": False, "details": {}} for _ in range(10)]
        rules = gen.generate_from_history(history, min_support=2)
        assert not any(r.action == "EXTRACT_FUNCTIONS" for r in rules)

    def test_rules_have_conditions(self):
        gen = RuleGenerator()
        rules = gen.generate_from_history(_SAMPLE_HISTORY, min_support=2)
        for rule in rules:
            assert len(rule.conditions) > 0

    def test_rules_sorted_by_priority(self):
        gen = RuleGenerator()
        rules = gen.generate_from_history(_SAMPLE_HISTORY, min_support=2)
        priorities = [r.priority for r in rules]
        assert priorities == sorted(priorities, reverse=True)

    def test_rule_support_count(self):
        gen = RuleGenerator()
        rules = gen.generate_from_history(_SAMPLE_HISTORY, min_support=2)
        ef_rules = [r for r in rules if r.action == "EXTRACT_FUNCTIONS"]
        assert ef_rules
        assert ef_rules[0].support == 3  # 3 successful EXTRACT_FUNCTIONS

    def test_learned_rule_to_yaml_dict(self):
        rule = LearnedRule(
            name="learned_extract_3obs",
            action="EXTRACT_FUNCTIONS",
            conditions=[{"metric": "cyclomatic_complexity", "operator": "gt", "value": 15}],
            priority=0.75,
            support=3,
            confidence=0.9,
        )
        d = rule.to_yaml_dict()
        assert d["name"] == "learned_extract_3obs"
        assert d["action"] == "EXTRACT_FUNCTIONS"
        assert d["_meta"]["support"] == 3
        assert len(d["conditions"]) == 1


class TestRuleGeneratorSaveLoad:
    def test_save_creates_yaml_file(self, tmp_path: Path):
        gen = RuleGenerator()
        rules = gen.generate_from_history(_SAMPLE_HISTORY, min_support=2)
        output = tmp_path / "config" / "learned_rules.yaml"
        gen.save(rules, output)
        assert output.exists()
        assert output.stat().st_size > 0

    def test_saved_yaml_is_loadable(self, tmp_path: Path):
        import yaml
        gen = RuleGenerator()
        rules = gen.generate_from_history(_SAMPLE_HISTORY, min_support=2)
        output = tmp_path / "learned_rules.yaml"
        gen.save(rules, output)

        with open(output) as f:
            data = yaml.safe_load(f)

        assert "learned_rules" in data
        assert len(data["learned_rules"]) == len(rules)

    def test_load_and_register_calls_dsl_engine(self, tmp_path: Path):
        from unittest.mock import MagicMock
        gen = RuleGenerator()
        rules = gen.generate_from_history(_SAMPLE_HISTORY, min_support=2)
        output = tmp_path / "rules.yaml"
        gen.save(rules, output)

        mock_engine = MagicMock()
        count = gen.load_and_register(output, mock_engine)
        assert count == len(rules)
        mock_engine.add_rules_from_yaml.assert_called_once()

    def test_load_and_register_returns_zero_for_missing_file(self, tmp_path: Path):
        gen = RuleGenerator()
        mock_engine = object()
        count = gen.load_and_register(tmp_path / "missing.yaml", mock_engine)
        assert count == 0


class TestRuleGeneratorNoMemory:
    def test_generate_returns_empty_without_memory(self):
        gen = RuleGenerator(memory=None)
        rules = gen.generate(min_support=1)
        assert rules == []
