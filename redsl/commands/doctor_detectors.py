"""Detectors for project doctor — identify common project health issues."""

import ast
import re
import subprocess
import sys
from pathlib import Path

from .doctor_data import Issue

_SKIP_DIRS = frozenset({
    "__pycache__", "venv", ".venv", ".tox", "node_modules",
    "build", "dist", ".git", ".eggs", "*.egg-info",
})

_GUARD_RE = re.compile(r"^if\s+__name__\s*==\s*[\"\']__main__[\"\']\s*:\s*$")
_DEF_RE = re.compile(r"^(class|def|async\s+def|try)\s*")

_SKIP_EXAMPLE_FILES = frozenset({
    "faulty.py",  # intentionally broken examples (e.g. pactfix)
})

def _should_skip(path: Path) -> bool:
    return any(part in _SKIP_DIRS or part.endswith(".egg-info") for part in path.parts)

def _python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if not _should_skip(p))


def _read_python_source(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _has_main_guard(lines: list[str]) -> bool:
    return any(_GUARD_RE.match(line.strip()) for line in lines)


def _next_non_blank_index(lines: list[str], start: int, stop: int) -> int | None:
    for idx in range(start, min(stop, len(lines))):
        if lines[idx].strip():
            return idx
    return None


def _stolen_indent_issue_for_header(lines: list[str], idx: int, rel: str) -> Issue | None:
    stripped = lines[idx].rstrip()
    if not (_DEF_RE.match(stripped) and stripped.endswith(":")):
        return None

    indent = len(lines[idx]) - len(lines[idx].lstrip())
    expected_body_indent = indent + 4
    next_idx = _next_non_blank_index(lines, idx + 1, idx + 5)
    if next_idx is None:
        return None

    next_line = lines[next_idx]
    actual_indent = len(next_line) - len(next_line.lstrip())
    if actual_indent <= indent and next_line.strip():
        return Issue(
            category="stolen_indent",
            path=rel,
            description=f"Line {idx + 1}: body after '{stripped[:60]}' not indented",
        )
    if actual_indent > expected_body_indent + 4:
        return Issue(
            category="stolen_indent",
            path=rel,
            description=f"Line {next_idx + 1}: excess indentation after '{stripped[:60]}'",
        )
    return None

def detect_broken_guards(root: Path) -> list['Issue']:
    """Find Python files with syntax errors caused by misplaced ``if __name__`` guards."""
    from .doctor_data import Issue
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

def detect_stolen_indent(root: Path) -> list[Issue]:
    """Find files where function/class body lost indentation after guard removal.

    Pattern (function body not indented):
        async def run_rest_server():
        \"""Run as REST ...\"""    ← should be indented
        port = ...

    Pattern (extra indent):
        def show_stats(...):
            \"""docs.\"""  
            from x import y
                summary = ...            ← extra indent level
    """
    issues: list[Issue] = []
    for py in _python_files(root):
        if py.name in _SKIP_EXAMPLE_FILES:
            continue
        src = _read_python_source(py)
        if src is None:
            continue

        try:
            ast.parse(src)
            continue  # No syntax error → skip
        except SyntaxError:
            pass

        lines = src.splitlines()
        rel = str(py.relative_to(root))
        if _has_main_guard(lines):
            continue

        for idx, line in enumerate(lines):
            issue = _stolen_indent_issue_for_header(lines, idx, rel)
            if issue is not None:
                issues.append(issue)
    return issues

def detect_broken_fstrings(root: Path) -> list['Issue']:
    """Find files with broken f-strings (single brace, missing open brace)."""
    from .doctor_data import Issue
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

def detect_stale_pycache(root: Path) -> list['Issue']:
    """Find stale __pycache__ directories."""
    from .doctor_data import Issue
    caches = list(root.rglob("__pycache__"))
    if len(caches) > 50:
        return [Issue(
            category="stale_cache",
            path="__pycache__",
            description=f"{len(caches)} __pycache__ directories found — may cause import mismatches",
        )]
    return []

def detect_missing_install(root: Path) -> list['Issue']:
    """Check whether the project's own package is importable."""
    from .doctor_data import Issue
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

def detect_module_level_exit(root: Path) -> list['Issue']:
    """Find test files with bare ``sys.exit(...)`` outside ``if __name__`` guard."""
    from .doctor_data import Issue
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

def detect_version_mismatch(root: Path) -> list['Issue']:
    """Find tests that hardcode a version string that differs from VERSION file."""
    from .doctor_data import Issue
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
        r'assert\\s+\\w+\\s*==\\s*["\'](\\d+\\.\\d+\\.\\d+)["\']'
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

def detect_pytest_cli_collision(root: Path) -> list['Issue']:
    """Check if ``python -m pytest`` is hijacked by a Typer/Click CLI."""
    from .doctor_data import Issue
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
            m = re.match(r'^name\\s*=\\s*"([^"]+)"', line.strip())
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
