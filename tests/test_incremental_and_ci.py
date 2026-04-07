"""Tests for Phase 2.1 (AST context), 2.4 (incremental analysis) and 3.1 (CI/CD)."""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import patch

import pytest

from redsl.analyzers import (
    CodeAnalyzer,
    ast_max_nesting_depth,
    get_changed_files,
    IncrementalAnalyzer,
    EvolutionaryCache,
)
from redsl.ci import generate_github_workflow, install_github_workflow


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2.1 — ast_max_nesting_depth
# ─────────────────────────────────────────────────────────────────────────────

class TestAstMaxNestingDepth:
    def _parse_func(self, src: str) -> ast.FunctionDef:
        tree = ast.parse(src)
        return tree.body[0]

    def test_flat_function_depth_zero(self):
        src = "def f():\n    return 1\n"
        node = self._parse_func(src)
        assert ast_max_nesting_depth(node) == 0

    def test_single_if_depth_one(self):
        src = "def f(x):\n    if x:\n        return 1\n"
        node = self._parse_func(src)
        assert ast_max_nesting_depth(node) == 1

    def test_nested_if_for_depth_two(self):
        src = "def f(x):\n    if x:\n        for i in x:\n            pass\n"
        node = self._parse_func(src)
        assert ast_max_nesting_depth(node) == 2

    def test_nested_function_not_counted(self):
        src = (
            "def outer(x):\n"
            "    if x:\n"
            "        pass\n"
            "    def inner():\n"
            "        for i in range(10):\n"
            "            if i:\n"
            "                pass\n"
        )
        node = self._parse_func(src)
        # outer has only 1 if — inner's nesting should NOT be counted
        assert ast_max_nesting_depth(node) == 1

    def test_try_except_counts(self):
        src = "def f():\n    try:\n        pass\n    except Exception:\n        pass\n"
        node = self._parse_func(src)
        assert ast_max_nesting_depth(node) >= 1


class TestIsPublicApiAndNestedDepth:
    def test_high_cc_public_func_sets_is_public_api(self, tmp_path: Path):
        """Publiczne funkcje z CC>10 powinny mieć is_public_api=True."""
        # Build a file with a high-CC public function
        lines = ["def process(x):"]
        for i in range(12):
            lines.append(f"    if x == {i}:")
            lines.append(f"        return {i}")
        lines.append("    return -1")
        code = "\n".join(lines)
        (tmp_path / "module.py").write_text(code)

        analyzer = CodeAnalyzer()
        result = analyzer.analyze_project(tmp_path)

        func_metrics = [m for m in result.metrics if m.function_name == "process"]
        assert func_metrics, "Expected metrics for 'process'"
        assert func_metrics[0].is_public_api is True

    def test_private_func_not_public_api(self, tmp_path: Path):
        """Prywatne funkcje (_prefix) z CC>10 nie powinny mieć is_public_api=True."""
        lines = ["def _internal(x):"]
        for i in range(12):
            lines.append(f"    if x == {i}:")
            lines.append(f"        return {i}")
        lines.append("    return -1")
        code = "\n".join(lines)
        (tmp_path / "module.py").write_text(code)

        analyzer = CodeAnalyzer()
        result = analyzer.analyze_project(tmp_path)

        func_metrics = [m for m in result.metrics if m.function_name == "_internal"]
        assert func_metrics, "Expected metrics for '_internal'"
        assert func_metrics[0].is_public_api is False

    def test_nested_depth_populated(self, tmp_path: Path):
        """nested_depth powinien być > 0 dla funkcji z zagnieżdżeniami."""
        lines = ["def complex_func(x, y):"]
        for i in range(5):
            lines.append(f"    if x == {i}:")
            lines.append(f"        for j in range({i+2}):")
            lines.append(f"            if j > {i}:")
            lines.append(f"                return j")
        lines.append("    return 0")
        code = "\n".join(lines)
        (tmp_path / "module.py").write_text(code)

        analyzer = CodeAnalyzer()
        result = analyzer.analyze_project(tmp_path)

        func_metrics = [m for m in result.metrics if m.function_name == "complex_func"]
        assert func_metrics, "Expected metrics for 'complex_func'"
        assert func_metrics[0].nested_depth >= 2


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2.4 — get_changed_files
# ─────────────────────────────────────────────────────────────────────────────

