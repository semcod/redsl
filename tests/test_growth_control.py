"""Tests for the redsl.autonomy.growth_control module."""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_git_project(tmp_path: Path) -> Path:
    """Create a minimal git-initialized Python project."""
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), capture_output=True)

    # Create a simple Python file
    pkg = tmp_path / "mymod"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "core.py").write_text(textwrap.dedent("""\
        def hello():
            return "world"

        def add(a, b):
            return a + b
    """))

    # Initial commit
    subprocess.run(["git", "add", "-A"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=str(tmp_path), capture_output=True, check=True)
    return tmp_path


# ===========================================================================
# growth_control.py
# ===========================================================================

class TestGrowthControl:
    def test_growth_budget_defaults(self) -> None:
        from redsl.autonomy.growth_control import GrowthBudget

        b = GrowthBudget()
        assert b.max_file_size == 400
        assert b.max_total_growth_per_week == 2000

    def test_find_oversized_files(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.growth_control import GrowthController, GrowthBudget

        # Create a big file
        big = tmp_git_project / "mymod" / "big.py"
        big.write_text("\n".join(f"x_{i} = {i}" for i in range(500)))

        gc = GrowthController(GrowthBudget(max_file_size=100))
        warnings = gc.check_growth(tmp_git_project)
        oversized = [w for w in warnings if "big.py" in w]
        assert len(oversized) >= 1

    def test_find_tiny_modules(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.growth_control import GrowthController

        # Create several tiny files
        for i in range(12):
            (tmp_git_project / "mymod" / f"tiny_{i}.py").write_text(f"x = {i}\n")

        gc = GrowthController()
        suggestions = gc.suggest_consolidation(tmp_git_project)
        consolidate = [s for s in suggestions if s["action"] == "consolidate_tiny_modules"]
        assert len(consolidate) >= 1

    def test_module_budget_check(self, tmp_path: Path) -> None:
        from redsl.autonomy.growth_control import check_module_budget

        # Create a bridge-type file that exceeds limits
        bridge = tmp_path / "my_bridge.py"
        source = "\n".join(f"import mod_{i}" for i in range(20))
        source += "\n" + "\n".join(f"def fn_{i}(): pass" for i in range(12))
        bridge.write_text(source)

        violations = check_module_budget(bridge, module_type="bridge")
        # Should trigger at least the functions or imports limit
        assert len(violations) >= 1

    def test_module_budget_infer_type(self) -> None:
        from redsl.autonomy.growth_control import _infer_module_type

        assert _infer_module_type(Path("regix_bridge.py")) == "bridge"
        assert _infer_module_type(Path("toon_parser.py"))