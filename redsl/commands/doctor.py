"""Project doctor — diagnose and repair common project health issues.

Detects and fixes:
  - broken ``if __name__`` guards (syntax errors from bad refactoring)
  - stale ``__pycache__`` directories causing import mismatches
  - missing package installations (editable-install candidates)
  - module-level ``sys.exit()`` calls outside ``if __name__`` guards
  - hardcoded version assertions that drift from VERSION files
  - missing symbol exports in ``__init__.py``
  - pytest / Typer CLI collisions
"""

from __future__ import annotations

import ast
import logging
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .doctor_detectors import detect_stolen_indent
from .doctor_fstring_fixers import _escape_fstring_body_braces, _fix_broken_fstring, _is_fstring_expr
from .doctor_indent_fixers import _fix_guard_in_try_block, _fix_guard_with_excess_indent, _fix_stolen_indent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Issue:
    """A single detected issue."""
    category: str
    path: str
    description: str
    auto_fixable: bool = True

@dataclass
class DoctorReport:
    """Aggregated report for one project."""
    project: str
    issues: list[Issue] = field(default_factory=list)
    fixes_applied: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return not self.issues and not self.errors

    def summary_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "issues_found": len(self.issues),
            "fixes_applied": len(self.fixes_applied),
            "errors": len(self.errors),
            "healthy": self.healthy,
            "details": {
                "issues": [
                    {"category": i.category, "path": i.path, "description": i.description, "auto_fixable": i.auto_fixable}
                    for i in self.issues
                ],
                "fixes": self.fixes_applied,
                "errors": self.errors,
            },
        }


# ---------------------------------------------------------------------------
# Detectors
# ---------------------------------------------------------------------------

_GUARD_RE = re.compile(r'^if\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:\s*$')
_DEF_RE = re.compile(r'^(class|def|async\s+def|try)\s*')
_SKIP_DIRS = frozenset({
    "__pycache__", "venv", ".venv", ".tox", "node_modules",
    "build", "dist", ".git", ".eggs", "*.egg-info",
})


def _should_skip(path: Path) -> bool:
    return any(part in _SKIP_DIRS or part.endswith(".egg-info") for part in path.parts)


def _python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if not _should_skip(p))


_SKIP_EXAMPLE_FILES = frozenset({
    "faulty.py",  # intentionally broken examples (e.g. pactfix)
})


def detect_broken_guards(root: Path) -> list[Issue]:
    """Find Python files with syntax errors caused by misplaced ``if __name__`` guards."""
    issues: list[Issue] = []
    for py in _python_files(root):
        if py.name in _SKIP_EXAMPLE_FILES:
            continue
        try:
            src = py.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        try:
            ast.parse(src)
        except SyntaxError:
            # Check if there's a bare if __name__ guard that may be the cause
            for line in src.splitlines():
                if _GUARD_RE.match(line.strip()):
                    issues.append(Issue(
                        category="broken_guard",
                        path=str(py.relative_to(root)),
                        description="SyntaxError with if __name__ guard — likely stolen body",
                    ))
                    break
    return issues


def detect_broken_fstrings(root: Path) -> list[Issue]:
    """Find files with broken f-strings (single brace, missing open brace)."""
    issues: list[Issue] = []
    for py in _python_files(root):
        if py.name in _SKIP_EXAMPLE_FILES:
            continue
        try:
            src = py.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        try:
            ast.parse(src)
            continue
        except SyntaxError as exc:
            if exc.msg and ("f-string" in exc.msg or "single '}'" in exc.msg):
                issues.append(Issue(
                    category="broken_fstring",
                    path=str(py.relative_to(root)),
                    description=f"Line {exc.lineno}: {exc.msg}",
                ))
    return issues


