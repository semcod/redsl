"""Growth control — prevent uncontrolled codebase expansion.

Enforces LOC budgets, per-module complexity budgets, and suggests
consolidation when the codebase grows too quickly.
"""

from __future__ import annotations

import ast
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

_SKIP_DIRS = frozenset({
    "__pycache__", "venv", ".venv", ".tox", "node_modules",
    "build", "dist", ".git", ".eggs",
})


def _should_skip(path: Path) -> bool:
    return any(part in _SKIP_DIRS or part.endswith(".egg-info") for part in path.parts)


def _python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if not _should_skip(p))


# ---------------------------------------------------------------------------
# Growth budget
# ---------------------------------------------------------------------------

@dataclass
class GrowthBudget:
    """LOC growth budget per iteration."""

    max_new_lines_per_commit: int = 300
    max_new_files_per_commit: int = 5
    max_file_size: int = 400
    max_total_growth_per_week: int = 2000
    require_test_for_new_module: bool = True


class GrowthController:
    """Enforce growth budgets on a project."""

    def __init__(self, budget: GrowthBudget | None = None) -> None:
        self.budget = budget or GrowthBudget()

    def check_growth(self, project_dir: Path) -> list[str]:
        """Return a list of warnings for budget violations."""
        project_dir = Path(project_dir).resolve()
        warnings: list[str] = []

        weekly_growth = self._measure_weekly_growth(project_dir)
        if weekly_growth > self.budget.max_total_growth_per_week:
            warnings.append(
                f"Weekly LOC growth: {weekly_growth} (budget: {self.budget.max_total_growth_per_week}). "
                f"Consider refactoring existing code instead of adding new."
            )

        if self.budget.require_test_for_new_module:
            untested = self._find_untested_new_modules(project_dir)
            for mod in untested:
                warnings.append(
                    f"New module {mod} has no corresponding test file."
                )

        oversized = self._find_oversized_files(project_dir)
        for f in oversized:
            split_count = f["lines"] // self.budget.max_file_size + 1
            warnings.append(
                f"{f['path']} has {f['lines']}L (budget: {self.budget.max_file_size}L). "
                f"Split into ~{split_count} modules."
            )

        return warnings

    def suggest_consolidation(self, project_dir: Path) -> list[dict]:
        """Suggest consolidation actions to reduce file sprawl."""
        project_dir = Path(project_dir).resolve()
        suggestions: list[dict] = []

        tiny = self._find_tiny_modules(project_dir)
        if len(tiny) > 10:
            suggestions.append({
                "action": "consolidate_tiny_modules",
                "description": f"{len(tiny)} modules under 30L — merge related ones",
                "candidates": [str(t) for t in tiny[:10]],
                "estimated_reduction": f"-{len(tiny) - 5} files",
            })

        prefix_groups = self._group_by_prefix(project_dir)
        for prefix, files in prefix_groups.items():
            if len(files) > 4:
                suggestions.append({
                    "action": "create_subpackage",
                    "description": f"{len(files)} files with prefix '{prefix}' — create {prefix}/ package",
                    "candidates": files,
                })

        return suggestions

    # ---- internal helpers ----

    def _measure_weekly_growth(self, project_dir: Path) -> int:
        """Measure LOC added in the last 7 days via git."""
        try:
            proc = subprocess.run(
                ["git", "log", "--since=7 days ago", "--format=", "--numstat"],
                capture_output=True, text=True, cwd=str(project_dir), timeout=15,
            )
            if proc.returncode != 0:
                return 0
            added = 0
            for line in proc.stdout.strip().splitlines():
                parts = line.split("\t")
                if len(parts) >= 2 and parts[0].isdigit():
                    added += int(parts[0])
            return added
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return 0

    def _find_untested_new_modules(self, project_dir: Path) -> list[str]:
        """Find Python modules added in the last week that lack a test file."""
        try:
            proc = subprocess.run(
                ["git", "log", "--since=7 days ago", "--diff-filter=A", "--name-only", "--format="],
                capture_output=True, text=True, cwd=str(project_dir), timeout=10,
            )
            if proc.returncode != 0:
                return []
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

        new_py = [
            f for f in proc.stdout.strip().splitlines()
            if f.endswith(".py") and not f.startswith("tests/") and "__init__" not in f
        ]
        untested: list[str] = []
        for f in new_py:
            stem = Path(f).stem
            test_patterns = [
                project_dir / "tests" / f"test_{stem}.py",
                project_dir / "tests" / f"{stem}_test.py",
            ]
            if not any(tp.exists() for tp in test_patterns):
                untested.append(f)
        return untested

    def _find_oversized_files(self, project_dir: Path) -> list[dict]:
        """Find files exceeding the budget size limit."""
        result: list[dict] = []
        for fp in _python_files(project_dir):
            try:
                lines = len(fp.read_text(encoding="utf-8", errors="replace").splitlines())
            except OSError:
                continue
            if lines > self.budget.max_file_size:
                result.append({
                    "path": str(fp.relative_to(project_dir)),
                    "lines": lines,
                })
        return result

    def _find_tiny_modules(self, project_dir: Path) -> list[Path]:
        """Find .py files with fewer than 30 lines (non-init)."""
        tiny: list[Path] = []
        for fp in _python_files(project_dir):
            if fp.name == "__init__.py":
                continue
            try:
                lines = len(fp.read_text(encoding="utf-8", errors="replace").splitlines())
            except OSError:
                continue
            if lines < 30:
                tiny.append(fp.relative_to(project_dir))
        return tiny

    def _group_by_prefix(self, project_dir: Path) -> dict[str, list[str]]:
        """Group files by common name prefix (e.g. doctor_*)."""
        groups: dict[str, list[str]] = {}
        for fp in _python_files(project_dir):
            parts = fp.stem.split("_", 1)
            if len(parts) < 2:
                continue
            prefix = parts[0]
            groups.setdefault(prefix, []).append(str(fp.relative_to(project_dir)))
        return groups


