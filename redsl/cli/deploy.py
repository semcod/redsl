"""redsl deploy — infrastructure deployment commands powered by redeploy."""
from __future__ import annotations

import sys
from pathlib import Path

import click


def register(cli_group: click.Group) -> None:
    cli_group.add_command(deploy)


@click.group("deploy")
def deploy() -> None:
    """Infrastructure deployment via redeploy (detect → plan → apply)."""


# ── detect ────────────────────────────────────────────────────────────────────

@deploy.command("detect")
@click.argument("host")
@click.option("--app", default="app", show_default=True, help="Application name")
@click.option("--domain", default=None, help="Public domain for health probes")
@click.option("-o", "--output", default="infra.yaml", show_default=True,
              type=click.Path(), help="Save InfraState YAML to this file")
def deploy_detect(host: str, app: str, domain: str | None, output: str) -> None:
    """Probe infrastructure on HOST and save infra.yaml."""
    from redsl.bridges.redeploy_bridge import detect_and_save, is_available
    from rich.console import Console

    console = Console()
    if not is_available():
        console.print("[red]✗ redeploy not installed. Run: pip install redeploy[/red]")
        sys.exit(1)

    console.print(f"[bold]detect[/bold]  {host}  app={app}")
    result = detect_and_save(host=host, app=app, domain=domain, output=Path(output))

    if "error" in result:
        console.print(f"[red]✗ {result['error']}[/red]")
        sys.exit(1)

    state = result["state"]
    console.print(f"  strategy : [cyan]{result['strategy']}[/cyan]")
    console.print(f"  version  : {result['version'] or '?'}")
    conflicts = result.get("conflicts", [])
    if conflicts:
        console.print(f"  [yellow]conflicts ({len(conflicts)}):[/yellow]")
        for c in conflicts:
            console.print(f"    [{c['severity'].upper()}] {c['type']}: {c['description']}")
    else:
        console.print("  [green]no conflicts[/green]")
    console.print(f"[dim]saved → {output}[/dim]")


# ── plan ──────────────────────────────────────────────────────────────────────

@deploy.command("plan")
@click.option("--infra", default="infra.yaml", show_default=True,
              type=click.Path(exists=True), help="InfraState YAML (from detect)")
@click.option("--target", default=None, type=click.Path(), help="Target config YAML")
@click.option("--strategy", default=None,
              type=click.Choice([
                  "docker_full", "native_kiosk", "docker_kiosk",
                  "podman_quadlet", "k3s", "systemd", "unknown",
              ]),
              help="Override target strategy")
@click.option("--domain", default=None)
@click.option("--version", "target_version", default=None, help="Target version to verify")
@click.option("--compose", multiple=True, help="Compose file(s)")
@click.option("--env-file", default=None)
@click.option("-o", "--output", default="migration-plan.yaml", show_default=True,
              type=click.Path(), help="Save MigrationPlan YAML")
def deploy_plan(infra: str, target: str | None, strategy: str | None, domain: str | None,
                target_version: str | None, compose: tuple[str, ...], env_file: str | None,
                output: str) -> None:
    """Generate migration-plan.yaml from infra.yaml + desired state."""
    from redsl.bridges.redeploy_bridge import plan_and_save, is_available
    from rich.console import Console

    console = Console()
    if not is_available():
        console.print("[red]✗ redeploy not installed. Run: pip install redeploy[/red]")
        sys.exit(1)

    result = plan_and_save(
        infra_path=Path(infra),
        output=Path(output),
        target_path=Path(target) if target else None,
        strategy=strategy,
        domain=domain,
        version=target_version,
        compose_files=list(compose) if compose else None,
        env_file=env_file,
    )

    if "error" in result:
        console.print(f"[red]✗ {result['error']}[/red]")
        sys.exit(1)

    p = result["plan"]
    console.print(f"[bold]plan[/bold]  "
                  f"[dim]{p['from_strategy']}[/dim] → [cyan]{p['to_strategy']}[/cyan]")
    console.print(f"  steps    : {result['steps']}")
    console.print(f"  risk     : {result['risk']}")
    console.print(f"  downtime : {result['estimated_downtime']}")
    if p.get("notes"):
        for note in p["notes"]:
            console.print(f"  [yellow]⚠ {note}[/yellow]")
    console.print(f"[dim]saved → {output}[/dim]")


# ── apply ─────────────────────────────────────────────────────────────────────

@deploy.command("apply")
@click.option("--plan", "plan_file", default="migration-plan.yaml", show_default=True,
              type=click.Path(exists=True))
@click.option("--dry-run", is_flag=True)
@click.option("--step", default=None, help="Run only a specific step by ID")
def deploy_apply(plan_file: str, dry_run: bool, step: str | None) -> None:
    """Execute a migration-plan.yaml."""
    from redsl.bridges.redeploy_bridge import apply, is_available
    from rich.console import Console

    console = Console()
    if not is_available():
        console.print("[red]✗ redeploy not installed. Run: pip install redeploy[/red]")
        sys.exit(1)

    prefix = "[DRY RUN] " if dry_run else ""
    console.print(f"[bold]{prefix}apply[/bold]  {plan_file}")

    result = apply(plan_path=Path(plan_file), dry_run=dry_run, step_id=step)

    if "error" in result:
        console.print(f"[red]✗ {result['error']}[/red]")
        sys.exit(1)

    for r in result.get("results", []):
        icon = "✅" if r["status"] == "done" else ("⏭" if r["status"] == "skipped" else "❌")
        line = f"  {icon} [{r['id']}]"
        if r.get("result"):
            line += f"  {r['result']}"
        if r.get("error"):
            line += f"  [red]{r['error']}[/red]"
        console.print(line)

    console.print(f"\n{result['summary']}")
    if not result["ok"]:
        sys.exit(1)


