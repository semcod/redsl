"""CLI commands for model selection (cheapest for coding)."""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table


def register_models(cli: click.Group) -> None:
    """Register model selection commands."""
    cli.add_command(models_group)


@click.group(name="models")
def models_group():
    """Model selection for coding - cheapest suitable model."""
    pass


def _build_selector(min_context: int | None = None, require_tools: bool | None = None):
    """Build ModelSelector with optional overrides."""
    from redsl.llm import get_gate
    from redsl.llm.selection import build_selector, CodingRequirements, CostProfile
    from redsl.llm.gate import ModelAgeGate
    import os

    gate = get_gate()

    # Create a relaxed gate for model selection (don't reject on single source)
    # Keep the same aggregator but with relaxed policy
    relaxed_gate = ModelAgeGate(
        aggregator=gate.agg,
        mode=os.getenv("LLM_POLICY_MODE", "frontier_lag"),
        max_age_days=int(os.getenv("LLM_POLICY_MAX_AGE_DAYS", "180")),
        strict=False,  # Non-strict for selection - use fallback instead of error
        unknown_action="allow",  # Allow models with unknown dates
        min_sources_agree=1,  # Only 1 source needed for selection
        blocklist=gate.blocklist,
        allowlist=gate.allowlist,
        fallback_map=gate.fallback_map,
    )

    # Apply overrides
    if min_context is not None:
        os.environ["LLM_CODING_MIN_CONTEXT"] = str(min_context)
    if require_tools is not None:
        os.environ["LLM_CODING_REQUIRE_TOOL_CALLING"] = "true" if require_tools else "false"

    return build_selector(gate.agg, relaxed_gate)


def _filter_candidates_by_tier(selector, tier: str):
    """Get candidates filtered by tier requirements."""
    candidates = selector.candidates()
    candidates = [c for c in candidates if c.passes_requirements]

    max_cost = selector.tiers.get(tier)
    if max_cost:
        candidates = [
            c for c in candidates
            if c.weighted_cost_per_1m and c.weighted_cost_per_1m <= max_cost
        ]
    return candidates


def _show_all_candidates(selector, tier: str, console: Console) -> None:
    """Display all candidate models in tier."""
    candidates = _filter_candidates_by_tier(selector, tier)

    if not candidates:
        console.print(f"[red]No models found in tier '{tier}'[/red]")
        raise SystemExit(1)

    console.print(f"[bold]Top candidates in tier '{tier}':[/bold]\n")
    for i, pick in enumerate(candidates[:5], 1):
        status = "✓" if i == 1 else f"  [{i}]"
        console.print(
            f"{status} [cyan]{pick.info.id}[/cyan] "
            f"— ${pick.weighted_cost_per_1m:.2f}/1M "
            f"(quality: {pick.quality_score:.0f})"
        )


def _show_selected_model(selector, tier: str, console: Console) -> None:
    """Display the selected model details."""
    pick = selector.pick(tier=tier)
    parts = pick.info.id.split("/", 1)
    provider = parts[0] if len(parts) > 0 else "?"
    model_name = parts[1] if len(parts) > 1 else pick.info.id
    or_status = "✓ Available" if "openrouter" in pick.info.sources else "✗ Not in OpenRouter"

    console.print(f"[green]Selected:[/green] [magenta]{provider}[/magenta]/[bold cyan]{model_name}[/bold cyan]")
    console.print(f"OpenRouter: {or_status}")
    console.print(f"Cost: ${pick.weighted_cost_per_1m:.2f}/1M tokens (weighted)")
    console.print(f"Quality: {pick.quality_score:.0f}/100")
    console.print(f"Context: {pick.info.capabilities.context_length:,}")
    console.print(
        f"Release: {pick.info.release_date.date() if pick.info.release_date else '?' }"
    )
    console.print(f"Sources: {', '.join(pick.info.sources)}")
    console.print(f"Tier: {tier}")


