"""CLI commands for the doctor subsystem (check, heal, batch)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click


def _echo_json(payload: Any) -> None:
    click.echo(json.dumps(payload, indent=2, default=str))


def _format_check_report(project_path: Path, report: Any) -> str:
    """Format doctor check report as text."""
    lines = [f"Doctor: {project_path.name}"]
    if report.healthy:
        lines.append("  ✓ No issues found")
    else:
        for issue in report.issues:
            fixable = "🔧" if issue.auto_fixable else "⚠️"
            lines.append(f"  {fixable} [{issue.category}] {issue.path}: {issue.description}")
        if report.errors:
            for err in report.errors:
                lines.append(f"  ✗ {err}")
    return "\n".join(lines)


def _format_heal_report(project_path: Path, report: Any) -> str:
    """Format doctor heal report as text."""
    lines = [f"Doctor heal: {project_path.name}"]
    for issue in report.issues:
        lines.append(f"  [{issue.category}] {issue.path}: {issue.description}")
    for fix in report.fixes_applied:
        lines.append(f"  ✓ {fix}")
    for err in report.errors:
        lines.append(f"  ✗ {err}")
    lines.append(f"  Summary: {len(report.fixes_applied)} fixed, {len(report.errors)} errors")
    return "\n".join(lines)


def _format_batch_report(reports: list) -> str:
    """Format doctor batch report as text."""
    lines = []
    total_issues = total_fixes = total_errors = 0
    for report in reports:
        total_issues += len(report.issues)
        total_fixes += len(report.fixes_applied)
        total_errors += len(report.errors)
        if report.issues or report.fixes_applied or report.errors:
            status = "✓" if not report.errors else "✗"
            lines.append(f"  {status} {report.project}: {len(report.issues)} issues, {len(report.fixes_applied)} fixed")
            for fix in report.fixes_applied:
                lines.append(f"      {fix}")
            for err in report.errors:
                lines.append(f"      ERROR: {err}")
    lines.append(f"\nTotal: {total_issues} issues, {total_fixes} fixed, {total_errors} errors across {len(reports)} projects")
    return "\n".join(lines)


def _register_doctor_check(doctor_grp: click.Group) -> None:
    @doctor_grp.command("check")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path))
    @click.option("--format", "-f", default="text", type=click.Choice(["text", "json"]), help="Output format")
    def doctor_check(project_path: Path, format: str) -> None:
        """Diagnose issues in a project (no changes made)."""
        from .doctor import diagnose
        report = diagnose(project_path)
        if format == "json":
            _echo_json(report.summary_dict())
        else:
            click.echo(_format_check_report(project_path, report))


def _register_doctor_heal(doctor_grp: click.Group) -> None:
    @doctor_grp.command("heal")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, path_type=Path))
    @click.option("--dry-run", is_flag=True, help="Show what would be fixed without applying")
    @click.option("--format", "-f", default="text", type=click.Choice(["text", "json"]), help="Output format")
    def doctor_heal(project_path: Path, dry_run: bool, format: str) -> None:
        """Diagnose and fix issues in a project."""
        from .doctor import heal
        report = heal(project_path, dry_run=dry_run)
        if format == "json":
            _echo_json(report.summary_dict())
        else:
            click.echo(_format_heal_report(project_path, report))


def _register_doctor_batch(doctor_grp: click.Group) -> None:
    @doctor_grp.command("batch")
    @click.argument("semcod_root", type=click.Path(exists=True, file_okay=False, path_type=Path))
    @click.option("--dry-run", is_flag=True, help="Show what would be fixed without applying")
    @click.option("--format", "-f", default="text", type=click.Choice(["text", "json"]), help="Output format")
    def doctor_batch(semcod_root: Path, dry_run: bool, format: str) -> None:
        """Diagnose and fix issues across all semcod subprojects."""
        from .doctor import heal_batch
        reports = heal_batch(semcod_root, dry_run=dry_run)
        if format == "json":
            _echo_json([r.summary_dict() for r in reports])
        else:
            click.echo(_format_batch_report(reports))


def register(cli: click.Group) -> None:
    """Register the doctor command group on the given Click group."""

    @cli.group()
    def doctor() -> None:
        """Project health diagnosis and repair."""

    _register_doctor_check(doctor)
    _register_doctor_heal(doctor)
    _register_doctor_batch(doctor)
