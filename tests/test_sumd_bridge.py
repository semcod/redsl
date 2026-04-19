"""Tests for sumd_bridge integration."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from redsl.analyzers.sumd_bridge import (
    HAS_SUMD,
    SumdAnalyzer,
    SumdMetrics,
    _parse_map_metrics,
    analyze_with_sumd,
)


class TestSumdAnalyzer:
    """Test native SumdAnalyzer implementation."""

    def test_analyze_empty_project(self, tmp_path: Path) -> None:
        """Test analyzing empty project."""
        analyzer = SumdAnalyzer()
        metrics = analyzer.analyze(tmp_path)

        assert isinstance(metrics, SumdMetrics)
        assert metrics.total_files == 0
        assert metrics.total_lines == 0
        assert metrics.cc_mean == 0.0

    def test_analyze_python_project(self, tmp_path: Path) -> None:
        """Test analyzing project with Python files."""
        # Create a simple Python module
        pkg_dir = tmp_path / "mypkg"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text('"""My package."""\n', encoding="utf-8")

        module = pkg_dir / "module.py"
        module.write_text(
            '''
def simple_func():
    """Simple function."""
    return 1

def complex_func(x):
    """Complex function with branches."""
    if x > 0:
        if x > 10:
            return "big"
        return "small"
    elif x < 0:
        return "negative"
    return "zero"

class MyClass:
    def method1(self):
        return 1
    def method2(self, x, y):
        return x + y
''',
            encoding="utf-8",
        )

        analyzer = SumdAnalyzer()
        metrics = analyzer.analyze(tmp_path)

        assert metrics.total_files == 2  # __init__.py, module.py
        assert metrics.total_functions >= 2
        assert metrics.total_classes >= 1
        assert metrics.cc_mean > 0

    def test_generate_map_toon(self, tmp_path: Path) -> None:
        """Test generating map.toon.yaml content."""
        # Create a simple Python module
        pkg_dir = tmp_path / "mypkg"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("# init", encoding="utf-8")

        module = pkg_dir / "utils.py"
        module.write_text(
            '''
def helper():
    """Helper function."""
    return True
''',
            encoding="utf-8",
        )

        analyzer = SumdAnalyzer()
        content = analyzer.generate_map_toon(tmp_path)

        # Header contains project name and stats
        assert "# " in content and "|" in content
        assert "M[" in content
        assert "D:" in content
        assert "helper()" in content or "utils.py" in content

    def test_cc_calculation(self, tmp_path: Path) -> None:
        """Test cyclomatic complexity calculation."""
        pkg_dir = tmp_path / "testpkg"
        pkg_dir.mkdir()

        module = pkg_dir / "complex.py"
        module.write_text(
            '''
def low_cc():
    return 1

def medium_cc(x):
    if x > 0:
        return 1
    return 0

def high_cc(x, y):
    if x > 0 and y > 0:
        if x > 10:
            return "big"
        return "small"
    elif x < 0:
        return "negative"
    elif y < 0:
        return "y-negative"
    return "zero"
''',
            encoding="utf-8",
        )

        analyzer = SumdAnalyzer()
        metrics = analyzer.analyze(tmp_path)

        # high_cc has multiple branches - should contribute to CC
        assert metrics.cc_mean >= 1.0
        assert metrics.total_functions >= 3


class TestAnalyzeWithSumd:
    """Test the analyze_with_sumd convenience function."""

    def test_analyze_empty(self, tmp_path: Path) -> None:
        """Test analyze_with_sumd on empty project."""
        result = analyze_with_sumd(tmp_path)

        assert result["available"] is True
        assert "map_content" in result
        assert "metrics" in result
        assert result["source"] in ("oqlos.sumd", "native")

    def test_analyze_with_python_files(self, tmp_path: Path) -> None:
        """Test analyze_with_sumd on project with Python files."""
        pkg_dir = tmp_path / "testpkg"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("# init\n", encoding="utf-8")

        module = pkg_dir / "calc.py"
        module.write_text(
            '''
def add(a, b):
    return a + b

def multiply(a, b):
    result = 0
    for _ in range(b):
        result = add(result, a)
    return result
''',
            encoding="utf-8",
        )

        result = analyze_with_sumd(tmp_path)

        assert result["available"] is True
        assert result["metrics"]["files"] >= 2
        assert result["metrics"]["functions"] >= 2
        assert result["metrics"]["cc_mean"] >= 1.0


class TestParseMapMetrics:
    """Test _parse_map_metrics helper."""

    def test_parse_valid_header(self) -> None:
        """Test parsing valid map header."""
        content = """# testproj | 10f 500L | py:10 | 2024-01-01
# stats: 25 func | 5 cls | 10 mod | CC̄=3.50 | critical:2
# alerts: high-cc func=15
# hotspots: big_func fan=20
"""
        metrics = _parse_map_metrics(content)

        assert metrics.get("functions") == 25
        assert metrics.get("classes") == 5
        assert metrics.get("modules") == 10
        assert metrics.get("cc_mean") == 3.50
        assert metrics.get("critical") == 2

    def test_parse_empty_content(self) -> None:
        """Test parsing empty content."""
        metrics = _parse_map_metrics("")
        assert metrics == {}

    def test_parse_without_stats_line(self) -> None:
        """Test parsing content without stats line."""
        content = """# testproj | 10f 500L | py:10 | 2024-01-01
M[10]:
  file.py,100
"""
        metrics = _parse_map_metrics(content)
        assert metrics == {}


class TestSumdIntegration:
    """Integration tests for sumd bridge."""

    def test_detects_multiple_languages(self, tmp_path: Path) -> None:
        """Test detecting multiple programming languages."""
        # Create files in different languages
        (tmp_path / "script.py").write_text("print('hello')\n", encoding="utf-8")
        (tmp_path / "app.js").write_text("console.log('hello');\n", encoding="utf-8")
        (tmp_path / "main.go").write_text('package main\nfunc main() {}\n', encoding="utf-8")

        analyzer = SumdAnalyzer()
        metrics = analyzer.analyze(tmp_path)

        # Should detect at least 3 files
        assert metrics.total_files >= 3

        # Check map content includes all languages
        content = analyzer.generate_map_toon(tmp_path)
        assert "py:" in content or "js:" in content or "go:" in content

    def test_skips_ignored_directories(self, tmp_path: Path) -> None:
        """Test that ignored directories are skipped."""
        # Create files in ignored and non-ignored directories
        (tmp_path / "main.py").write_text("print('main')\n", encoding="utf-8")

        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        (venv_dir / "ignored.py").write_text("# should be ignored\n", encoding="utf-8")

        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "cached.pyc").write_bytes(b"cached")

        analyzer = SumdAnalyzer()
        metrics = analyzer.analyze(tmp_path)

        # Should only count main.py
        assert metrics.total_files == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
