"""Tests for redsl.commands.doctor module."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from redsl.commands.doctor import (
    Issue,
    DoctorReport,
    detect_broken_guards,
    detect_stolen_indent,
    detect_broken_fstrings,
    detect_stale_pycache,
    detect_version_mismatch,
    detect_module_level_exit,
    fix_broken_guards,
    fix_stolen_indent,
    fix_broken_fstrings,
    fix_version_mismatch,
    fix_module_level_exit,
    diagnose,
    heal,
    _fix_guard_in_try_block,
    _fix_stolen_indent,
    _fix_broken_fstring,
    _escape_fstring_body_braces,
    _is_fstring_expr,
)


class TestDetectors:
    def test_detect_broken_guard(self, tmp_path: Path) -> None:
        py = tmp_path / "bad.py"
        py.write_text(textwrap.dedent("""\
            class Foo:
                pass
            if __name__ == "__main__":
                x = 1
            except ImportError:
                pass
        """))
        issues = detect_broken_guards(tmp_path)
        assert len(issues) == 1
        assert issues[0].category == "broken_guard"

    def test_no_broken_guard_on_valid(self, tmp_path: Path) -> None:
        py = tmp_path / "ok.py"
        py.write_text("x = 1\n")
        assert detect_broken_guards(tmp_path) == []

    def test_detect_stolen_indent(self, tmp_path: Path) -> None:
        py = tmp_path / "bad.py"
        py.write_text(textwrap.dedent("""\
            async def run():
            \"\"\"Docs.\"\"\"
            port = 8080
        """))
        issues = detect_stolen_indent(tmp_path)
        assert len(issues) >= 1
        assert issues[0].category == "stolen_indent"

    def test_detect_broken_fstring(self, tmp_path: Path) -> None:
        py = tmp_path / "bad.py"
        py.write_text('x = f"http://host}:{port}"\n')
        issues = detect_broken_fstrings(tmp_path)
        assert len(issues) == 1
        assert issues[0].category == "broken_fstring"

    def test_detect_stale_pycache(self, tmp_path: Path) -> None:
        for i in range(55):
            (tmp_path / f"pkg{i}" / "__pycache__").mkdir(parents=True)
        issues = detect_stale_pycache(tmp_path)
        assert len(issues) == 1
        assert issues[0].category == "stale_cache"

    def test_detect_version_mismatch(self, tmp_path: Path) -> None:
        (tmp_path / "VERSION").write_text("2.0.0")
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "__init__.py").write_text("")
        (tests / "test_ver.py").write_text(
            'from pkg import __version__\ndef test_v():\n    assert ver == "1.0.0"\n'
        )
        issues = detect_version_mismatch(tmp_path)
        assert len(issues) == 1
        assert "1.0.0" in issues[0].description

    def test_detect_module_level_exit(self, tmp_path: Path) -> None:
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "__init__.py").write_text("")
        (tests / "test_exit.py").write_text("import sys\nsys.exit(main())\n")
        issues = detect_module_level_exit(tmp_path)
        assert len(issues) == 1
        assert issues[0].category == "module_level_exit"

    def test_skip_faulty_py(self, tmp_path: Path) -> None:
        py = tmp_path / "faulty.py"
        py.write_text('if __name__ == "__main__":\n    print "bad"\n')
        assert detect_broken_guards(tmp_path) == []


class TestFixers:
    def test_fix_guard_in_try_block(self, tmp_path: Path) -> None:
        py = tmp_path / "config.py"
        py.write_text(textwrap.dedent("""\
            try:
                from dotenv import load_dotenv
            if __name__ == "__main__":
                load_dotenv()
            except ImportError:
                pass
        """))
        assert _fix_guard_in_try_block(py)
        src = py.read_text()
        assert "if __name__" not in src
        assert "load_dotenv()" in src
        assert "except ImportError" in src
        # Should now parse cleanly
        import ast
        ast.parse(src)

    def test_fix_stolen_indent(self, tmp_path: Path) -> None:
        py = tmp_path / "server.py"
        py.write_text(textwrap.dedent("""\
            import os

            async def run_rest_server():
            \"\"\"Run as REST API server.\"\"\"
            port = int(os.getenv('PORT', '8081'))
            app = create_rest_api()
        """))
        assert _fix_stolen_indent(py)
        src = py.read_text()
        import ast
        ast.parse(src)
        assert '    """Run as REST API server."""' in src
        assert "    port = int" in src

    def test_fix_broken_fstring(self, tmp_path: Path) -> None:
        py = tmp_path / "main.py"
        py.write_text(textwrap.dedent("""\
            host = "0.0.0.0"
            port = 8080
            url = f"http://host}:{port}"
        """))
        assert _fix_broken_fstring(py)
        src = py.read_text()
        import ast
        ast.parse(src)
        assert "{host}" in src

    def test_fix_version_mismatch(self, tmp_path: Path) -> None:
        (tmp_path / "VERSION").write_text("2.0.0")
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "__init__.py").write_text("")
        test_file = tests / "test_ver.py"
        test_file.write_text('def test_v():\n    assert ver == "1.0.0"\n')

        report = DoctorReport(project="test")
        report.issues.append(Issue(
            category="version_mismatch",
            path="tests/test_ver.py",
            description="Line 2: asserts '1.0.0' but VERSION is '2.0.0'",
        ))
        fix_version_mismatch(tmp_path, report)
        assert len(report.fixes_applied) == 1
        assert '"2.0.0"' in test_file.read_text()

    def test_fix_module_level_exit(self, tmp_path: Path) -> None:
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "__init__.py").write_text("")
        test_file = tests / "test_exit.py"
        test_file.write_text("import sys\n\nsys.exit(main())\n")

        report = DoctorReport(project="test")
        report.issues.append(Issue(
            category="module_level_exit",
            path="tests/test_exit.py",
            description="Bare sys.exit() at line 3",
        ))
        fix_module_level_exit(tmp_path, report)
        assert len(report.fixes_applied) == 1
        src = test_file.read_text()
        assert 'if __name__ == "__main__":' in src


    def test_fix_multiline_fstring_braces(self, tmp_path: Path) -> None:
        py = tmp_path / "executor.py"
        py.write_text(textwrap.dedent("""\
            def build():
                template = f'''
            class Foo:
                def __init__(self):
                    self._data = {}
                    self._config = {}

                def run(self, x):
                    return {action.get('name', 'default')}
            '''
                return template
        """))
        assert _fix_broken_fstring(py)
        src = py.read_text()
        import ast
        ast.parse(src)
        assert "{{}}" in src  # escaped empty dict
        assert "{action.get" in src  # preserved valid interpolation

    def test_escape_fstring_body_preserves_valid_expr(self) -> None:
        body = "hello {name}, data = {}\n"
        result = _escape_fstring_body_braces(body)
        assert "{name}" in result
        assert "{{}}" in result

    def test_is_fstring_expr(self) -> None:
        assert _is_fstring_expr("name")
        assert _is_fstring_expr("action.get('x', 'y')")
        assert not _is_fstring_expr("")
        assert not _is_fstring_expr("   ")


class TestOrchestrator:
    def test_diagnose_empty(self, tmp_path: Path) -> None:
        (tmp_path / "tests").mkdir()
        report = diagnose(tmp_path)
        assert report.healthy

    def test_heal_dry_run(self, tmp_path: Path) -> None:
        (tmp_path / "tests").mkdir()
        (tmp_path / "VERSION").write_text("1.0.0")
        tests = tmp_path / "tests"
        (tests / "__init__.py").write_text("")
        (tests / "test_v.py").write_text(
            '# Reads VERSION\nassert x == "0.9.0"\n'
        )

        report = heal(tmp_path, dry_run=True)
        assert len(report.issues) >= 1
        assert len(report.fixes_applied) == 0

    def test_report_summary_dict(self) -> None:
        report = DoctorReport(project="test")
        report.issues.append(Issue("cat", "path", "desc"))
        report.fixes_applied.append("fixed something")
        d = report.summary_dict()
        assert d["issues_found"] == 1
        assert d["fixes_applied"] == 1
