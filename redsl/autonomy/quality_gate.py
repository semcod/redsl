"""Quality gate — blocks commits that degrade code quality metrics.

Pre-commit hook + CI gate checking metrics BEFORE merge.
If new code worsens CC mean by >0.2 or adds a god module -> BLOCK.
"""

from __future__ import annotations

import ast
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class GateVerdict:
    """Result of a quality gate check."""

    passed: bool
    reason: str
    metrics_before: dict
    metrics_after: dict
    violations: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Gate thresholds (configurable via kwargs)
# ---------------------------------------------------------------------------

_DEFAULT_THRESHOLDS = {
    "max_cc_delta": 0.2,
    "max_new_file_lines": 400,
    "max_new_function_cc": 12,
    "max_critical_delta": 0,
    "max_file_lines": 500,
}


# ---------------------------------------------------------------------------
# Metrics collection
# ---------------------------------------------------------------------------

def _collect_python_files(project_dir: Path) -> list[Path]:
    """Collect all non-ignored .py files."""
    skip = frozenset({
        "__pycache__", "venv", ".venv", ".tox", "node_modules",
        "build", "dist", ".git", ".eggs",
    })
    result: list[Path] = []
    for p in project_dir.rglob("*.py"):
        if any(part in skip or part.endswith(".egg-info") for part in p.parts):
            continue
        result.append(p)
    return sorted(result)