@models_group.command(name="pick-coding")
@click.option(
    "--tier",
    type=click.Choice(["cheap", "balanced", "premium"]),
    default="balanced",
    help="Budget tier for model selection"
)
@click.option(
    "--min-context",
    type=int,
    default=None,
    help="Override minimum context length"
)
@click.option(
    "--require-tools/--no-require-tools",
    default=True,
    help="Require tool calling support"
)
@click.option(
    "--show-all",
    is_flag=True,
    help="Show all candidates, not just the selected one"
)
def pick_coding(tier: str, min_context: int | None, require_tools: bool, show_all: bool):
    """Pokaż jaki model zostałby wybrany dla danego tieru.

    Example:
        redsl models pick-coding --tier cheap
        redsl models pick-coding --tier balanced --min-context 64000
    """
    from redsl.llm.selection import ModelSelectionError

    selector = _build_selector(min_context=min_context, require_tools=require_tools)
    console = Console()

    try:
        if show_all:
            _show_all_candidates(selector, tier, console)
        else:
            _show_selected_model(selector, tier, console)
    except ModelSelectionError as e:
        console.print(f"[red]Selection failed: {e}[/red]")
        raise SystemExit(1)


@models_group.command(name="list-coding")
@click.option(
    "--tier",
    type=click.Choice(["cheap", "balanced", "premium", "all"]),
    default="all",
    help="Filter by budget tier"
)
@click.option(
    "--limit",
    type=int,
    default=20,
    help="Limit number of results"
)
@click.option(
    "--show-rejected/--no-rejected",
    default=False,
    help="Show models that were rejected (for debugging)"
)
@click.option(
    "--sort",
    type=click.Choice(["cost", "quality", "context"]),
    default="cost",
    help="Sort order"
)
@click.option(
    "--source",
    type=click.Choice(["openrouter", "all"]),
    default="openrouter",
    help="Filter by source (default: openrouter only)"
)
def list_coding(tier: str, limit: int, show_rejected: bool, sort: str, source: str):
    """Tabela modeli spełniających wymagania coding, posortowana po cenie.

    Example:
        redsl models list-coding --tier cheap --limit 10
        redsl models list-coding --show-rejected  # debug rejected models
    """
    from redsl.llm.selection import ModelCandidate

    selector = _build_selector()
    candidates = _filter_candidates(
        selector.candidates(), selector, tier, source, show_rejected
    )
    candidates = _sort_candidates(candidates, sort)[:limit]
    _render_model_table(candidates, tier, sort, source)


def _filter_candidates(
    candidates: list, selector, tier: str, source: str, show_rejected: bool
) -> list:
    """Apply filters to candidate list."""
    if not show_rejected:
        candidates = [c for c in candidates if c.passes_requirements]

    if source == "openrouter":
        candidates = [c for c in candidates if "openrouter" in c.info.sources]

    if tier != "all":
        max_cost = selector.tiers.get(tier)
        if max_cost:
            candidates = [
                c for c in candidates
                if c.weighted_cost_per_1m and c.weighted_cost_per_1m <= max_cost
            ]

    return candidates


def _sort_candidates(candidates: list, sort: str) -> list:
    """Sort candidates by specified criteria."""
    if sort == "cost":
        return sorted(candidates, key=lambda c: (c.weighted_cost_per_1m or float('inf')))
    elif sort == "quality":
        return sorted(candidates, key=lambda c: -c.quality_score)
    elif sort == "context":
        return sorted(candidates, key=lambda c: -(c.info.capabilities.context_length or 0))
    return candidates


def _render_model_table(candidates: list, tier: str, sort: str, source: str) -> None:
    """Render the model table output."""
    table = Table(title=f"Coding models — tier={tier}, sort={sort}, source={source}")
    table.add_column("Provider", style="magenta", no_wrap=True)
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("$/1M", justify="right")
    table.add_column("Quality", justify="right")
    table.add_column("Context", justify="right")
    table.add_column("OR", justify="center")
    table.add_column("Status")

    for c in candidates:
        row = _build_table_row(c)
        table.add_row(*row)

    Console().print(table)
    Console().print(f"\n[dim]Showing {len(candidates)} models[/dim]")


