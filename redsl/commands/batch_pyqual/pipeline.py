"""Single project pipeline with split processing stages."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ...autonomy.quality_gate import _collect_python_files, _measure_metrics
from ...validation import pyqual_bridge
from .models import PyqualProjectResult
from .config_gen import _generate_pyqual_yaml, _detect_publish_configured
from .verdict import compute_verdict

logger = logging.getLogger(__name__)

# Profile constants
_AUTO_PROFILE = "auto"
_DEFAULT_PROFILE = "python"
_PUBLISH_PROFILE = "python-publish"


def _resolve_profile(requested_profile: str, run_pipeline: bool, publish: bool) -> str:
    """Resolve auto profile based on options."""
    if requested_profile != _AUTO_PROFILE:
        return requested_profile
    if publish:
        return _PUBLISH_PROFILE
    return _DEFAULT_PROFILE


@dataclass
class ProjectContext:
    """Mutable context passed through pipeline stages."""

    result: PyqualProjectResult
    project: Path
    pyqual_available: bool
    pyqual_ready: bool
    pyqual_yaml: Path

    # Mutable state
    should_skip: bool = False
    skip_result: PyqualProjectResult | None = None


def _init_project_context(
    project: Path,
    profile: str,
    publish: bool,
    dry_run: bool,
    skip_dirty: bool,
    pyqual_available: bool,
) -> ProjectContext:
    """Stage 1: Initialize project context and check skip conditions."""
    result = PyqualProjectResult(name=project.name, path=str(project))
    result.profile_used = profile
    result.publish_requested = publish
    result.dry_run = dry_run
    result.pyqual_available = pyqual_available

    # Check dirty status
    from .discovery import _git_status_lines
    dirty_before = _git_status_lines(project)
    result.dirty_entries_before = len(dirty_before)
    result.dirty_before = bool(dirty_before)

    if result.dirty_before and skip_dirty:
        result.skipped = True
        result.skip_reason = f"dirty-repo ({result.dirty_entries_before} changes)"
        result.verdict = "skipped"
        result.verdict_reasons = [result.skip_reason]
        ctx = ProjectContext(
            result=result,
            project=project,
            pyqual_available=pyqual_available,
            pyqual_ready=False,
            pyqual_yaml=project / "pyqual.yaml",
            should_skip=True,
            skip_result=result,
        )
        return ctx

    # Check/generate pyqual.yaml
    pyqual_yaml = project / "pyqual.yaml"
    result.has_pyqual_yaml = pyqual_yaml.exists()
    result.publish_configured = _detect_publish_configured(pyqual_yaml)

    if not pyqual_yaml.exists():
        print(f"    Generating pyqual.yaml...")
        generated = _generate_pyqual_yaml(project, profile, pyqual_available)
        result.pyqual_yaml_generated = generated
        result.has_pyqual_yaml = generated and pyqual_yaml.exists()
        result.publish_configured = _detect_publish_configured(pyqual_yaml)

    return ProjectContext(
        result=result,
        project=project,
        pyqual_available=pyqual_available,
        pyqual_ready=False,
        pyqual_yaml=pyqual_yaml,
    )


def _validate_config(ctx: ProjectContext, fix_config: bool) -> ProjectContext:
    """Validate pyqual config."""
    if not (ctx.pyqual_available and ctx.result.has_pyqual_yaml):
        return ctx

    try:
        ctx.result.config_valid, ctx.result.config_message = pyqual_bridge.validate_config(
            ctx.project, fix=fix_config
        )
        ctx.result.config_fixed = fix_config and "Auto-fixed" in ctx.result.config_message
        if not ctx.result.config_valid:
            print("    pyqual config: FAIL")
        elif ctx.result.config_fixed:
            print("    pyqual config: fixed")
        else:
            print("    pyqual config: valid")
    except Exception as exc:
        ctx.result.config_valid = False
        ctx.result.errors.append(f"pyqual validate: {exc}")

    return ctx


def _run_analysis_stage(ctx: ProjectContext) -> ProjectContext:
    """Stage 2: Run ReDSL metrics analysis."""
    try:
        py_files = _collect_python_files(ctx.project)
        metrics = _measure_metrics(ctx.project, py_files)
        ctx.result.py_files = metrics["total_files"]
        ctx.result.total_loc = metrics["total_lines"]
        ctx.result.avg_cc = round(metrics["cc_mean"], 2)
        ctx.result.critical_count = metrics["critical"]
        if metrics.get("functions"):
            ctx.result.max_cc = max(f["cc"] for f in metrics["functions"])
    except Exception as exc:
        ctx.result.errors.append(f"ReDSL metrics: {exc}")

    return ctx


def _run_redsl_fix_stage(ctx: ProjectContext, max_fixes: int) -> ProjectContext:
    """Stage 3: Apply ReDSL hybrid auto-fixes."""
    if ctx.result.critical_count > 0 or ctx.result.avg_cc > 10:
        try:
            from ..autofix import _run_hybrid_fix
            applied, errors = _run_hybrid_fix(ctx.project, max_fixes)
            ctx.result.redsl_fixes_applied = applied
            ctx.result.redsl_fixes_errors = errors
            if applied > 0:
                print(f"    ReDSL: {applied} auto-fixes applied")
        except Exception as exc:
            ctx.result.errors.append(f"ReDSL fix: {exc}")

    # Quality gate structural fixes
    try:
        from ...autonomy.auto_fix import auto_fix_violations
        from ...autonomy.quality_gate import run_quality_gate

        gate_verdict = run_quality_gate(ctx.project)
        if gate_verdict.violations:
            print(f"    ReDSL quality gate: {len(gate_verdict.violations)} violations")
            fix_result = auto_fix_violations(ctx.project, gate_verdict.violations)
            additional_fixed = len(getattr(fix_result, "fixed", []))
            additional_manual = len(getattr(fix_result, "manual_needed", []))
            ctx.result.redsl_fixes_applied += additional_fixed
            if additional_fixed > 0 or additional_manual > 0:
                print(
                    f"    ReDSL gate auto-fix: {additional_fixed} fixed, "
                    f"{additional_manual} manual"
                )
    except Exception as exc:
        ctx.result.errors.append(f"ReDSL gate fix: {exc}")

    return ctx


def _run_gates_stage(ctx: ProjectContext) -> ProjectContext:
    """Stage 4: Run pyqual gates check."""
    pyqual_ready = ctx.pyqual_available and ctx.result.has_pyqual_yaml and ctx.result.config_valid

    if ctx.pyqual_available and ctx.result.has_pyqual_yaml and not ctx.result.config_valid:
        ctx.result.errors.append("pyqual config invalid — skipping gates/pipeline")

    if not pyqual_ready:
        return ctx

    try:
        gate_result = pyqual_bridge.check_gates(ctx.project)
        ctx.result.gates_passed = gate_result.get("passed", True)
        ctx.result.gate_details = list(gate_result.get("gates", []))
        ctx.result.gates_total = len(ctx.result.gate_details)
        ctx.result.gates_passing = sum(1 for gate in ctx.result.gate_details if gate.get("passed"))
        if gate_result.get("timed_out"):
            ctx.result.errors.append("pyqual gates timed out")
        if gate_result.get("error"):
            ctx.result.errors.append(f"pyqual gates: {gate_result['error']}")
        print(f"    pyqual gates: {'PASS' if ctx.result.gates_passed else 'FAIL'} "
              f"({ctx.result.gates_passing}/{ctx.result.gates_total})")
    except Exception as exc:
        ctx.result.errors.append(f"pyqual gates: {exc}")

    return ctx


def _run_pipeline_stage(ctx: ProjectContext, run_pipeline: bool, publish: bool, fix_config: bool, dry_run: bool) -> ProjectContext:
    """Stage 5: Run pyqual pipeline (optional)."""
    pyqual_ready = ctx.pyqual_available and ctx.result.has_pyqual_yaml and ctx.result.config_valid

    if not (run_pipeline or publish) or not pyqual_ready:
        return ctx

    try:
        print(f"    Running pyqual pipeline...")
        pipeline_result = pyqual_bridge.run_pipeline(ctx.project, fix_config=fix_config, dry_run=dry_run)
        ctx.result.pipeline_ran = True
        ctx.result.pipeline_passed = bool(pipeline_result.get("passed", False))
        ctx.result.pipeline_iterations = int(pipeline_result.get("iterations", 0))
        ctx.result.pipeline_push_passed = bool(pipeline_result.get("push_passed", False))
        ctx.result.pipeline_publish_passed = bool(pipeline_result.get("publish_passed", False))
        if pipeline_result.get("timed_out"):
            ctx.result.errors.append("pyqual pipeline timed out")
        if pipeline_result.get("error"):
            ctx.result.errors.append(f"pyqual pipeline: {pipeline_result['error']}")
        print(f"    pyqual pipeline: {'PASS' if ctx.result.pipeline_passed else 'FAIL'}")
    except Exception as exc:
        ctx.result.errors.append(f"pyqual pipeline: {exc}")

    return ctx


def _run_git_stage(ctx: ProjectContext, git_push: bool, dry_run: bool) -> ProjectContext:
    """Stage 6: Git commit and push."""
    if not git_push:
        return ctx

    try:
        from .discovery import _git_status_lines, _run_cmd

        status_lines = _git_status_lines(ctx.project)
        ctx.result.changes_to_commit = len(status_lines)

        if dry_run:
            if ctx.pyqual_available:
                push_result = pyqual_bridge.git_push(ctx.project, detect_protection=True, dry_run=True)
                ctx.result.push_preflight_passed = bool(
                    push_result.get("pushed", False)
                    or push_result.get("dry_run", False)
                    or push_result.get("ok", False)
                )
            else:
                push_result = _run_cmd(["git", "push", "--dry-run"], ctx.project, timeout=60)
                ctx.result.push_preflight_passed = push_result.returncode == 0
            print(f"    Git push preflight: {'PASS' if ctx.result.push_preflight_passed else 'FAIL'}")
        elif ctx.result.dirty_before:
            ctx.result.errors.append("Push skipped: repository had local changes before batch run")
        else:
            if status_lines:
                if ctx.pyqual_available:
                    commit_result = pyqual_bridge.git_commit(
                        ctx.project,
                        f"chore(pyqual): auto-fix by ReDSL + pyqual ({datetime.now():%Y-%m-%d %H:%M})",
                    )
                    ctx.result.git_committed = bool(commit_result.get("committed", False))
                else:
                    _run_cmd(["git", "add", "-A"], ctx.project, timeout=10)
                    commit_result = _run_cmd(
                        ["git", "commit", "-m", f"chore(pyqual): auto-fix by ReDSL + pyqual ({datetime.now():%Y-%m-%d %H:%M})"],
                        ctx.project,
                        timeout=30,
                    )
                    ctx.result.git_committed = commit_result.returncode == 0

            if ctx.pyqual_available:
                push_result = pyqual_bridge.git_push(ctx.project, detect_protection=True)
                ctx.result.git_pushed = bool(push_result.get("pushed", False))
            else:
                push_result = _run_cmd(["git", "push"], ctx.project, timeout=60)
                ctx.result.git_pushed = push_result.returncode == 0

            if ctx.result.git_committed or ctx.result.git_pushed:
                status = (
                    "committed + pushed"
                    if ctx.result.git_committed and ctx.result.git_pushed
                    else "pushed" if ctx.result.git_pushed else "commit failed"
                )
                print(f"    Git: {status}")
    except Exception as exc:
        ctx.result.errors.append(f"Git: {exc}")

    return ctx


def _finalize_result(
    ctx: ProjectContext,
    require_pipeline: bool,
    require_push: bool,
    require_publish: bool,
) -> PyqualProjectResult:
    """Stage 7: Finalize result and compute verdict."""
    from .discovery import _git_status_lines

    if ctx.should_skip and ctx.skip_result:
        return ctx.skip_result

    # Publish config check
    if require_publish and not ctx.result.publish_configured and not ctx.result.pipeline_publish_passed:
        ctx.result.errors.append("Publish requested but pyqual.yaml does not configure publish stages")

    # Final dirty check
    dirty_after = _git_status_lines(ctx.project)
    ctx.result.dirty_entries_after = len(dirty_after)
    ctx.result.dirty_after = bool(dirty_after)

    # Compute verdict
    ctx.result.verdict, ctx.result.verdict_reasons = compute_verdict(
        ctx.result,
        require_pipeline=require_pipeline,
        require_push=require_push,
        require_publish=require_publish,
    )

    return ctx.result


def process_project(
    project: Path,
    max_fixes: int = 30,
    run_pipeline: bool = False,
    git_push: bool = False,
    profile: str = _DEFAULT_PROFILE,
    publish: bool = False,
    fix_config: bool = False,
    dry_run: bool = False,
    skip_dirty: bool = False,
    pyqual_available: bool = True,
) -> PyqualProjectResult:
    """Full ReDSL + pyqual pipeline for a single project.

    This is the main entry point that orchestrates all pipeline stages.
    Each stage has CC < 10 for maintainability.
    """
    # Stage 1: Initialize context
    ctx = _init_project_context(project, profile, publish, dry_run, skip_dirty, pyqual_available)
    if ctx.should_skip:
        return ctx.skip_result or ctx.result

    # Stage 1b: Validate config
    ctx = _validate_config(ctx, fix_config)

    # Stage 2: Analysis
    ctx = _run_analysis_stage(ctx)

    # Stage 3: ReDSL fixes
    ctx = _run_redsl_fix_stage(ctx, max_fixes)

    # Stage 4: Gates
    ctx = _run_gates_stage(ctx)

    # Stage 5: Pipeline
    ctx = _run_pipeline_stage(ctx, run_pipeline, publish, fix_config, dry_run)

    # Stage 6: Git
    ctx = _run_git_stage(ctx, git_push, dry_run)

    # Stage 7: Finalize
    return _finalize_result(ctx, run_pipeline, git_push, publish)