# ── run (spec YAML: source + target) ─────────────────────────────────────────

@deploy.command("run")
@click.argument("spec", default="migration.yaml", type=click.Path(exists=True))
@click.option("--dry-run", is_flag=True)
@click.option("--plan-only", is_flag=True, help="Generate plan but do not apply")
@click.option("--detect", "do_detect", is_flag=True,
              help="Run live detect first (overrides source state from spec)")
@click.option("--plan-out", default=None, type=click.Path(), help="Save plan to file")
def deploy_run(spec: str, dry_run: bool, plan_only: bool,
               do_detect: bool, plan_out: str | None) -> None:
    """Run full pipeline from a migration spec YAML (source + target in one file)."""
    from redsl.bridges.redeploy_bridge import run_spec, is_available
    from rich.console import Console

    console = Console()
    if not is_available():
        console.print("[red]✗ redeploy not installed. Run: pip install redeploy[/red]")
        sys.exit(1)

    console.print(f"[bold]run[/bold]  {spec}")
    result = run_spec(
        spec_path=Path(spec),
        dry_run=dry_run,
        plan_only=plan_only,
        do_detect=do_detect,
        plan_out=Path(plan_out) if plan_out else None,
    )

    if "error" in result:
        console.print(f"[red]✗ {result['error']}[/red]")
        sys.exit(1)

    p = result.get("plan", {})
    console.print(f"  [dim]{p.get('from_strategy', '?')}[/dim]"
                  f" → [cyan]{p.get('to_strategy', '?')}[/cyan]"
                  f"  steps={result.get('steps', 0)}"
                  f"  risk={result.get('risk', '?')}"
                  f"  downtime={result.get('estimated_downtime', '?')}")

    if result.get("plan_only"):
        console.print("[dim]--plan-only: stopped before apply[/dim]")
        return

    for r in result.get("results", []):
        icon = "✅" if r["status"] == "done" else ("⏭" if r["status"] == "skipped" else "❌")
        line = f"  {icon} [{r['id']}]"
        if r.get("result"):
            line += f"  {r['result']}"
        if r.get("error"):
            line += f"  [red]{r['error']}[/red]"
        console.print(line)

    console.print(f"\n{result.get('summary', '')}")
    if not result.get("ok", True):
        sys.exit(1)


# ── migrate (detect + plan + apply in one shot) ───────────────────────────────

@deploy.command("migrate")
@click.argument("host")
@click.option("--app", default="app", show_default=True)
@click.option("--domain", default=None)
@click.option("--strategy", default="docker_full", show_default=True,
              type=click.Choice([
                  "docker_full", "native_kiosk", "docker_kiosk",
                  "podman_quadlet", "k3s", "systemd", "unknown",
              ]))
@click.option("--version", "target_version", default=None)
@click.option("--compose", multiple=True)
@click.option("--env-file", default=None)
@click.option("--dry-run", is_flag=True)
@click.option("--infra-out", default=None, type=click.Path(), help="Save infra.yaml")
@click.option("--plan-out", default=None, type=click.Path(), help="Save migration-plan.yaml")
def deploy_migrate(host: str, app: str, domain: str | None, strategy: str,
                   target_version: str | None, compose: tuple[str, ...],
                   env_file: str | None, dry_run: bool,
                   infra_out: str | None, plan_out: str | None) -> None:
    """Full detect → plan → apply on HOST in one command."""
    from redsl.bridges.redeploy_bridge import migrate, is_available
    from rich.console import Console

    console = Console()
    if not is_available():
        console.print("[red]✗ redeploy not installed. Run: pip install redeploy[/red]")
        sys.exit(1)

    prefix = "[DRY RUN] " if dry_run else ""
    console.print(f"[bold]{prefix}migrate[/bold]  {host}  app={app}  strategy={strategy}")

    result = migrate(
        host=host,
        app=app,
        domain=domain,
        strategy=strategy,
        version=target_version,
        compose_files=list(compose) if compose else None,
        env_file=env_file,
        dry_run=dry_run,
        infra_out=Path(infra_out) if infra_out else None,
        plan_out=Path(plan_out) if plan_out else None,
    )

    if "error" in result:
        console.print(f"[red]✗ {result['error']}[/red]")
        sys.exit(1)

    console.print(f"  detected : {result.get('strategy', '?')}")
    console.print(f"  conflicts: {result.get('conflicts', 0)}")
    console.print(f"  steps    : {result.get('steps', 0)}")
    console.print(f"  risk     : {result.get('risk', '?')}")

    for r in result.get("results", []):
        icon = "✅" if r["status"] == "done" else ("⏭" if r["status"] == "skipped" else "❌")
        line = f"  {icon} [{r['id']}]"
        if r.get("result"):
            line += f"  {r['result']}"
        if r.get("error"):
            line += f"  [red]{r['error']}[/red]"
        console.print(line)

    console.print(f"\n{result.get('summary', '')}")
    if not result.get("ok", True):
        sys.exit(1)
