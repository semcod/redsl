"""Batch pyqual orchestrator — multi-project quality pipeline.

For each project in a workspace:
1. Detect if pyqual.yaml exists → generate if missing
2. Run ReDSL analysis + auto-fix (DSL decisions)
3. Run pyqual gates to verify quality thresholds
4. Run pyqual pipeline (optional: fix → verify → report)
5. Git commit + push results
6. Produce aggregate Markdown report

This module bridges ReDSL's code intelligence (analyzers, DSL engine,
LLM orchestrator) with pyqual's declarative quality gates and CI/CD
automation.
"""

from __future__ import annotations

import fnmatch
import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_SKIP_DIRS = frozenset({
    "venv", ".venv", ".git", "__pycache__", "node_modules", ".tox",
    "dist", "build", "logs", "2026", "project", "docs", "refactor_output",
    "shared", "pyqual-demo",
})

_PACKAGE_MARKERS = {"pyproject.toml", "setup.py", "setup.cfg"}

_AUTO_PROFILE = "auto"
_DEFAULT_PROFILE = "python"
_FULL_PROFILE = "python-full"
_PUBLISH_PROFILE = "python-publish"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class PyqualProjectResult:
    """Result of pyqual pipeline for a single project."""

    name: str
    path: str
    has_pyqual_yaml: bool = False
    pyqual_yaml_generated: bool = False
    profile_used: str = ""
    config_valid: bool = True
    config_fixed: bool = False
    config_message: str = ""
    publish_requested: bool = False
    publish_configured: bool = False

    # ReDSL analysis
    py_files: int = 0
    total_loc: int = 0
    avg_cc: float = 0.0
    max_cc: int = 0
    critical_count: int = 0
    redsl_fixes_applied: int = 0
    redsl_fixes_errors: int = 0

    # pyqual gates
    pyqual_available: bool = False
    gates_passed: bool = False
    gates_total: int = 0
    gates_passing: int = 0
    gate_details: list[dict[str, Any]] = field(default_factory=list)

    # pyqual pipeline
    pipeline_ran: bool = False
    pipeline_passed: bool = False
    pipeline_iterations: int = 0
    pipeline_push_passed: bool = False
    pipeline_publish_passed: bool = False

    # git
    git_committed: bool = False
    git_pushed: bool = False
    push_preflight_passed: bool = False
    changes_to_commit: int = 0
    dirty_before: bool = False
    dirty_after: bool = False
    dirty_entries_before: int = 0
    dirty_entries_after: int = 0
    dry_run: bool = False
    verdict: str = "unknown"
    verdict_reasons: list[str] = field(default_factory=list)

    errors: list[str] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_package(path: Path) -> bool:
    return any((path / m).exists() for m in _PACKAGE_MARKERS)


def _find_packages(workspace_root: Path) -> list[Path]:
    packages = []
    for item in sorted(workspace_root.iterdir()):
        if not item.is_dir() or item.name.startswith(".") or item.name in _SKIP_DIRS:
            continue
        if _is_package(item):
            packages.append(item)
    return packages


def _normalize_patterns(values: tuple[str, ...] | list[str] | None) -> list[str]:
    patterns: list[str] = []
    for value in values or ():
        for item in str(value).split(","):
            token = item.strip()
            if token:
                patterns.append(token)
    return patterns