def _build_table_row(c) -> tuple:
    """Build a single table row from a candidate."""
    if c.passes_requirements:
        status = "✓"
    else:
        reason = c.rejection_reason or "unknown"
        status = f"✗ {reason[:25]}"

    cost_str = f"${c.weighted_cost_per_1m:.2f}" if c.weighted_cost_per_1m else "?"
    context_str = f"{c.info.capabilities.context_length:,}" if c.info.capabilities.context_length else "?"

    parts = c.info.id.split("/", 1)
    provider = parts[0] if len(parts) > 0 else "?"
    model_name = parts[1] if len(parts) > 1 else c.info.id
    or_available = "✓" if "openrouter" in c.info.sources else "✗"

    return (
        provider,
        model_name,
        cost_str,
        f"{c.quality_score:.0f}" if c.quality_score else "—",
        context_str,
        or_available,
        status,
    )


@models_group.command(name="estimate-cost")
@click.option(
    "--tier",
    type=click.Choice(["cheap", "balanced", "premium"]),
    default="balanced",
    help="Budget tier"
)
@click.option(
    "--input-tokens",
    type=int,
    default=10000,
    help="Estimated input tokens per operation"
)
@click.option(
    "--output-tokens",
    type=int,
    default=2000,
    help="Estimated output tokens per operation"
)
@click.option(
    "--ops-per-day",
    type=int,
    default=100,
    help="Number of operations per day"
)
@click.option(
    "--days",
    type=int,
    default=30,
    help="Number of days to estimate"
)
def estimate_cost(tier: str, input_tokens: int, output_tokens: int, ops_per_day: int, days: int):
    """Estimate monthly cost for given tier and usage pattern.

    Example:
        redsl models estimate-cost --tier cheap --ops-per-day 50
        redsl models estimate-cost --tier premium --input-tokens 50000
    """
    from decimal import Decimal
    from redsl.llm.selection import ModelSelectionError

    selector = _build_selector()
    console = Console()

    try:
        pick = selector.pick(tier=tier)
    except ModelSelectionError as e:
        console.print(f"[red]No models available in tier '{tier}': {e}[/red]")
        raise SystemExit(1)

    if not pick.weighted_cost_per_1m:
        console.print("[red]Selected model has unknown pricing[/red]")
        raise SystemExit(1)

    # Calculate cost per operation
    cost_per_1m = pick.weighted_cost_per_1m

    # Weighted cost per token
    weight_in = Decimal("0.8")
    weight_out = Decimal("0.2")
    cost_per_token = cost_per_1m / Decimal(1_000_000)

    # For weighted calculation, we use the input/output ratio
    # Simplified: treat all tokens as weighted average
    avg_weight = (weight_in * Decimal(input_tokens) + weight_out * Decimal(output_tokens)) / Decimal(input_tokens + output_tokens)
    total_tokens = input_tokens + output_tokens
    cost_per_op = (Decimal(total_tokens) * cost_per_token * avg_weight) / avg_weight

    # Actually, let's recalculate properly:
    # weighted_per_1m = (prompt * 0.8 + completion * 0.2) * 1_000_000
    # So per token: prompt_cost * 0.8 + completion_cost * 0.2
    # Total for operation: input_tokens * prompt_cost + output_tokens * completion_cost

    p = pick.info.pricing
    if p.is_known:
        cost_per_op = (
            Decimal(input_tokens) * p.prompt +
            Decimal(output_tokens) * p.completion
        )
    else:
        # Fallback to weighted estimate
        cost_per_op = Decimal(total_tokens) * cost_per_1m / Decimal(1_000_000)

    daily_cost = cost_per_op * Decimal(ops_per_day)
    monthly_cost = daily_cost * Decimal(days)

    console.print(f"[bold]Cost Estimate for tier '{tier}'[/bold]\n")
    console.print(f"Selected model: [cyan]{pick.info.id}[/cyan]")
    console.print(f"Weighted cost: ${cost_per_1m:.2f}/1M tokens")
    if p.is_known:
        console.print(f"  Input:  ${float(p.prompt) * 1_000_000:.2f}/1M")
        console.print(f"  Output: ${float(p.completion) * 1_000_000:.2f}/1M")
    console.print()
    console.print(f"Usage pattern:")
    console.print(f"  Input tokens:  {input_tokens:,}")
    console.print(f"  Output tokens: {output_tokens:,}")
    console.print(f"  Operations/day: {ops_per_day}")
    console.print()
    console.print(f"Cost breakdown:")
    console.print(f"  Per operation:  ${cost_per_op:.4f}")
    console.print(f"  Per day:        ${daily_cost:.2f}")
    console.print(f"  Per month:      [bold]${monthly_cost:.2f}[/bold]")


