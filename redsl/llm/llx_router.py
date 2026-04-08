"""
Tier 3B — Intelligent Model Router (llx integration).

Wybiera optymalny model LLM na podstawie:
  • akcji refaktoryzacji (DSL)
  • złożoności kodu (CC, liczba linii)
  • pozostałego budżetu (USD)
  • dostępności lokalnych modeli (Ollama)

MODEL_MATRIX determinuje wybór modelu per (action, tier).
Jeśli llx CLI jest dostępne, deleguje routing do llx; w przeciwnym razie
stosuje wewnętrzną macierz decyzji.
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_REFLECTION_MODEL_DEFAULT = "gpt-4o-mini"
_REFLECTION_MODEL_LOCAL = "ollama/llama3"

_PRICES_PER_M_TOKENS: dict[str, float] = {
    "gpt-4o": 15.0,
    "gpt-4o-mini": 0.6,
    "ollama/llama3": 0.0,
    "ollama/mistral": 0.0,
    "anthropic/claude-3.5-sonnet": 9.0,
    "anthropic/claude-3-haiku": 1.25,
}


def _get_refactor_action_enum():
    """Lazy import to avoid circular deps at module load time."""
    from redsl.dsl import RefactorAction
    return RefactorAction


def _build_model_matrix() -> dict[tuple[str, str], str]:
    """Buduj macierz (action_value, tier) → model."""
    return {
        ("extract_functions", "critical"): "gpt-4o",
        ("extract_functions", "high"): "gpt-4o-mini",
        ("extract_functions", "any"): "gpt-4o-mini",
        ("split_module", "critical"): "gpt-4o",
        ("split_module", "high"): "gpt-4o-mini",
        ("split_module", "any"): "gpt-4o-mini",
        ("deduplicate", "any"): "gpt-4o-mini",
        ("deduplicate", "critical"): "gpt-4o-mini",
        ("deduplicate", "high"): "gpt-4o-mini",
        ("add_type_hints", "any"): "gpt-4o-mini",
        ("add_type_hints", "critical"): "gpt-4o-mini",
        ("add_type_hints", "high"): "gpt-4o-mini",
        ("simplify_conditionals", "critical"): "gpt-4o",
        ("simplify_conditionals", "high"): "gpt-4o-mini",
        ("simplify_conditionals", "any"): "gpt-4o-mini",
        ("reduce_fan_out", "critical"): "gpt-4o",
        ("reduce_fan_out", "high"): "gpt-4o-mini",
        ("reduce_fan_out", "any"): "gpt-4o-mini",
        ("rename_for_clarity", "any"): "gpt-4o-mini",
        ("add_docstrings", "any"): "gpt-4o-mini",
    }


_MODEL_MATRIX = _build_model_matrix()


@dataclass
class ModelSelection:
    model: str
    reason: str
    estimated_cost: float
    estimated_tokens: int


def _classify_complexity(context: dict) -> str:
    cc = context.get("cyclomatic_complexity", 0)
    lines = context.get("module_lines", 0)
    if cc > 30 or lines > 500:
        return "critical"
    if cc > 15 or lines > 300:
        return "high"
    return "any"


def _estimate_tokens(context: dict) -> int:
    lines = context.get("module_lines", 100)
    code_tokens = lines * 4
    return code_tokens + 500 + 2000


def _estimate_cost(model: str, tokens: int) -> float:
    price_per_m = _PRICES_PER_M_TOKENS.get(model, 1.0)
    return (tokens / 1_000_000) * price_per_m


def _ollama_available(model: str = "llama3") -> bool:
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as resp:
            if resp.status != 200:
                return False
            data = json.loads(resp.read())
            model_names = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
            return model in model_names
    except Exception:
        return False


def _llx_available() -> bool:
    try:
        result = subprocess.run(["llx", "--version"], capture_output=True, timeout=3)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def select_model(
    action,
    context: dict,
    budget_remaining: float = float("inf"),
) -> ModelSelection:
    """Wybierz optymalny model na podstawie akcji i kontekstu.

    Parameters
    ----------
    action:
        RefactorAction enum value or plain string (action.value).
    context:
        Dict with keys like cyclomatic_complexity, module_lines, etc.
    budget_remaining:
        Remaining USD budget — triggers downgrade if exceeded.
    """
    action_value = action.value if hasattr(action, "value") else str(action)
    tier = _classify_complexity(context)

    model = _MODEL_MATRIX.get(
        (action_value, tier),
        _MODEL_MATRIX.get((action_value, "any"), "gpt-4o-mini"),
    )

    estimated_tokens = _estimate_tokens(context)
    cost = _estimate_cost(model, estimated_tokens)

    if cost > budget_remaining:
        model = "gpt-4o-mini"
        cost = _estimate_cost(model, estimated_tokens)
        if cost > budget_remaining:
            model = _REFLECTION_MODEL_LOCAL
            cost = 0.0

    reason = f"{action_value} with {tier} complexity → {model}"
    return ModelSelection(
        model=model,
        reason=reason,
        estimated_cost=cost,
        estimated_tokens=estimated_tokens,
    )


def select_reflection_model(use_local: bool = False) -> str:
    """Wybierz model do refleksji — zawsze tańszy.

    Jeśli use_local=True i Ollama jest dostępna, zwróć lokalny model.
    """
    if use_local and _ollama_available():
        return _REFLECTION_MODEL_LOCAL
    return _REFLECTION_MODEL_DEFAULT


def estimate_cycle_cost(decisions: list, contexts: list[dict]) -> list[dict]:
    """Szacuj koszt całego cyklu refaktoryzacji — lista per decyzja.

    Returns list of dicts with: action, target_file, model, tokens, cost_usd.
    """
    items = []
    for decision, ctx in zip(decisions, contexts):
        selection = select_model(decision.action, ctx)
        items.append(
            {
                "action": decision.action.value if hasattr(decision.action, "value") else str(decision.action),
                "target_file": getattr(decision, "target_file", "unknown"),
                "model": selection.model,
                "tokens": selection.estimated_tokens,
                "cost_usd": selection.estimated_cost,
                "reason": selection.reason,
            }
        )
    return items


def apply_provider_prefix(model: str, configured_model: str) -> str:
    """Apply provider prefix from configured model to a bare model name.

    If configured_model is 'openrouter/openai/gpt-5.4-mini' and model is
    'gpt-4o-mini', return 'openrouter/openai/gpt-4o-mini'.
    If model already has a prefix (e.g. 'ollama/llama3'), return as-is.
    """
    if "/" in model:
        return model
    if configured_model.startswith("ollama/"):
        return configured_model
    parts = configured_model.split("/")
    if len(parts) >= 3:
        # e.g. openrouter/openai/gpt-X → prefix = openrouter/openai
        prefix = "/".join(parts[:-1])
        return f"{prefix}/{model}"
    if len(parts) == 2:
        # e.g. openrouter/gpt-X → prefix = openrouter
        return f"{parts[0]}/{model}"
    return model


def call_via_llx(messages: list[dict], task_type: str) -> str | None:
    """Deleguj wywołanie LLM do llx CLI jeśli dostępne.

    Returns response string or None if llx unavailable.
    """
    if not _llx_available():
        return None

    try:
        result = subprocess.run(
            [
                "llx", "query",
                "--task", task_type,
                "--budget", "0.05",
                "--stdin",
            ],
            input=json.dumps({"messages": messages}),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("response")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as exc:
        logger.debug("llx call failed: %s", exc)
    return None