def detect_stale_pycache(root: Path) -> list[Issue]:
    """Find stale __pycache__ directories."""
    caches = list(root.rglob("__pycache__"))
    if len(caches) > 50:
        return [Issue(
            category="stale_cache",
            path="__pycache__",
            description=f"{len(caches)} __pycache__ directories found — may cause import mismatches",
        )]
    return []


def detect_missing_install(root: Path) -> list[Issue]:
    """Check whether the project's own package is importable."""
    pyproject = root / "pyproject.toml"
    setup_py = root / "setup.py"
    if not pyproject.exists() and not setup_py.exists():
        return []

    pkg_name = _guess_package_name(root)
    if not pkg_name:
        return []

    proc = subprocess.run(
        [sys.executable, "-c", f"import {pkg_name}"],
        capture_output=True, text=True, cwd=str(root), timeout=10,
    )
    if proc.returncode != 0:
        return [Issue(
            category="missing_install",
            path="pyproject.toml",
            description=f"Package '{pkg_name}' not importable — needs `pip install -e .`",
        )]
    return []


def detect_module_level_exit(root: Path) -> list[Issue]:
    """Find test files with bare ``sys.exit(...)`` outside ``if __name__`` guard."""
    issues: list[Issue] = []
    tests_dir = root / "tests"
    if not tests_dir.is_dir():
        return issues
    for py in _python_files(tests_dir):
        try:
            src = py.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(src)
        except (OSError, SyntaxError):
            continue
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                func = node.value.func
                if _is_sys_exit_call(func):
                    issues.append(Issue(
                        category="module_level_exit",
                        path=str(py.relative_to(root)),
                        description=f"Bare sys.exit() at line {node.lineno} — causes pytest SystemExit",
                    ))
    return issues


def detect_version_mismatch(root: Path) -> list[Issue]:
    """Find tests that hardcode a version string that differs from VERSION file."""
    issues: list[Issue] = []
    version_file = root / "VERSION"
    if not version_file.exists():
        return issues
    actual_version = version_file.read_text().strip()
    tests_dir = root / "tests"
    if not tests_dir.is_dir():
        return issues

    # Only match tests that directly read/import the project version:
    #   from pkg import __version__  / open("VERSION")
    #   assert __version__ == "x.y.z"
    #   assert ver == "x.y.z"
    # Ignore test fixtures that happen to contain version strings.
    version_ref_re = re.compile(
        r'(?:__version__|VERSION|open.*VERSION|read_text.*VERSION)',
    )
    version_assert_re = re.compile(
        r'assert\s+\w+\s*==\s*["\'](\d+\.\d+\.\d+)["\']'
    )
    for py in _python_files(tests_dir):
        if py.name == "test_doctor.py":
            continue
        try:
            src = py.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Only scan files that actually reference the project version
        if not version_ref_re.search(src):
            continue
        for lineno, line in enumerate(src.splitlines(), 1):
            m = version_assert_re.search(line)
            if m and m.group(1) != actual_version:
                issues.append(Issue(
                    category="version_mismatch",
                    path=str(py.relative_to(root)),
                    description=f"Line {lineno}: asserts '{m.group(1)}' but VERSION is '{actual_version}'",
                ))
    return issues


def detect_pytest_cli_collision(root: Path) -> list[Issue]:
    """Check if ``python -m pytest`` is hijacked by a Typer/Click CLI."""
    main_py = root / (root.name) / "__main__.py"
    if not main_py.exists():
        # Try src layout
        main_py = root / "src" / (root.name) / "__main__.py"
    if not main_py.exists():
        return []
    try:
        src = main_py.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    if "typer" in src.lower() or "click" in src.lower():
        # Verify by trying pytest --co
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "--co", "-q", "tests"],
            capture_output=True, text=True, cwd=str(root), timeout=10,
        )
        if proc.returncode != 0 and "No such command" in proc.stderr:
            return [Issue(
                category="pytest_collision",
                path=str(main_py.relative_to(root)),
                description="Typer/Click CLI intercepts pytest invocation",
            )]
    return []