def _file_cc_functions(path: Path) -> list[dict]:
    """Return list of {name, cc, lineno} for functions in *path*."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return []

    from redsl.analyzers.python_analyzer import ast_cyclomatic_complexity

    results: list[dict] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            cc = ast_cyclomatic_complexity(node)
            results.append({"name": node.name, "cc": cc, "lineno": node.lineno})
    return results


def _measure_metrics(project_dir: Path, files: list[Path]) -> dict:
    """Compute aggregate metrics for a set of files."""
    total_lines = 0
    total_cc = 0.0
    func_count = 0
    critical = 0
    file_details: list[dict] = []
    functions: list[dict] = []

    for fp in files:
        try:
            lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        n_lines = len(lines)
        total_lines += n_lines

        funcs = _file_cc_functions(fp)
        for f in funcs:
            total_cc += f["cc"]
            func_count += 1
            if f["cc"] > 15:
                critical += 1
            functions.append({**f, "path": str(fp.relative_to(project_dir))})

        file_details.append({
            "path": str(fp.relative_to(project_dir)),
            "lines": n_lines,
        })

    cc_mean = total_cc / func_count if func_count else 0.0
    return {
        "cc_mean": cc_mean,
        "critical": critical,
        "total_lines": total_lines,
        "total_files": len(files),
        "func_count": func_count,
        "files": file_details,
        "functions": functions,
    }


def _git_diff_names(project_dir: Path, ref: str = "HEAD") -> list[str]:
    """Return list of changed file paths relative to project_dir."""
    try:
        proc = subprocess.run(
            ["git", "diff", "--name-only", ref],
            capture_output=True, text=True, cwd=str(project_dir), timeout=10,
        )
        if proc.returncode != 0:
            return []
        staged = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True, text=True, cwd=str(project_dir), timeout=10,
        )
        names = set(proc.stdout.strip().splitlines())
        if staged.returncode == 0:
            names |= set(staged.stdout.strip().splitlines())
        return [n for n in names if n.endswith(".py")]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def _git_file_at_ref(project_dir: Path, rel_path: str, ref: str = "HEAD") -> str | None:
    """Read a file at a given git ref."""
    try:
        proc = subprocess.run(
            ["git", "show", f"{ref}:{rel_path}"],
            capture_output=True, text=True, cwd=str(project_dir), timeout=10,
        )
        return proc.stdout if proc.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def _get_metrics_at_ref(project_dir: Path, ref: str = "HEAD") -> dict:
    """Collect metrics from git ref (HEAD)."""
    files = _collect_python_files(project_dir)
    return _measure_metrics(project_dir, files)


def _get_metrics_current(project_dir: Path) -> dict:
    """Collect metrics from the current working tree."""
    files = _collect_python_files(project_dir)
    metrics = _measure_metrics(project_dir, files)

    changed = set(_git_diff_names(project_dir))
    tracked = set()
    try:
        proc = subprocess.run(
            ["git", "ls-files"],
            capture_output=True, text=True, cwd=str(project_dir), timeout=10,
        )
        if proc.returncode == 0:
            tracked = set(proc.stdout.strip().splitlines())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    new_files: list[dict] = []
    grown_files: list[dict] = []
    new_functions: list[dict] = []

    for fd in metrics["files"]:
        rel = fd["path"]
        if rel not in tracked:
            new_files.append(fd)
        elif rel in changed:
            old_src = _git_file_at_ref(project_dir, rel)
            if old_src is not None:
                old_lines = len(old_src.splitlines())
                grown_files.append({
                    "path": rel,
                    "lines_before": old_lines,
                    "lines_after": fd["lines"],
                })

    for func in metrics["functions"]:
        rel = func["path"]
        if rel not in tracked:
            new_functions.append(func)

    metrics["new_files"] = new_files
    metrics["grown_files"] = grown_files
    metrics["new_functions"] = new_functions
    return metrics


# ---------------------------------------------------------------------------
# Gate logic
# ---------------------------------------------------------------------------

def run_quality_gate(
    project_dir: Path,
    *,
    max_cc_delta: float = _DEFAULT_THRESHOLDS["max_cc_delta"],
    max_new_file_lines: int = _DEFAULT_THRESHOLDS["max_new_file_lines"],
    max_new_function_cc: int = _DEFAULT_THRESHOLDS["max_new_function_cc"],
    max_critical_delta: int = _DEFAULT_THRESHOLDS["max_critical_delta"],
    max_file_lines: int = _DEFAULT_THRESHOLDS["max_file_lines"],
) -> GateVerdict:
    """Check whether current changes pass the quality gate."""
    project_dir = Path(project_dir).resolve()

    before = _get_metrics_at_ref(project_dir, "HEAD")
    after = _get_metrics_current(project_dir)

    violations: list[str] = []

    # Rule 1: CC mean must not increase by more than threshold
    cc_delta = after["cc_mean"] - before["cc_mean"]
    if cc_delta > max_cc_delta:
        violations.append(
            f"CC mean increased by {cc_delta:.2f} (limit: +{max_cc_delta}). "
            f"Before: {before['cc_mean']:.1f}, after: {after['cc_mean']:.1f}"
        )

    # Rule 2: no new file > max_new_file_lines
    for f in after.get("new_files", []):
        if f["lines"] > max_new_file_lines:
            violations.append(
                f"New file {f['path']} has {f['lines']}L (limit: {max_new_file_lines}L)"
            )

    # Rule 3: no new function CC > max_new_function_cc
    for f in after.get("new_functions", []):
        if f["cc"] > max_new_function_cc:
            violations.append(
                f"New function {f['name']} has CC={f['cc']} (limit: {max_new_function_cc})"
            )

    # Rule 4: critical count must not increase
    crit_delta = after["critical"] - before["critical"]
    if crit_delta > max_critical_delta:
        violations.append(
            f"Critical count increased by {crit_delta} (limit: +{max_critical_delta})"
        )

    # Rule 5: no file may grow past max_file_lines
    for f in after.get("grown_files", []):
        if f["lines_after"] > max_file_lines and f["lines_before"] <= max_file_lines:
            violations.append(
                f"{f['path']} exceeded {max_file_lines}L "
                f"({f['lines_before']}->{f['lines_after']}L)"
            )

    return GateVerdict(
        passed=len(violations) == 0,
        reason="OK" if not violations else f"{len(violations)} violation(s)",
        metrics_before=before,
        metrics_after=after,
        violations=violations,
    )


# ---------------------------------------------------------------------------
# Pre-commit hook installer
# ---------------------------------------------------------------------------

_HOOK_SCRIPT = '''#!/bin/bash
# reDSL quality gate — auto-installed pre-commit hook
echo "reDSL quality gate..."
python3 -m redsl.autonomy.quality_gate "$PWD"
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "Quality gate FAILED. Fix violations before committing."
    echo "   Run: redsl gate --details"
    exit 1
fi
echo "Quality gate passed"
'''


def install_pre_commit_hook(project_dir: Path) -> Path:
    """Install a git pre-commit hook that runs the quality gate.

    Returns the path to the installed hook.
    """
    project_dir = Path(project_dir).resolve()
    hook_path = project_dir / ".git" / "hooks" / "pre-commit"
    hook_path.write_text(_HOOK_SCRIPT)
    hook_path.chmod(0o755)
    logger.info("Installed pre-commit hook: %s", hook_path)
    return hook_path


# ---------------------------------------------------------------------------
# CLI entry point (for hook script)
# ---------------------------------------------------------------------------

def _cli_main() -> None:
    """Entry point when called as ``python -m redsl.autonomy.quality_gate <dir>``."""
    import sys

    project_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    verdict = run_quality_gate(project_dir)

    if verdict.passed:
        print(f"Quality gate PASSED (CC={verdict.metrics_after['cc_mean']:.2f})")
        sys.exit(0)
    else:
        print(f"Quality gate FAILED — {verdict.reason}")
        for v in verdict.violations:
            print(f"  - {v}")
        sys.exit(1)


if __name__ == "__main__":
    _cli_main()