@models_group.command(name="config")
def show_coding_config():
    """Show current coding model selection configuration."""
    import os

    console = Console()
    console.print("[bold]Coding Model Selection Configuration[/bold]\n")

    settings = [
        ("LLM_COST_METRIC", "weighted", "Cost metric (weighted/completion/prompt/blended_1m)"),
        ("LLM_COST_WEIGHT_INPUT", "0.8", "Input cost weight"),
        ("LLM_COST_WEIGHT_OUTPUT", "0.2", "Output cost weight"),
        ("LLM_CODING_MIN_CONTEXT", "32768", "Min context length"),
        ("LLM_CODING_REQUIRE_TOOL_CALLING", "true", "Require tool calling"),
        ("LLM_CODING_REQUIRE_JSON_MODE", "false", "Require JSON mode"),
        ("LLM_CODING_REQUIRE_STREAMING", "true", "Require streaming"),
        ("LLM_CODING_MIN_AIDER_SCORE", "30.0", "Min Aider benchmark score"),
        ("LLM_CODING_REQUIRE_QUALITY_SIGNAL", "true", "Require quality signal"),
        ("LLM_CODING_USE_OR_CATEGORY", "true", "Use OpenRouter programming category"),
        ("LLM_CODING_SELECTION_STRATEGY", "cheapest_quality", "Selection strategy"),
        ("LLM_CODING_TIER_CHEAP", "0.50", "Cheap tier max $/1M"),
        ("LLM_CODING_TIER_BALANCED", "3.00", "Balanced tier max $/1M"),
        ("LLM_CODING_TIER_PREMIUM", "15.00", "Premium tier max $/1M"),
        ("LLM_CODING_MAX_COST_PER_CALL_USD", "0.10", "Max cost per call safety limit"),
        ("LLM_CODING_FALLBACK_TO_NEXT_TIER", "true", "Allow tier fallback"),
    ]

    for key, default, description in settings:
        value = os.getenv(key, default)
        is_default = os.getenv(key) is None
        marker = "[dim](default)[/dim]" if is_default else "[green](set)[/green]"
        console.print(f"  [cyan]{key}[/cyan]={value} {marker}")
        console.print(f"    {description}")

    # Known good list
    known_good = os.getenv("LLM_CODING_KNOWN_GOOD", "")
    if known_good:
        console.print(f"\n  [cyan]LLM_CODING_KNOWN_GOOD[/cyan]:")
        for model in known_good.split(",")[:5]:
            console.print(f"    - {model}")
        if len(known_good.split(",")) > 5:
            console.print(f"    ... and {len(known_good.split(',')) - 5} more")

    # Tier mappings
    console.print("\n[bold]Default Tiers by Operation:[/bold]")
    operations = [
        "EXTRACT_FUNCTION",
        "SPLIT_MODULE",
        "ARCHITECTURE_REVIEW",
        "AUTO_FIX",
    ]
    for op in operations:
        tier = os.getenv(f"LLM_DEFAULT_TIER_{op}", "balanced")
        console.print(f"  {op}: {tier}")


__all__ = ["register_models", "models_group"]