# ---------------------------------------------------------------------------
# Fixers
# ---------------------------------------------------------------------------

def fix_broken_guards(root: Path, report: DoctorReport) -> None:
    """Use body_restorer to repair stolen class/function bodies."""
    from ..refactors.body_restorer import repair_file

    for issue in report.issues:
        if issue.category != "broken_guard":
            continue
        path = root / issue.path
        try:
            if repair_file(path):
                report.fixes_applied.append(f"body_restorer fixed {issue.path}")
            elif _fix_guard_in_try_block(path):
                report.fixes_applied.append(f"try-block guard fixed {issue.path}")
            elif _fix_guard_with_excess_indent(path):
                report.fixes_applied.append(f"guard+indent fixed {issue.path}")
            elif _fix_stolen_indent(path):
                report.fixes_applied.append(f"indent restored {issue.path}")
            elif _fix_via_git_revert(path, root):
                report.fixes_applied.append(f"git-reverted {issue.path}")
            else:
                report.errors.append(f"Could not auto-fix {issue.path}")
        except Exception as exc:
            report.errors.append(f"Error fixing {issue.path}: {exc}")


def fix_stolen_indent(root: Path, report: DoctorReport) -> None:
    """Restore indentation for function/class bodies that lost it."""
    for issue in report.issues:
        if issue.category != "stolen_indent":
            continue
        path = root / issue.path
        try:
            if _fix_stolen_indent(path):
                report.fixes_applied.append(f"indent restored {issue.path}")
            elif _fix_via_git_revert(path, root):
                report.fixes_applied.append(f"git-reverted {issue.path}")
            else:
                report.errors.append(f"Could not fix indent in {issue.path}")
        except Exception as exc:
            report.errors.append(f"Error fixing indent {issue.path}: {exc}")


def fix_broken_fstrings(root: Path, report: DoctorReport) -> None:
    """Fix common broken f-string patterns."""
    for issue in report.issues:
        if issue.category != "broken_fstring":
            continue
        path = root / issue.path
        try:
            if _fix_broken_fstring(path):
                report.fixes_applied.append(f"f-string fixed {issue.path}")
            elif _fix_via_git_revert(path, root):
                report.fixes_applied.append(f"git-reverted {issue.path}")
            else:
                report.errors.append(f"Could not fix f-string in {issue.path}")
        except Exception as exc:
            report.errors.append(f"Error fixing f-string {issue.path}: {exc}")


def fix_stale_pycache(root: Path, report: DoctorReport) -> None:
    """Remove all __pycache__ directories."""
    removed = 0
    for cache_dir in root.rglob("__pycache__"):
        try:
            shutil.rmtree(cache_dir)
            removed += 1
        except OSError:
            pass
    if removed:
        report.fixes_applied.append(f"Removed {removed} __pycache__ directories")


def fix_missing_install(root: Path, report: DoctorReport) -> None:
    """Run pip install -e . for the project."""
    for issue in report.issues:
        if issue.category != "missing_install":
            continue
        pip_str = _find_pip(root)
        cmd = pip_str.split() + ["install", "-e", "."]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True, text=True, cwd=str(root), timeout=120,
            )
            if proc.returncode == 0:
                report.fixes_applied.append(f"pip install -e . succeeded for {root.name}")
            elif "externally-managed" in proc.stderr:
                # Retry with --break-system-packages for system Python
                cmd_retry = cmd + ["--break-system-packages"]
                proc2 = subprocess.run(
                    cmd_retry,
                    capture_output=True, text=True, cwd=str(root), timeout=120,
                )
                if proc2.returncode == 0:
                    report.fixes_applied.append(f"pip install -e . succeeded for {root.name}")
                else:
                    report.errors.append(f"pip install -e . failed for {root.name}: {proc2.stderr[:200]}")
            else:
                report.errors.append(f"pip install -e . failed for {root.name}: {proc.stderr[:200]}")
        except Exception as exc:
            report.errors.append(f"pip install -e . error for {root.name}: {exc}")