# ---------------------------------------------------------------------------
# Per-module complexity budget
# ---------------------------------------------------------------------------

@dataclass
class ModuleBudget:
    """Complexity budget for a single module."""

    max_lines: int = 300
    max_functions: int = 15
    max_cc_per_function: int = 10
    max_cc_mean: float = 5.0
    max_fan_out: int = 10
    max_imports: int = 15


BUDGETS: dict[str, ModuleBudget] = {
    "bridge": ModuleBudget(max_lines=250, max_functions=8, max_cc_per_function=8),
    "parser": ModuleBudget(max_lines=300, max_functions=20, max_cc_per_function=12),
    "engine": ModuleBudget(max_lines=400, max_functions=15, max_cc_per_function=10),
    "cli": ModuleBudget(max_lines=200, max_functions=10, max_cc_per_function=5),
    "model": ModuleBudget(max_lines=100, max_functions=5, max_cc_per_function=3),
    "default": ModuleBudget(),
}


def _infer_module_type(file_path: Path) -> str:
    """Heuristically infer the module type from its name."""
    name = file_path.stem.lower()
    if "bridge" in name:
        return "bridge"
    if "parser" in name:
        return "parser"
    if "engine" in name:
        return "engine"
    if name in ("cli", "__main__"):
        return "cli"
    if "model" in name or "data" in name:
        return "model"
    return "default"


def check_module_budget(
    file_path: Path,
    module_type: str | None = None,
) -> list[str]:
    """Check whether a module stays within its complexity budget."""
    file_path = Path(file_path)
    module_type = module_type or _infer_module_type(file_path)
    budget = BUDGETS.get(module_type, BUDGETS["default"])
    violations: list[str] = []

    try:
        source = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [f"Cannot read {file_path}"]

    lines = len(source.splitlines())
    if lines > budget.max_lines:
        violations.append(
            f"{file_path.name}: {lines}L > {budget.max_lines}L budget for '{module_type}'"
        )

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return violations

    functions = [
        n for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    if len(functions) > budget.max_functions:
        violations.append(
            f"{file_path.name}: {len(functions)} functions > {budget.max_functions} budget"
        )

    imports = [
        n for n in ast.walk(tree)
        if isinstance(n, (ast.Import, ast.ImportFrom))
    ]
    if len(imports) > budget.max_imports:
        violations.append(
            f"{file_path.name}: {len(imports)} imports > {budget.max_imports} budget"
        )

    return violations
