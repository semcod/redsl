"""Scan command for CLI."""

from __future__ import annotations

from pathlib import Path

import click

from redsl.commands import scan as scan_commands
from redsl.cli.logging import setup_logging


def _print_scan_summary(results: list, output_path: Path) -> None:
    """Print scan summary to console."""
    ok = sum(1 for r in results if r.is_ok())
    from redsl.commands.scan import _TIER_CRITICAL, _TIER_HIGH, _TIER_MEDIUM, _TIER_LOW
    tier_counts = {t: sum(1 for r in results if r.tier == t) for t in [_TIER_CRITICAL, _TIER_HIGH, _TIER_MEDIUM, _TIER_LOW]}
    click.echo("─" * 60)
    click.echo(f"\nProjects analysed: {ok}/{len(results)}")
    click.echo(f"  🔴 Critical: {tier_counts[_TIER_CRITICAL]}  🟠 High: {tier_counts[_TIER_HIGH]}  🟡 Medium: {tier_counts[_TIER_MEDIUM]}  🟢 Low: {tier_counts[_TIER_LOW]}")
    click.echo(f"\n📄 Report saved to: {output_path}")


@click.command("scan")
@click.argument("folder", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--output", "-o", "output_path", type=click.Path(path_type=Path), default=None, help="Save markdown report to file")
@click.option("--quiet", "-q", is_flag=True, default=False, help="Suppress progress output")
@click.pass_context
def scan(ctx: click.Context, folder: Path, output_path: Path | None, quiet: bool) -> None:
    """Scan a folder of projects and produce a markdown priority report."""
    setup_logging(folder, ctx.obj.get("verbose", False))
    click.echo(f"\nScanning projects in: {folder}")
    click.echo("─" * 60)
    results = scan_commands.scan_folder(folder, progress=not quiet)
    report_md = scan_commands.render_markdown(results, folder)

    if output_path is None:
        output_path = folder / "redsl_scan_report.md"
    output_path.write_text(report_md, encoding="utf-8")

    _print_scan_summary(results, output_path)