def fix_module_level_exit(root: Path, report: DoctorReport) -> None:
    """Wrap bare sys.exit() calls in if __name__ == '__main__' guards."""
    for issue in report.issues:
        if issue.category != "module_level_exit":
            continue
        path = root / issue.path
        try:
            src = path.read_text(encoding="utf-8")
            lines = src.splitlines(keepends=True)
            new_lines: list[str] = []
            changed = False

            for line in lines:
                stripped = line.strip()
                if stripped.startswith("sys.exit(") and not any(
                    l.strip() == 'if __name__ == "__main__":' or l.strip() == "if __name__ == '__main__':"
                    for l in new_lines[-3:]
                ):
                    indent = len(line) - len(line.lstrip())
                    guard = " " * indent + 'if __name__ == "__main__":\n'
                    wrapped = " " * (indent + 4) + stripped + "\n"
                    new_lines.append(guard)
                    new_lines.append(wrapped)
                    changed = True
                else:
                    new_lines.append(line)

            if changed:
                path.write_text("".join(new_lines), encoding="utf-8")
                report.fixes_applied.append(f"Wrapped sys.exit() in guard: {issue.path}")
        except Exception as exc:
            report.errors.append(f"Error fixing {issue.path}: {exc}")


def fix_version_mismatch(root: Path, report: DoctorReport) -> None:
    """Update hardcoded version strings in test files."""
    version_file = root / "VERSION"
    if not version_file.exists():
        return
    actual_version = version_file.read_text().strip()

    for issue in report.issues:
        if issue.category != "version_mismatch":
            continue
        path = root / issue.path
        try:
            src = path.read_text(encoding="utf-8")
            # Replace old version assertions with dynamic version
            version_pattern = re.compile(
                r'(assert\s+.*==\s*["\'])(\d+\.\d+\.\d+)(["\'])'
            )
            new_src = version_pattern.sub(
                lambda m: m.group(1) + actual_version + m.group(3), src
            )
            if new_src != src:
                path.write_text(new_src, encoding="utf-8")
                report.fixes_applied.append(f"Updated version to {actual_version} in {issue.path}")
        except Exception as exc:
            report.errors.append(f"Error fixing {issue.path}: {exc}")


