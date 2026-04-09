"""
Tests covering:
  1. DirectRefactorEngine bug fixes:
     - EXTRACT_CONSTANTS: insertion after multi-line imports
     - FIX_MODULE_EXECUTION_BLOCK: assignments NOT moved into __main__ guard
  2. pyqual_bridge unit + integration tests
  3. planfile_bridge unit + integration tests
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from redsl.refactors.direct import DirectRefactorEngine
from redsl.refactors import ReturnTypeAdder as PackageReturnTypeAdder
from redsl.refactors import UnusedImportRemover as PackageUnusedImportRemover
from redsl.refactors.ast_transformers import ReturnTypeAdder as ModuleReturnTypeAdder
from redsl.refactors.ast_transformers import UnusedImportRemover as ModuleUnusedImportRemover
from redsl.validation import pyqual_bridge
from redsl.commands.planfile_bridge import (
    create_ticket,
    is_available as planfile_available,
    list_tickets,
    report_refactor_results,
)

REDSL_ROOT = Path(__file__).parent.parent / "redsl"

skip_if_pyqual_missing = pytest.mark.skipif(
    not pyqual_bridge.is_available(), reason="pyqual not installed"
)
skip_if_planfile_missing = pytest.mark.skipif(
    not planfile_available(), reason="planfile not installed"
)


# ---------------------------------------------------------------------------
# AST transformer export compatibility
# ---------------------------------------------------------------------------


class TestAstTransformerExports:
    def test_package_reexports_match_module_exports(self):
        assert PackageReturnTypeAdder is ModuleReturnTypeAdder
        assert PackageUnusedImportRemover is ModuleUnusedImportRemover


# ---------------------------------------------------------------------------
# DirectRefactorEngine — EXTRACT_CONSTANTS bug fix
# ---------------------------------------------------------------------------

class TestExtractConstantsMultiLineImport:
    """extract_constants must not inject code inside multi-line import blocks."""

    @pytest.fixture()
    def engine(self) -> DirectRefactorEngine:
        return DirectRefactorEngine()

    def _write(self, tmp_path: Path, code: str) -> Path:
        p = tmp_path / "src.py"
        p.write_text(code)
        return p

    def test_insert_after_multiline_import_is_valid_python(self, tmp_path, engine):
        code = (
            "from foo import (\n"
            "    Alpha,\n"
            "    Beta,\n"
            ")\n"
            "from pathlib import Path\n"
            "\n"
            "def work(x):\n"
            "    return x * 42\n"
        )
        p = self._write(tmp_path, code)
        engine.extract_constants(p, [(8, 42)])
        result = p.read_text()
        import ast
        ast.parse(result)  # must not raise

    def test_constants_inserted_after_all_imports(self, tmp_path, engine):
        code = (
            "from foo import (\n"
            "    Alpha,\n"
            ")\n"
            "import os\n"
            "\n"
            "def f(n):\n"
            "    if n > 99:\n"
            "        return n * 50\n"
            "    return n + 75\n"
        )
        p = self._write(tmp_path, code)
        engine.extract_constants(p, [(7, 99), (8, 50), (9, 75)])
        result = p.read_text()
        # Constant definition must appear AFTER all imports
        import_end = max(result.find("import os"), result.find(")"))
        const_pos = result.find("CONSTANT_99")
        assert const_pos > import_end

    def test_magic_numbers_are_replaced_in_source(self, tmp_path, engine):
        code = (
            "from x import (\n"
            "    A,\n"
            "    B,\n"
            ")\n"
            "\n"
            "LIMIT = 50\n"
            "\n"
            "def calc(n):\n"
            "    if n > 50:\n"
            "        return n * 30\n"
            "    return 1024\n"
        )
        p = self._write(tmp_path, code)
        engine.extract_constants(p, [(9, 50), (10, 30), (11, 1024)])
        result = p.read_text()
        assert "CONSTANT_50" in result
        assert "CONSTANT_30" in result
        assert "CONSTANT_1024" in result
        assert "if n > CONSTANT_50" in result

    def test_single_line_imports_still_work(self, tmp_path, engine):
        code = "import os\nimport sys\n\ndef f(x):\n    if x > 42:\n        return x * 99\n    return x + 77\n"
        p = self._write(tmp_path, code)
        engine.extract_constants(p, [(5, 42), (6, 99), (7, 77)])
        result = p.read_text()
        import ast
        ast.parse(result)
        assert "CONSTANT_42" in result

    def test_no_constants_when_fewer_than_3_magic_numbers(self, tmp_path, engine):
        code = "import os\n\ndef f(x):\n    return x * 42\n"
        p = self._write(tmp_path, code)
        changed = engine.extract_constants(p, [(4, 42)])
        assert changed is False
        assert "CONSTANT" not in p.read_text()


# ---------------------------------------------------------------------------
# DirectRefactorEngine — REMOVE_UNUSED_IMPORTS regression
# ---------------------------------------------------------------------------


class TestRemoveUnusedImportsMultiLineImport:
    """Multiline imports must keep the `import` keyword after cleanup."""

    @pytest.fixture()
    def engine(self) -> DirectRefactorEngine:
        return DirectRefactorEngine()

    def test_multiline_from_import_keeps_import_keyword(self, tmp_path, engine):
        code = (
            "from foo import (\n"
            "    Alpha,\n"
            "    Beta,\n"
            ")\n"
            "\n"
            "def work(x):\n"
            "    return Alpha + x\n"
        )
        p = tmp_path / "src.py"
        p.write_text(code)

        changed = engine.remove_unused_imports(p, ["Beta"])

        assert changed is True
        result = p.read_text()
        assert "from foo import (" in result
        assert "Beta" not in result
        import ast
        ast.parse(result)


# ---------------------------------------------------------------------------
# DirectRefactorEngine — FIX_MODULE_EXECUTION_BLOCK bug fix
# ---------------------------------------------------------------------------

class TestFixModuleExecutionBlock:
    """Assignments must NOT be moved into __main__ guard."""

    @pytest.fixture()
    def engine(self) -> DirectRefactorEngine:
        return DirectRefactorEngine()

    def _write(self, tmp_path: Path, code: str) -> Path:
        p = tmp_path / "src.py"
        p.write_text(code)
        return p

    def test_assignments_are_not_guarded(self, tmp_path, engine):
        code = (
            "import typer\n"
            "app = typer.Typer()\n"
            "TaskPattern = dict\n"
            "\n"
            "@app.command()\n"
            "def run() -> None:\n"
            "    pass\n"
        )
        p = self._write(tmp_path, code)
        changed = engine.fix_module_execution_block(p)
        assert changed is False
        assert "if __name__" not in p.read_text()

    def test_alias_assignment_not_guarded(self, tmp_path, engine):
        code = "from strategy import Strategy\nStrategyV2 = Strategy\n"
        p = self._write(tmp_path, code)
        changed = engine.fix_module_execution_block(p)
        assert changed is False

    def test_bare_call_at_module_level_is_guarded(self, tmp_path, engine):
        code = "def main() -> None:\n    pass\n\nmain()\n"
        p = self._write(tmp_path, code)
        changed = engine.fix_module_execution_block(p)
        assert changed is True
        result = p.read_text()
        assert 'if __name__ == "__main__"' in result
        import ast
        ast.parse(result)

    def test_call_already_in_main_guard_not_double_wrapped(self, tmp_path, engine):
        code = (
            "def main() -> None:\n    pass\n\n"
            'if __name__ == "__main__":\n    main()\n'
        )
        p = self._write(tmp_path, code)
        changed = engine.fix_module_execution_block(p)
        assert changed is False

    def test_result_always_valid_python(self, tmp_path, engine):
        code = "def setup() -> None:\n    pass\n\nsetup()\n"
        p = self._write(tmp_path, code)
        engine.fix_module_execution_block(p)
        import ast
        ast.parse(p.read_text())


# ---------------------------------------------------------------------------
# DirectRefactorEngine — ADD_RETURN_TYPES coverage
# ---------------------------------------------------------------------------


class TestAddReturnTypes:
    @pytest.fixture()
    def engine(self) -> DirectRefactorEngine:
        return DirectRefactorEngine()

    def test_multiline_signature_gets_return_annotation(self, tmp_path, engine):
        code = (
            "def compute(\n"
            "    x,\n"
            "    y,\n"
            "):\n"
            "    if x > y:\n"
            "        return 1\n"
            "    return 1\n"
        )
        p = tmp_path / "src.py"
        p.write_text(code)

        changed = engine.add_return_types(p, [("compute", 1)])

        assert changed is True
        result = p.read_text()
        assert "-> int" in result
        import ast
        ast.parse(result)


# ---------------------------------------------------------------------------
# pyqual_bridge — unit tests
# ---------------------------------------------------------------------------

class TestPyqualBridgeUnit:
    def test_is_available_returns_bool(self):
        assert isinstance(pyqual_bridge.is_available(), bool)

    def test_check_gates_returns_dict_when_unavailable(self):
        with patch("redsl.validation.pyqual_bridge.is_available", return_value=False):
            result = pyqual_bridge.check_gates(Path("/tmp"))
        assert result["passed"] is True
        assert result["available"] is False

    def test_doctor_returns_empty_when_unavailable(self):
        with patch("redsl.validation.pyqual_bridge.is_available", return_value=False):
            result = pyqual_bridge.doctor(Path("/tmp"))
        assert result == {}

    def test_validate_config_returns_true_when_unavailable(self):
        with patch("redsl.validation.pyqual_bridge.is_available", return_value=False):
            valid, msg = pyqual_bridge.validate_config(Path("/tmp"))
        assert valid is True

    def test_check_gates_handles_timeout_gracefully(self):
        with patch("redsl.validation.pyqual_bridge.is_available", return_value=True), \
             patch("subprocess.run", side_effect=subprocess.TimeoutExpired("pyqual", 60)):
            result = pyqual_bridge.check_gates(Path("/tmp"))
        assert result["passed"] is True
        assert result.get("timed_out") is True

    def test_check_gates_structure(self):
        mock_proc = MagicMock(returncode=0, stdout="All gates PASSED\n", stderr="")
        with patch("redsl.validation.pyqual_bridge.is_available", return_value=True), \
             patch("subprocess.run", return_value=mock_proc):
            result = pyqual_bridge.check_gates(Path("/tmp"))
        assert "passed" in result
        assert "gates" in result
        assert result["available"] is True

    def test_check_gates_parses_unicode_rows(self):
        mock_proc = MagicMock(
            returncode=1,
            stdout="✅ cc: 5.5 ≤ 15\n❌ coverage: 10.0 ≥ 20\n",
            stderr="",
        )
        with patch("redsl.validation.pyqual_bridge.is_available", return_value=True), \
             patch("subprocess.run", return_value=mock_proc):
            result = pyqual_bridge.check_gates(Path("/tmp"))
        assert result["passed"] is False
        assert len(result["gates"]) == 2
        assert result["gates"][0]["passed"] is True
        assert result["gates"][1]["passed"] is False

    def test_validate_config_passes_fix_flag(self):
        mock_proc = MagicMock(returncode=0, stdout="ok", stderr="")
        with patch("redsl.validation.pyqual_bridge.is_available", return_value=True), \
             patch("subprocess.run", return_value=mock_proc) as run_mock:
            valid, _ = pyqual_bridge.validate_config(Path("/tmp"), fix=True)
        assert valid is True
        args = run_mock.call_args.args[0]
        assert "--fix" in args
        assert args[:2] == ["pyqual", "validate"]

    def test_run_pipeline_parses_iterations_push_and_publish(self):
        mock_proc = MagicMock(
            returncode=0,
            stdout=(
                "iterations:\n"
                "- iteration: 1\n"
                "  stages:\n"
                "  - name: push\n"
                "    status: passed\n"
                "  - name: publish\n"
                "    status: passed\n"
            ),
            stderr="",
        )
        with patch("redsl.validation.pyqual_bridge.is_available", return_value=True), \
             patch("subprocess.run", return_value=mock_proc):
            result = pyqual_bridge.run_pipeline(Path("/tmp"), fix_config=True)
        assert result["passed"] is True
        assert result["iterations"] == 1
        assert result["push_passed"] is True
        assert result["publish_passed"] is True

    def test_git_helpers_return_unavailable_when_missing(self):
        with patch("redsl.validation.pyqual_bridge.is_available", return_value=False):
            commit = pyqual_bridge.git_commit(Path("/tmp"), "msg")
            push = pyqual_bridge.git_push(Path("/tmp"))
        assert commit["committed"] is False
        assert commit["available"] is False
        assert push["pushed"] is False
        assert push["available"] is False


# ---------------------------------------------------------------------------
# pyqual_bridge — integration tests
# ---------------------------------------------------------------------------

class TestPyqualBridgeIntegration:
    @skip_if_pyqual_missing
    def test_doctor_returns_dict(self):
        result = pyqual_bridge.doctor(REDSL_ROOT.parent)
        assert isinstance(result, dict)

    @skip_if_pyqual_missing
    def test_check_gates_returns_bool_passed(self):
        result = pyqual_bridge.check_gates(REDSL_ROOT.parent)
        assert "passed" in result
        assert isinstance(result["passed"], bool)

    @skip_if_pyqual_missing
    def test_validate_config_returns_bool(self):
        valid, msg = pyqual_bridge.validate_config(REDSL_ROOT.parent)
        assert isinstance(valid, bool)
        assert isinstance(msg, str)

    @skip_if_pyqual_missing
    def test_is_available_consistent(self):
        assert pyqual_bridge.is_available() is True


# ---------------------------------------------------------------------------
# planfile_bridge — unit tests
# ---------------------------------------------------------------------------

class TestPlanfileBridgeUnit:
    def test_is_available_returns_bool(self):
        assert isinstance(planfile_available(), bool)

    def test_create_ticket_returns_unavailable_when_missing(self):
        with patch("redsl.commands.planfile_bridge.is_available", return_value=False):
            result = create_ticket(Path("/tmp"), "T", "D")
        assert result["created"] is False
        assert result["available"] is False

    def test_list_tickets_returns_empty_when_unavailable(self):
        with patch("redsl.commands.planfile_bridge.is_available", return_value=False):
            result = list_tickets(Path("/tmp"))
        assert result == []

    def test_report_refactor_results_graceful_when_unavailable(self):
        with patch("redsl.commands.planfile_bridge.is_available", return_value=False):
            result = report_refactor_results(
                Path("/tmp"), decisions_applied=3,
                files_modified=["a.py", "b.py"],
                avg_cc_before=12.0, avg_cc_after=8.0,
            )
        assert result["created"] is False

    def test_create_ticket_handles_subprocess_error(self):
        with patch("redsl.commands.planfile_bridge.is_available", return_value=True), \
             patch("subprocess.run", side_effect=Exception("boom")):
            result = create_ticket(Path("/tmp"), "T", "D")
        assert result["created"] is False
        assert "error" in result

    def test_create_ticket_handles_timeout(self):
        with patch("redsl.commands.planfile_bridge.is_available", return_value=True), \
             patch("subprocess.run", side_effect=subprocess.TimeoutExpired("planfile", 15)):
            result = create_ticket(Path("/tmp"), "T", "D")
        assert result["timed_out"] is True


# ---------------------------------------------------------------------------
# planfile_bridge — integration tests
# ---------------------------------------------------------------------------

class TestPlanfileBridgeIntegration:
    @skip_if_planfile_missing
    def test_is_available_consistent(self):
        assert planfile_available() is True

    @skip_if_planfile_missing
    def test_list_tickets_returns_list(self):
        result = list_tickets(REDSL_ROOT.parent)
        assert isinstance(result, list)

    @skip_if_planfile_missing
    def test_report_refactor_results_is_dict(self):
        result = report_refactor_results(
            REDSL_ROOT.parent,
            decisions_applied=2,
            files_modified=["orchestrator.py"],
            avg_cc_before=10.0,
            avg_cc_after=8.0,
        )
        assert isinstance(result, dict)
        assert "created" in result
