"""Print a concise LLM configuration banner at the start of CLI commands.

The goal is to make it obvious at every invocation:
* whether `.env` was picked up,
* which LLM model + provider are wired in,
* whether the command actually calls the LLM or stays in direct-refactor mode.

Nothing secret is printed — only presence/absence of API keys.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import click

from redsl.config import AgentConfig


_DIRECT_ACTIONS = (
    "REMOVE_UNUSED_IMPORTS",
    "EXTRACT_CONSTANTS",
    "FIX_MODULE_EXECUTION_BLOCK",
    "ADD_RETURN_TYPES",
)


def _provider_for_model(model: str) -> tuple[str, str]:
    """Return (provider_label, env_var_name) for the given model string."""
    m = model.lower()
    if m.startswith("openrouter/"):
        return "OpenRouter", "OPENROUTER_API_KEY"
    if m.startswith(("x-ai/", "xai/")):
        return "xAI", "XAI_API_KEY"
    if m.startswith("openai/"):
        return "OpenAI", "OPENAI_API_KEY"
    if m.startswith("anthropic/"):
        return "Anthropic", "ANTHROPIC_API_KEY"
    if m.startswith("ollama/"):
        return "Ollama (local)", ""
    if m.startswith("gemini/") or m.startswith("google/"):
        return "Google", "GOOGLE_API_KEY"
    return "auto", "OPENROUTER_API_KEY"


def _find_dotenv() -> Path | None:
    """Locate the .env file that python-dotenv would have picked up.

    python-dotenv walks up from the current working directory; we mirror that.
    """
    cwd = Path.cwd().resolve()
    for parent in (cwd, *cwd.parents):
        candidate = parent / ".env"
        if candidate.is_file():
            return candidate
    return None


def _key_status(env_name: str) -> str:
    if not env_name:
        return "n/a (local model)"
    value = os.getenv(env_name)
    if not value:
        return f"{env_name}=MISSING"
    masked = value[:4] + "***" if len(value) > 4 else "***"
    return f"{env_name}={masked}"


def _dotenv_label(dotenv_path: Path | None) -> str:
    if dotenv_path is not None:
        return str(dotenv_path)
    # No .env found on the walk from CWD — tell the user where we looked.
    return f"not found (searched from {Path.cwd()})"


def print_llm_banner(
    *,
    mode: str = "llm",
    extra_lines: Iterable[str] = (),
) -> None:
    """Print the LLM config banner to stderr.

    Parameters
    ----------
    mode:
        One of ``"llm"`` (command may call LLM), ``"direct"`` (AST-only),
        ``"mixed"`` (LLM + direct fallback), ``"plan"`` (analysis only).
    extra_lines:
        Optional extra status lines to append under the banner.
    """
    config = AgentConfig.from_env()
    model = config.llm.model
    reflection = config.llm.reflection_model
    provider, env_name = _provider_for_model(model)
    dotenv_path = _find_dotenv()

    lines: list[str] = ["reDSL LLM config:"]
    lines.append(f"  .env:        {_dotenv_label(dotenv_path)}")
    lines.append(f"  Model:       {model}")
    if reflection and reflection != model:
        lines.append(f"  Reflection:  {reflection}")
    lines.append(f"  Provider:    {provider}")
    lines.append(f"  API key:     {_key_status(env_name)}")

    if mode == "direct":
        lines.append(
            "  Mode:        DIRECT refactor only (no LLM calls)"
        )
        lines.append(
            "  Actions:     " + ", ".join(_DIRECT_ACTIONS)
        )
    elif mode == "mixed":
        lines.append(
            "  Mode:        LLM-backed refactor + direct fallback"
        )
        lines.append(
            "  Direct:      " + ", ".join(_DIRECT_ACTIONS)
        )
        lines.append(
            "  Router:      llx_router picks a per-action model "
            "(see `redsl cost`); the base model above provides the provider prefix."
        )
    elif mode == "plan":
        lines.append("  Mode:        Planning / analysis (no LLM calls)")
    else:
        lines.append("  Mode:        LLM-backed refactor")
        lines.append(
            "  Router:      llx_router picks a per-action model; "
            "the base model above provides the provider prefix."
        )

    for extra in extra_lines:
        lines.append(f"  {extra}")

    click.echo("\n".join(lines), err=True)


__all__ = ["print_llm_banner"]