def fix_pytest_collision(root: Path, report: DoctorReport) -> None:
    """Add override_name to pytest config so it doesn't collide with Typer CLI."""
    for issue in report.issues:
        if issue.category != "pytest_collision":
            continue
        pyproject = root / "pyproject.toml"
        if not pyproject.exists():
            continue
        try:
            content = pyproject.read_text(encoding="utf-8")
            if "[tool.pytest.ini_options]" in content and "addopts" not in content:
                # Add --override-ini to force pytest to not go through __main__
                content = content.replace(
                    "[tool.pytest.ini_options]",
                    '[tool.pytest.ini_options]\naddopts = "-p no:cacheprovider"',
                )
                pyproject.write_text(content, encoding="utf-8")
                report.fixes_applied.append(f"Updated pytest config for {root.name}")
            # The real fix: ensure tests can be run directly
            # Create a conftest at project root level if missing
            root_conftest = root / "conftest.py"
            if not root_conftest.exists():
                root_conftest.write_text(
                    '"""Root conftest — ensures pytest collects from tests/ not package CLI."""\n',
                    encoding="utf-8",
                )
                report.fixes_applied.append(f"Created root conftest.py for {root.name}")
        except Exception as exc:
            report.errors.append(f"Error fixing pytest collision for {root.name}: {exc}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _guess_package_name(root: Path) -> str | None:
    """Guess the importable package name from the project directory."""
    # Try direct package: root/name/
    candidate = root / root.name
    if (candidate / "__init__.py").exists():
        return root.name
    # Try src layout: root/src/name/
    candidate = root / "src" / root.name
    if (candidate / "__init__.py").exists():
        return root.name
    # Try pyproject.toml [project] name
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        for line in pyproject.read_text().splitlines():
            m = re.match(r'^name\s*=\s*"([^"]+)"', line.strip())
            if m:
                return m.group(1).replace("-", "_")
    return None


def _is_sys_exit_call(func: ast.expr) -> bool:
    """Check if an AST node is sys.exit(...)."""
    if isinstance(func, ast.Attribute):
        return (
            isinstance(func.value, ast.Name)
            and func.value.id == "sys"
            and func.attr == "exit"
        )
    return False


def _find_pip(root: Path) -> str:
    """Find the best pip executable for a project."""
    for venv_name in (".venv", "venv"):
        venv_pip = root / venv_name / "bin" / "pip"
        if venv_pip.exists():
            try:
                proc = subprocess.run(
                    [str(venv_pip), "--version"],
                    capture_output=True, text=True, timeout=5,
                )
                if proc.returncode == 0:
                    return str(venv_pip)
            except (subprocess.TimeoutExpired, OSError):
                pass
    # Fallback: use sys.executable -m pip (most reliable)
    return f"{sys.executable} -m pip"


def _fix_via_git_revert(path: Path, root: Path) -> bool:
    """Last resort: revert a broken file to its git HEAD version if it parses."""
    rel = str(path.relative_to(root))
    try:
        proc = subprocess.run(
            ["git", "show", f"HEAD:{rel}"],
            capture_output=True, text=True, cwd=str(root), timeout=5,
        )
        if proc.returncode != 0:
            return False
        head_src = proc.stdout
        ast.parse(head_src)
        path.write_text(head_src, encoding="utf-8")
        return True
    except (subprocess.TimeoutExpired, SyntaxError, OSError):
        return False
# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

_DETECTORS = [
    detect_broken_guards,
    detect_stolen_indent,
    detect_broken_fstrings,
    detect_stale_pycache,
    detect_missing_install,
    detect_module_level_exit,
    detect_version_mismatch,
    detect_pytest_cli_collision,
]

_FIXERS = {
    "broken_guard": fix_broken_guards,
    "stolen_indent": fix_stolen_indent,
    "broken_fstring": fix_broken_fstrings,
    "stale_cache": fix_stale_pycache,
    "missing_install": fix_missing_install,
    "module_level_exit": fix_module_level_exit,
    "version_mismatch": fix_version_mismatch,
    "pytest_collision": fix_pytest_collision,
}


def diagnose(root: Path) -> DoctorReport:
    """Run all detectors on a project and return a report (no fixes applied)."""
    report = DoctorReport(project=root.name)
    for detector in _DETECTORS:
        try:
            issues = detector(root)
            report.issues.extend(issues)
        except Exception as exc:
            report.errors.append(f"Detector {detector.__name__} failed: {exc}")
    return report


def heal(root: Path, dry_run: bool = False) -> DoctorReport:
    """Diagnose and fix issues in a project."""
    report = diagnose(root)

    if dry_run or not report.issues:
        return report

    categories = {i.category for i in report.issues if i.auto_fixable}
    for category in categories:
        fixer = _FIXERS.get(category)
        if fixer:
            try:
                fixer(root, report)
            except Exception as exc:
                report.errors.append(f"Fixer {category} failed: {exc}")

    return report


def heal_batch(semcod_root: Path, dry_run: bool = False) -> list[DoctorReport]:
    """Run doctor on all semcod subprojects."""
    reports: list[DoctorReport] = []
    for project_dir in sorted(semcod_root.iterdir()):
        if not project_dir.is_dir():
            continue
        if not (project_dir / "tests").is_dir():
            continue
        logger.info("Doctor: %s", project_dir.name)
        report = heal(project_dir, dry_run=dry_run)
        reports.append(report)
    return reports