def _matches_any(name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def _filter_packages(
    packages: list[Path],
    include: tuple[str, ...] | list[str] | None = None,
    exclude: tuple[str, ...] | list[str] | None = None,
) -> list[Path]:
    include_patterns = _normalize_patterns(include)
    exclude_patterns = _normalize_patterns(exclude)
    filtered = packages
    if include_patterns:
        filtered = [pkg for pkg in filtered if _matches_any(pkg.name, include_patterns)]
    if exclude_patterns:
        filtered = [pkg for pkg in filtered if not _matches_any(pkg.name, exclude_patterns)]
    return filtered


def _pyqual_cli_available() -> bool:
    return shutil.which("pyqual") is not None


def _run_cmd(cmd: list[str], cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout, cwd=str(cwd),
    )


def _git_status_lines(project: Path) -> list[str]:
    try:
        proc = _run_cmd(["git", "status", "--porcelain"], project, timeout=15)
    except Exception:
        return []
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _resolve_profile(requested_profile: str, run_pipeline: bool, publish: bool) -> str:
    if requested_profile != _AUTO_PROFILE:
        return requested_profile
    if publish:
        return _PUBLISH_PROFILE
    return _DEFAULT_PROFILE


def _detect_publish_configured(pyqual_yaml: Path) -> bool:
    if not pyqual_yaml.exists():
        return False
    try:
        content = pyqual_yaml.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return any(token in content for token in ("publish", "twine-publish", "make-publish", "release-check"))


def _compute_verdict(
    result: PyqualProjectResult,
    require_pipeline: bool = False,
    require_push: bool = False,
    require_publish: bool = False,
) -> tuple[str, list[str]]:
    if result.skipped:
        return "skipped", ([result.skip_reason] if result.skip_reason else [])

    reasons: list[str] = []
    if not result.config_valid:
        reasons.append("config")
    if not result.gates_passed:
        reasons.append("gates")
    if require_pipeline and not result.pipeline_passed:
        reasons.append("pipeline")
    if require_push:
        if result.dry_run:
            if not result.push_preflight_passed:
                reasons.append("push-preflight")
        elif result.changes_to_commit > 0:
            if not (result.git_committed or result.pipeline_push_passed):
                reasons.append("commit")
            if not (result.git_pushed or result.pipeline_push_passed):
                reasons.append("push")
            if result.dirty_after:
                reasons.append("dirty-after")
    if require_publish:
        if not result.publish_configured:
            reasons.append("publish-config")
        if not result.dry_run and not result.pipeline_publish_passed:
            reasons.append("publish")

    if reasons:
        return "failed", reasons
    if result.dry_run and (require_pipeline or require_push or require_publish):
        return "ready", []
    return "success", []


# ---------------------------------------------------------------------------
# pyqual.yaml generator
# ---------------------------------------------------------------------------

_PYQUAL_YAML_TEMPLATE = """\
pipeline:
  name: quality-loop-{name}

  metrics:
    cc_max: 15
    critical_max: 30
    coverage_min: 20
    coverage_branch_min: 15
    completion_rate_min: 75
    ruff_errors_max: 150
    mypy_errors_max: 100

  stages:
    - name: ruff-lint
      tool: ruff
      when: always
      optional: true

    - name: mypy-types
      tool: mypy
      when: always
      optional: true

    - name: verify
      tool: vallm-verify
      optional: true
      when: after_fix

    - name: report
      tool: report
      when: always
      optional: true

    - name: push
      tool: git-push
      when: always
      optional: true

  loop:
    max_iterations: 3
    on_fail: report

  env:
    LLM_MODEL: openrouter/qwen/qwen3-coder-next
"""


def _generate_pyqual_yaml(project: Path, profile: str, pyqual_available: bool) -> bool:
    if pyqual_available:
        proc = _run_cmd(["pyqual", "init", "--profile", profile, "."], project, timeout=60)
        return proc.returncode == 0 and (project / "pyqual.yaml").exists()
    content = _PYQUAL_YAML_TEMPLATE.format(name=project.name)
    (project / "pyqual.yaml").write_text(content, encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# Single project pipeline
# ---------------------------------------------------------------------------

def _process_project(
    project: Path,
    max_fixes: int = 30,
    run_pipeline: bool = False,
    git_push: bool = False,
    profile: str = _DEFAULT_PROFILE,
    publish: bool = False,
    fix_config: bool = False,
    dry_run: bool = False,
    skip_dirty: bool = False,
) -> PyqualProjectResult:
    """Full ReDSL + pyqual pipeline for a single project."""
    from ..validation import pyqual_bridge

    result = PyqualProjectResult(name=project.name, path=str(project))
    pyqual_available = _pyqual_cli_available()
    result.pyqual_available = pyqual_available
    result.profile_used = profile
    result.publish_requested = publish
    result.dry_run = dry_run
    dirty_before = _git_status_lines(project)
    result.dirty_entries_before = len(dirty_before)
    result.dirty_before = bool(dirty_before)
    if result.dirty_before and skip_dirty:
        result.skipped = True
        result.skip_reason = f"dirty-repo ({result.dirty_entries_before} changes)"
        result.verdict = "skipped"
        result.verdict_reasons = [result.skip_reason]
        return result

    # 1. Check / generate pyqual.yaml
    pyqual_yaml = project / "pyqual.yaml"
    result.has_pyqual_yaml = pyqual_yaml.exists()
    result.publish_configured = _detect_publish_configured(pyqual_yaml)
    if not pyqual_yaml.exists():
        print(f"    Generating pyqual.yaml...")
        if pyqual_available:
            generated = pyqual_bridge.init_config(project, profile).get("created", False)
        else:
            generated = _generate_pyqual_yaml(project, profile, pyqual_available)
        result.pyqual_yaml_generated = generated
        result.has_pyqual_yaml = generated and pyqual_yaml.exists()
        result.publish_configured = _detect_publish_configured(pyqual_yaml)

    if pyqual_available and result.has_pyqual_yaml:
        try:
            result.config_valid, result.config_message = pyqual_bridge.validate_config(project, fix=fix_config)
            result.config_fixed = fix_config and "Auto-fixed" in result.config_message
            if not result.config_valid:
                print("    pyqual config: FAIL")
            elif result.config_fixed:
                print("    pyqual config: fixed")
            else:
                print("    pyqual config: valid")
        except Exception as exc:
            result.config_valid = False
            result.errors.append(f"pyqual validate: {exc}")

    pyqual_ready = pyqual_available and result.has_pyqual_yaml and result.config_valid
    if pyqual_available and result.has_pyqual_yaml and not result.config_valid:
        result.errors.append("pyqual config invalid — skipping gates/pipeline")

    # 2. ReDSL metrics + auto-fix
    try:
        from ..autonomy.quality_gate import _collect_python_files, _measure_metrics
        py_files = _collect_python_files(project)
        metrics = _measure_metrics(project, py_files)
        result.py_files = metrics["total_files"]
        result.total_loc = metrics["total_lines"]
        result.avg_cc = round(metrics["cc_mean"], 2)
        result.critical_count = metrics["critical"]
        if metrics.get("functions"):
            result.max_cc = max(f["cc"] for f in metrics["functions"])
    except Exception as exc:
        result.errors.append(f"ReDSL metrics: {exc}")

    # 3. ReDSL hybrid auto-fix
    if result.critical_count > 0 or result.avg_cc > 10:
        try:
            from .autofix import _run_hybrid_fix
            applied, errors = _run_hybrid_fix(project, max_fixes)
            result.redsl_fixes_applied = applied
            result.redsl_fixes_errors = errors
            if applied > 0:
                print(f"    ReDSL: {applied} auto-fixes applied")
        except Exception as exc:
            result.errors.append(f"ReDSL fix: {exc}")

    # 3b. ReDSL quality-gate auto-fix for structural problems (high CC, oversized files)
    try:
        from ..autonomy.auto_fix import auto_fix_violations
        from ..autonomy.quality_gate import run_quality_gate

        gate_verdict = run_quality_gate(project)
        if gate_verdict.violations:
            print(f"    ReDSL quality gate: {len(gate_verdict.violations)} violations")
            fix_result = auto_fix_violations(project, gate_verdict.violations)
            additional_fixed = len(getattr(fix_result, "fixed", []))
            additional_manual = len(getattr(fix_result, "manual_needed", []))
            result.redsl_fixes_applied += additional_fixed
            if additional_fixed > 0 or additional_manual > 0:
                print(
                    f"    ReDSL gate auto-fix: {additional_fixed} fixed, "
                    f"{additional_manual} manual"
                )
    except Exception as exc:
        result.errors.append(f"ReDSL gate fix: {exc}")

    # 4. pyqual gates check
    if pyqual_ready:
        try:
            gate_result = pyqual_bridge.check_gates(project)
            result.gates_passed = gate_result.get("passed", True)
            result.gate_details = list(gate_result.get("gates", []))
            result.gates_total = len(result.gate_details)
            result.gates_passing = sum(1 for gate in result.gate_details if gate.get("passed"))
            if gate_result.get("timed_out"):
                result.errors.append("pyqual gates timed out")
            if gate_result.get("error"):
                result.errors.append(f"pyqual gates: {gate_result['error']}")
            print(f"    pyqual gates: {'PASS' if result.gates_passed else 'FAIL'} "
                  f"({result.gates_passing}/{result.gates_total})")
        except Exception as exc:
            result.errors.append(f"pyqual gates: {exc}")

    # 5. pyqual pipeline (optional)
    if (run_pipeline or publish) and pyqual_ready:
        try:
            print(f"    Running pyqual pipeline...")
            pipeline_result = pyqual_bridge.run_pipeline(project, fix_config=fix_config, dry_run=dry_run)
            result.pipeline_ran = True
            result.pipeline_passed = bool(pipeline_result.get("passed", False))
            result.pipeline_iterations = int(pipeline_result.get("iterations", 0))
            result.pipeline_push_passed = bool(pipeline_result.get("push_passed", False))
            result.pipeline_publish_passed = bool(pipeline_result.get("publish_passed", False))
            if pipeline_result.get("timed_out"):
                result.errors.append("pyqual pipeline timed out")
            if pipeline_result.get("error"):
                result.errors.append(f"pyqual pipeline: {pipeline_result['error']}")
            print(f"    pyqual pipeline: {'PASS' if result.pipeline_passed else 'FAIL'}")
        except Exception as exc:
            result.errors.append(f"pyqual pipeline: {exc}")

    # 6. Git commit + push
    if git_push:
        try:
            status_lines = _git_status_lines(project)
            result.changes_to_commit = len(status_lines)
            if dry_run:
                if pyqual_available:
                    push_result = pyqual_bridge.git_push(project, detect_protection=True, dry_run=True)
                    result.push_preflight_passed = bool(
                        push_result.get("pushed", False)
                        or push_result.get("dry_run", False)
                        or push_result.get("ok", False)
                    )
                else:
                    push_result = _run_cmd(["git", "push", "--dry-run"], project, timeout=60)
                    result.push_preflight_passed = push_result.returncode == 0
                print(f"    Git push preflight: {'PASS' if result.push_preflight_passed else 'FAIL'}")
            elif result.dirty_before:
                result.errors.append("Push skipped: repository had local changes before batch run")
            else:
                if status_lines:
                    if pyqual_available:
                        commit_result = pyqual_bridge.git_commit(
                            project,
                            f"chore(pyqual): auto-fix by ReDSL + pyqual ({datetime.now():%Y-%m-%d %H:%M})",
                        )
                        result.git_committed = bool(commit_result.get("committed", False))
                    else:
                        _run_cmd(["git", "add", "-A"], project, timeout=10)
                        commit_result = _run_cmd(["git", "commit", "-m", f"chore(pyqual): auto-fix by ReDSL + pyqual ({datetime.now():%Y-%m-%d %H:%M})"], project, timeout=30)
                        result.git_committed = commit_result.returncode == 0
                if pyqual_available:
                    push_result = pyqual_bridge.git_push(project, detect_protection=True)
                    result.git_pushed = bool(push_result.get("pushed", False))
                else:
                    push_result = _run_cmd(["git", "push"], project, timeout=60)
                    result.git_pushed = push_result.returncode == 0
                if result.git_committed or result.git_pushed:
                    print(
                        "    Git: "
                        + (
                            "committed + pushed"
                            if result.git_committed and result.git_pushed
                            else "pushed"
                            if result.git_pushed
                            else "commit failed"
                        )
                    )
        except Exception as exc:
            result.errors.append(f"Git: {exc}")

    if publish and not result.publish_configured and not result.pipeline_publish_passed:
        result.errors.append("Publish requested but pyqual.yaml does not configure publish stages")

    dirty_after = _git_status_lines(project)
    result.dirty_entries_after = len(dirty_after)
    result.dirty_after = bool(dirty_after)
    result.verdict, result.verdict_reasons = _compute_verdict(
        result,
        require_pipeline=(run_pipeline or publish),
        require_push=git_push,
        require_publish=publish,
    )

    return result


# ---------------------------------------------------------------------------
# Batch runner
# ---------------------------------------------------------------------------

def run_pyqual_batch(
    workspace_root: Path,
    max_fixes: int = 30,
    run_pipeline: bool = False,
    git_push: bool = False,
    limit: int = 0,
    profile: str = _AUTO_PROFILE,
    publish: bool = False,
    fix_config: bool = False,
    include: tuple[str, ...] | list[str] | None = None,
    exclude: tuple[str, ...] | list[str] | None = None,
    dry_run: bool = False,
    skip_dirty: bool = False,
    fail_fast: bool = False,
) -> dict[str, Any]:
    """Run ReDSL + pyqual on all projects in workspace."""
    packages = _filter_packages(_find_packages(workspace_root), include=include, exclude=exclude)
    if limit > 0:
        packages = packages[:limit]
    pyqual_ok = _pyqual_cli_available()
    resolved_profile = _resolve_profile(profile, run_pipeline, publish)
    effective_pipeline = run_pipeline or publish

    print(f"\n{'=' * 60}")
    print(f"reDSL × pyqual — Multi-Project Quality Pipeline")
    print(f"{'=' * 60}")
    print(f"Workspace:      {workspace_root}")
    print(f"Projects found: {len(packages)}")
    print(f"pyqual CLI:     {'✅ available' if pyqual_ok else '⚠️  not found (install: pip install pyqual)'}")
    print(f"Pipeline mode:  {'full (fix+verify+publish)' if effective_pipeline else 'gates only'}")
    print(f"Git push:       {'enabled' if git_push else 'disabled'}")
    print(f"Publish:        {'enabled' if publish else 'disabled'}")
    print(f"Config fix:     {'enabled' if fix_config else 'disabled'}")
    print(f"Dry run:        {'enabled' if dry_run else 'disabled'}")
    print(f"Skip dirty:     {'enabled' if skip_dirty else 'disabled'}")
    print(f"Profile:        {resolved_profile}")
    print(f"{'=' * 60}")

    all_results: list[PyqualProjectResult] = []

    for i, package in enumerate(packages, 1):
        print(f"\n[{i}/{len(packages)}] {package.name}")
        print("-" * 40)

        result = _process_project(package, max_fixes, effective_pipeline, git_push, resolved_profile, publish, fix_config, dry_run, skip_dirty)
        all_results.append(result)

        # Brief status
        parts = []
        if result.skipped:
            parts.append(f"skipped: {result.skip_reason}")
        if result.pyqual_yaml_generated:
            parts.append("pyqual.yaml generated")
        if not result.config_valid:
            parts.append("config FAIL")
        elif result.config_fixed:
            parts.append("config fixed")
        if result.redsl_fixes_applied > 0:
            parts.append(f"{result.redsl_fixes_applied} ReDSL fixes")
        if result.gates_passed:
            parts.append(f"gates PASS ({result.gates_passing}/{result.gates_total})")
        elif result.gates_total > 0:
            parts.append(f"gates FAIL ({result.gates_passing}/{result.gates_total})")
        if result.pipeline_passed:
            parts.append("pipeline OK")
        elif result.pipeline_ran:
            parts.append("pipeline FAIL")
        if result.push_preflight_passed:
            parts.append("push preflight OK")
        if result.pipeline_publish_passed:
            parts.append("publish OK")
        if result.git_committed:
            parts.append("committed")
        if result.git_pushed:
            parts.append("pushed")
        parts.append(f"verdict={result.verdict}")
        if not parts:
            parts.append(f"{result.py_files} files, CC̄={result.avg_cc}")

        print(f"  → {', '.join(parts)}")

        if fail_fast and result.verdict == "failed":
            print("  → fail-fast triggered, stopping batch")
            break

    summary = _build_summary(all_results)
    _print_summary(summary)
    _save_report(all_results, summary, workspace_root)

    return summary


def _build_summary(results: list[PyqualProjectResult]) -> dict[str, Any]:
    return {
        "projects_processed": len(results),
        "projects_success": sum(1 for r in results if r.verdict == "success"),
        "projects_ready": sum(1 for r in results if r.verdict == "ready"),
        "projects_failed": sum(1 for r in results if r.verdict == "failed"),
        "projects_skipped": sum(1 for r in results if r.verdict == "skipped"),
        "pyqual_yamls_generated": sum(1 for r in results if r.pyqual_yaml_generated),
        "projects_config_valid": sum(1 for r in results if r.config_valid),
        "projects_config_fixed": sum(1 for r in results if r.config_fixed),
        "total_redsl_fixes": sum(r.redsl_fixes_applied for r in results),
        "total_gates_total": sum(r.gates_total for r in results),
        "total_gates_passing": sum(r.gates_passing for r in results),
        "projects_gates_passed": sum(1 for r in results if r.gates_passed),
        "projects_pipeline_passed": sum(1 for r in results if r.pipeline_passed),
        "projects_publish_ready": sum(1 for r in results if r.publish_configured or r.pipeline_publish_passed),
        "projects_publish_passed": sum(1 for r in results if r.pipeline_publish_passed),
        "projects_committed": sum(1 for r in results if r.git_committed),
        "projects_pushed": sum(1 for r in results if r.git_pushed),
        "projects_push_preflight_passed": sum(1 for r in results if r.push_preflight_passed),
        "total_py_files": sum(r.py_files for r in results),
        "total_loc": sum(r.total_loc for r in results),
        "total_errors": sum(len(r.errors) for r in results),
        "batch_verdict": (
            "failed"
            if any(r.verdict == "failed" for r in results)
            else "ready"
            if any(r.verdict == "ready" for r in results)
            else "skipped"
            if results and all(r.verdict == "skipped" for r in results)
            else "success"
            if results
            else "empty"
        ),
        "project_details": [
            {
                "name": r.name,
                "py_files": r.py_files,
                "total_loc": r.total_loc,
                "avg_cc": r.avg_cc,
                "max_cc": r.max_cc,
                "critical": r.critical_count,
                "redsl_fixes": r.redsl_fixes_applied,
                "config_valid": r.config_valid,
                "config_fixed": r.config_fixed,
                "gates_pass": r.gates_passed,
                "gates_ratio": f"{r.gates_passing}/{r.gates_total}",
                "pipeline_pass": r.pipeline_passed,
                "publish_ready": r.publish_configured,
                "publish_pass": r.pipeline_publish_passed,
                "committed": r.git_committed,
                "pushed": r.git_pushed,
                "push_preflight_passed": r.push_preflight_passed,
                "dirty_before": r.dirty_before,
                "dirty_after": r.dirty_after,
                "verdict": r.verdict,
                "verdict_reasons": r.verdict_reasons,
                "errors": r.errors,
            }
            for r in results
        ],
    }


def _print_summary(summary: dict[str, Any]) -> None:
    print(f"\n{'=' * 60}")
    print("reDSL × pyqual — SUMMARY")
    print(f"{'=' * 60}")
    print(f"Batch verdict:           {summary['batch_verdict']}")
    print(f"Projects processed:      {summary['projects_processed']}")
    print(f"Projects success:        {summary['projects_success']}")
    print(f"Projects ready:          {summary['projects_ready']}")
    print(f"Projects failed:         {summary['projects_failed']}")
    print(f"Projects skipped:        {summary['projects_skipped']}")
    print(f"pyqual.yaml generated:   {summary['pyqual_yamls_generated']}")
    print(f"Configs valid:           {summary['projects_config_valid']}/{summary['projects_processed']}")
    if summary['projects_config_fixed'] > 0:
        print(f"Configs fixed:           {summary['projects_config_fixed']}")
    print(f"ReDSL auto-fixes:        {summary['total_redsl_fixes']}")
    print(f"Gates passing:           {summary['total_gates_passing']}/{summary['total_gates_total']}")
    print(f"Projects all-gates-pass: {summary['projects_gates_passed']}/{summary['projects_processed']}")
    if summary['projects_publish_ready'] > 0:
        print(f"Publish-ready:           {summary['projects_publish_ready']}")
        print(f"Publish passed:          {summary['projects_publish_passed']}")
    if summary['projects_push_preflight_passed'] > 0:
        print(f"Push preflight passed:   {summary['projects_push_preflight_passed']}")
    if summary['projects_committed'] > 0:
        print(f"Git commits:             {summary['projects_committed']}")
        print(f"Git pushes:              {summary['projects_pushed']}")
    print(f"Total files:             {summary['total_py_files']}")
    print(f"Total LOC:               {summary['total_loc']:,}")
    if summary["total_errors"] > 0:
        print(f"Errors:                  {summary['total_errors']}")


def _save_report(
    results: list[PyqualProjectResult],
    summary: dict[str, Any],
    workspace_root: Path,
) -> None:
    """Save Markdown report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# reDSL × pyqual — Multi-Project Quality Report",
        "",
        f"> Generated: **{now}**  ",
        f"> Workspace: `{workspace_root}`  ",
        f"> Projects: **{summary['projects_processed']}**",
        f"> Batch verdict: **{summary['batch_verdict']}**",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|------:|",
        f"| Projects processed | {summary['projects_processed']} |",
        f"| Projects success | {summary['projects_success']} |",
        f"| Projects ready | {summary['projects_ready']} |",
        f"| Projects failed | {summary['projects_failed']} |",
        f"| Projects skipped | {summary['projects_skipped']} |",
        f"| pyqual.yaml generated | {summary['pyqual_yamls_generated']} |",
        f"| Configs valid | {summary['projects_config_valid']}/{summary['projects_processed']} |",
        f"| Configs fixed | {summary['projects_config_fixed']} |",
        f"| ReDSL auto-fixes | {summary['total_redsl_fixes']} |",
        f"| Gates passing | {summary['total_gates_passing']}/{summary['total_gates_total']} |",
        f"| Projects gates pass | {summary['projects_gates_passed']}/{summary['projects_processed']} |",
        f"| Publish-ready projects | {summary['projects_publish_ready']} |",
        f"| Publish passed | {summary['projects_publish_passed']} |",
        f"| Push preflight passed | {summary['projects_push_preflight_passed']} |",
        f"| Git commits | {summary['projects_committed']} |",
        f"| Git pushes | {summary['projects_pushed']} |",
        f"| Total .py files | {summary['total_py_files']} |",
        f"| Total LOC | {summary['total_loc']:,} |",
        "",
        "---",
        "",
        "## Per-Project Details",
        "",
        "| # | Project | Files | LOC | CC̄ | Max CC | Fixes | Config | Gates | Pipeline | Publish | Git | Verdict |",
        "|---|---------|------:|----:|----:|-------:|------:|--------|-------|----------|---------|-----|---------|",
    ]

    for i, r in enumerate(results, 1):
        config_str = "✅" if r.config_valid else ("🛠️" if r.config_fixed else "❌")
        gate_str = f"{'✅' if r.gates_passed else '❌'} {r.gates_passing}/{r.gates_total}" if r.gates_total else "—"
        pipe_str = "✅" if r.pipeline_passed else ("❌" if r.pipeline_ran else "—")
        publish_str = "✅" if r.pipeline_publish_passed else ("📝" if r.publish_configured else "—")
        git_str = "✅" if r.git_pushed else ("🔎" if r.push_preflight_passed else ("📝" if r.git_committed else "—"))
        lines.append(
            f"| {i} | `{r.name}` | {r.py_files} | {r.total_loc:,} | {r.avg_cc:.1f} | {r.max_cc} "
            f"| {r.redsl_fixes_applied} | {config_str} | {gate_str} | {pipe_str} | {publish_str} | {git_str} | {r.verdict} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Project Notes",
        "",
    ]

    for r in results:
        if not (r.gate_details or r.verdict_reasons or r.errors):
            continue
        lines.append(f"### {r.name}")
        lines.append("")
        lines.append(f"- verdict: {r.verdict}")
        if r.verdict_reasons:
            lines.append(f"- verdict reasons: {', '.join(r.verdict_reasons)}")
        for error in r.errors:
            lines.append(f"- error: {error}")
        for gd in r.gate_details:
            lines.append(f"- gate: {gd['line']}")
        lines.append("")

    lines += [
        "---",
        "",
        f"_Report generated by [reDSL](https://github.com/wronai/redsl) × [pyqual](https://github.com/wronai/pyqual)_",
    ]

    report_path = workspace_root / "redsl_pyqual_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport saved to: {report_path}")
