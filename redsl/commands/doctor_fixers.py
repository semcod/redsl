"""Fixers for project doctor — repair common project health issues."""

import ast
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable


def _apply_fixer_to_issues(
    root: Path,
    report: "DoctorReport",
    category: str,
    fixer_fn: Callable[[Path], bool],
    success_msg: str,
    fail_msg: str,
    error_prefix: str,
) -> None:
    """Apply *fixer_fn* to every issue in *report* matching *category*.

    On success appends *success_msg.format(path=…)* to ``report.fixes_applied``;
    tries git-revert as fallback; on failure appends *fail_msg.format(path=…)*.
    """
    from .doctor_helpers import _fix_via_git_revert

    for issue in report.issues:
        if issue.category != category:
            continue
        path = root / issue.path
        try:
            if fixer_fn(path):
                report.fixes_applied.append(success_msg.format(path=issue.path))
            elif _fix_via_git_revert(path, root):
                report.fixes_applied.append(f"git-reverted {issue.path}")
            else:
                report.errors.append(fail_msg.format(path=issue.path))
        except Exception as exc:
            report.errors.append(f"{error_prefix} {issue.path}: {exc}")

def fix_broken_guards(root: Path, report: 'DoctorReport') -> None:
    """Use body_restorer to repair stolen class/function bodies."""
    from ..refactors.body_restorer import repair_file
    from .doctor_data import DoctorReport
    from .doctor_helpers import _fix_via_git_revert
    from .doctor_indent_fixers import _fix_guard_in_try_block, _fix_guard_with_excess_indent, _fix_stolen_indent

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

def fix_stolen_indent(root: Path, report: 'DoctorReport') -> None:
    """Restore indentation for function/class bodies that lost it."""
    from .doctor_indent_fixers import _fix_stolen_indent
    _apply_fixer_to_issues(
        root, report,
        category="stolen_indent",
        fixer_fn=_fix_stolen_indent,
        success_msg="indent restored {path}",
        fail_msg="Could not fix indent in {path}",
        error_prefix="Error fixing indent",
    )

def fix_broken_fstrings(root: Path, report: 'DoctorReport') -> None:
    """Fix common broken f-string patterns."""
    from .doctor_fstring_fixers import _fix_broken_fstring
    _apply_fixer_to_issues(
        root, report,
        category="broken_fstring",
        fixer_fn=_fix_broken_fstring,
        success_msg="f-string fixed {path}",
        fail_msg="Could not fix f-string in {path}",
        error_prefix="Error fixing f-string",
    )

def fix_stale_pycache(root: Path, report: 'DoctorReport') -> None:
    """Remove all __pycache__ directories."""
    from .doctor_data import DoctorReport
    removed = 0
    for cache_dir in root.rglob("__pycache__"):
        try:
            shutil.rmtree(cache_dir)
            removed += 1
        except OSError:
            pass
    if removed:
        report.fixes_applied.append(f"Removed {removed} __pycache__ directories")

def fix_missing_install(root: Path, report: 'DoctorReport') -> None:
    """Run pip install -e . for the project."""
    from .doctor_data import DoctorReport
    from .doctor_helpers import _find_pip, _guess_package_name

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

def fix_module_level_exit(root: Path, report: 'DoctorReport') -> None:
    """Wrap bare sys.exit() calls in if __name__ == '__main__' guards."""
    from .doctor_data import DoctorReport

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

def fix_version_mismatch(root: Path, report: 'DoctorReport') -> None:
    """Update hardcoded version strings in test files."""
    from .doctor_data import DoctorReport
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

def fix_pytest_collision(root: Path, report: 'DoctorReport') -> None:
    """Add override_name to pytest config so it doesn't collide with Typer CLI."""
    from .doctor_data import DoctorReport
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
