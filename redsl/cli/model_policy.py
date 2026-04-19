"""CLI commands for model policy management."""

from __future__ import annotations

import json

import click


def register_model_policy(cli: click.Group) -> None:
    """Register model-policy commands."""
    cli.add_command(model_policy)


@click.group(name="model-policy")
def model_policy():
    """Manage LLM model age and lifecycle policy."""
    pass


@model_policy.command(name="check")
@click.argument("model")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def check_model(model: str, json_output: bool):
    """Check if a model is allowed by policy.

    Example:
        redsl model-policy check gpt-4o
        redsl model-policy check anthropic/claude-3-5-sonnet -j
    """
    from redsl.llm import check_model_policy, ModelRejectedError

    try:
        result = check_model_policy(model)
    except ModelRejectedError as e:
        if json_output:
            click.echo(json.dumps({
                "allowed": False,
                "model": model,
                "reason": str(e),
                "age_days": None,
                "sources_used": [],
            }, indent=2))
        else:
            click.echo(f"Model: {model}")
            click.echo(f"Status: ❌ REJECTED")
            click.echo(f"Reason: {e}")
        raise SystemExit(1)

    if json_output:
        click.echo(json.dumps(result, indent=2))
    else:
        status = "✅ ALLOWED" if result["allowed"] else "❌ REJECTED"
        click.echo(f"Model: {result['model']}")
        click.echo(f"Status: {status}")
        click.echo(f"Reason: {result['reason']}")
        if result["age_days"] is not None:
            click.echo(f"Age: {result['age_days']} days")
        if result["sources_used"]:
            click.echo(f"Sources: {', '.join(result['sources_used'])}")

    if not result["allowed"]:
        raise SystemExit(1)


@model_policy.command(name="list")
@click.option("--max-age", "-a", type=int, help="Filter by max age in days")
@click.option("--provider", "-p", help="Filter by provider (openai, anthropic, google)")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
@click.option("--limit", "-l", type=int, default=50, help="Limit results (default: 50)")
def list_models(max_age: int | None, provider: str | None, json_output: bool, limit: int):
    """List models currently allowed by policy.

    Example:
        redsl model-policy list
        redsl model-policy list --max-age 90 --provider openai
        redsl model-policy list -j | jq '.[] | select(.age_days < 60)'
    """
    from redsl.llm import list_allowed_models, get_gate

    all_allowed = list_allowed_models()
    gate = get_gate()

    models = []
    for model_id in all_allowed:
        info = gate.agg.get(model_id)
        if info is None:
            continue

        # Apply filters
        if provider and not info.id.startswith(f"{provider}/"):
            continue
        if max_age is not None and info.age_days is not None and info.age_days > max_age:
            continue

        decision = gate.check(model_id)
        models.append({
            "id": model_id,
            "provider": info.provider,
            "age_days": info.age_days,
            "sources": list(info.sources),
            "deprecated": info.deprecated,
            "allowed": decision.allowed,
            "reason": decision.reason,
        })

    models = models[:limit]

    if json_output:
        click.echo(json.dumps(models, indent=2))
    else:
        click.echo(f"Found {len(models)} allowed models:")
        for m in models:
            age_str = f"{m['age_days']}d" if m["age_days"] else "unknown"
            click.echo(f"  {m['id']:<40} age={age_str:<8} src={','.join(m['sources'])}")


@model_policy.command(name="refresh")
def refresh_registry():
    """Force refresh model registry from sources."""
    from redsl.llm import get_gate

    gate = get_gate()
    click.echo("Refreshing model registry...")

    try:
        gate.agg.refresh()
        all_models = gate.agg.get_all()
        click.echo(f"✅ Registry refreshed: {len(all_models)} models loaded")

        # Show source breakdown
        sources = {}
        for info in all_models.values():
            for src in info.sources:
                sources[src] = sources.get(src, 0) + 1
        click.echo("\nSources:")
        for src, count in sorted(sources.items()):
            click.echo(f"  {src}: {count} models")

    except Exception as e:
        click.echo(f"❌ Refresh failed: {e}", err=True)
        raise SystemExit(1)


@model_policy.command(name="config")
def show_config():
    """Show current model policy configuration."""
    import os

    click.echo("Current Model Policy Configuration:")
    click.echo("")

    settings = [
        ("LLM_POLICY_MODE", "frontier_lag"),
        ("LLM_POLICY_MAX_AGE_DAYS", "180"),
        ("LLM_POLICY_STRICT", "true"),
        ("LLM_POLICY_UNKNOWN_RELEASE", "deny"),
        ("LLM_POLICY_MIN_SOURCES_AGREE", "2"),
        ("LLM_POLICY_SOURCE_DISAGREEMENT_DAYS", "14"),
        ("LLM_REGISTRY_USE_OPENROUTER", "true"),
        ("LLM_REGISTRY_USE_MODELS_DEV", "true"),
        ("LLM_REGISTRY_USE_OPENAI", "false"),
        ("LLM_REGISTRY_USE_ANTHROPIC", "false"),
    ]

    for key, default in settings:
        value = os.getenv(key, default)
        is_default = os.getenv(key) is None
        marker = "  (default)" if is_default else ""
        click.echo(f"  {key}={value}{marker}")

    click.echo("")

    blocklist = os.getenv("LLM_MODEL_BLOCKLIST", "")
    if blocklist:
        click.echo(f"Blocklist: {blocklist}")
    else:
        click.echo("Blocklist: (empty)")

    allowlist = os.getenv("LLM_MODEL_ALLOWLIST", "")
    if allowlist:
        click.echo(f"Allowlist: {allowlist}")
    else:
        click.echo("Allowlist: (empty)")

    fallback = os.getenv("LLM_MODEL_FALLBACK_MAP", "")
    if fallback:
        click.echo(f"Fallback map: {fallback}")
    else:
        click.echo("Fallback map: (empty)")