class TestGetChangedFiles:
    def test_returns_empty_when_git_fails(self, tmp_path: Path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = "not a git repo"
            result = get_changed_files(tmp_path)
        assert result == []

    def test_returns_existing_py_files(self, tmp_path: Path):
        (tmp_path / "foo.py").write_text("x = 1\n")
        (tmp_path / "bar.py").write_text("y = 2\n")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "foo.py\nbar.py\nbaz.py\n"  # baz.py doesn't exist
            result = get_changed_files(tmp_path)

        assert len(result) == 2
        names = {f.name for f in result}
        assert names == {"foo.py", "bar.py"}

    def test_ignores_non_py_files(self, tmp_path: Path):
        (tmp_path / "module.py").write_text("x = 1\n")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "module.py\nREADME.md\nsetup.cfg\n"
            result = get_changed_files(tmp_path)

        assert len(result) == 1
        assert result[0].name == "module.py"


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2.4 — EvolutionaryCache
# ─────────────────────────────────────────────────────────────────────────────

class TestEvolutionaryCache:
    def test_cache_miss_on_empty(self, tmp_path: Path):
        cache = EvolutionaryCache(tmp_path)
        (tmp_path / "foo.py").write_text("x = 1")
        assert cache.get(tmp_path / "foo.py") is None

    def test_cache_hit_after_set(self, tmp_path: Path):
        cache = EvolutionaryCache(tmp_path)
        f = tmp_path / "foo.py"
        f.write_text("x = 1")
        metrics = {"file_path": "foo.py", "module_lines": 1}
        cache.set(f, metrics)
        result = cache.get(f)
        assert result == metrics

    def test_cache_stale_after_modification(self, tmp_path: Path):
        cache = EvolutionaryCache(tmp_path)
        f = tmp_path / "foo.py"
        f.write_text("x = 1")
        cache.set(f, {"file_path": "foo.py"})
        f.write_text("x = 999")  # modify
        assert cache.get(f) is None  # stale

    def test_cache_persists_across_instances(self, tmp_path: Path):
        f = tmp_path / "bar.py"
        f.write_text("y = 2")
        metrics = {"file_path": "bar.py", "module_lines": 1}

        c1 = EvolutionaryCache(tmp_path)
        c1.set(f, metrics)
        c1.save()

        c2 = EvolutionaryCache(tmp_path)
        assert c2.get(f) == metrics

    def test_invalidate_removes_entry(self, tmp_path: Path):
        cache = EvolutionaryCache(tmp_path)
        f = tmp_path / "foo.py"
        f.write_text("z = 3")
        cache.set(f, {"file_path": "foo.py"})
        cache.invalidate(f)
        assert cache.get(f) is None


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2.4 — IncrementalAnalyzer
# ─────────────────────────────────────────────────────────────────────────────

class TestIncrementalAnalyzer:
    def test_falls_back_to_full_analysis_when_no_changes(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("x = 1\n")
        analyzer = CodeAnalyzer()
        incremental = IncrementalAnalyzer(analyzer)

        with patch("redsl.analyzers.incremental.get_changed_files", return_value=[]):
            result = incremental.analyze_changed(tmp_path, use_cache=False)

        assert result is not None
        assert result.total_files >= 1

    def test_analyzes_only_changed_files(self, tmp_path: Path):
        f = tmp_path / "changed.py"
        f.write_text("def foo(x):\n    return x\n")
        (tmp_path / "unchanged.py").write_text("y = 42\n")

        analyzer = CodeAnalyzer()
        incremental = IncrementalAnalyzer(analyzer)

        with patch("redsl.analyzers.incremental.get_changed_files", return_value=[f]):
            result = incremental.analyze_changed(tmp_path, use_cache=False)

        assert result is not None
        paths = {m.file_path for m in result.metrics}
        assert any("changed.py" in p for p in paths)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3.1 — GitHub Actions generator
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateGithubWorkflow:
    def test_produces_valid_yaml(self, tmp_path: Path):
        import yaml
        content = generate_github_workflow(tmp_path)
        parsed = yaml.safe_load(content)
        assert "jobs" in parsed
        assert "redsl-analyze" in parsed["jobs"]

    def test_includes_checkout_step(self, tmp_path: Path):
        content = generate_github_workflow(tmp_path)
        assert "actions/checkout" in content

    def test_includes_quality_gates_check(self, tmp_path: Path):
        content = generate_github_workflow(tmp_path)
        assert "quality gates" in content.lower() or "QUALITY GATES" in content

    def test_custom_python_version(self, tmp_path: Path):
        content = generate_github_workflow(tmp_path, config={"python_version": "3.12"})
        assert "3.12" in content

    def test_custom_max_cc_gate(self, tmp_path: Path):
        content = generate_github_workflow(tmp_path, config={"max_avg_cc": 7.5})
        assert "7.5" in content

    def test_install_creates_workflow_file(self, tmp_path: Path):
        output = install_github_workflow(tmp_path)
        assert output.exists()
        assert output.name == "redsl.yml"
        assert output.parent.name == "workflows"

    def test_install_does_not_overwrite_by_default(self, tmp_path: Path):
        output = install_github_workflow(tmp_path)
        original_content = output.read_text()
        output.write_text("# custom content")
        install_github_workflow(tmp_path)  # should not overwrite
        assert output.read_text() == "# custom content"

    def test_install_overwrites_when_requested(self, tmp_path: Path):
        output = install_github_workflow(tmp_path)
        output.write_text("# custom content")
        install_github_workflow(tmp_path, overwrite=True)
        assert "actions/checkout" in output.read_text()
