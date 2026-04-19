# Model Age Policy

ReDSL includes a built-in system to enforce LLM model age and lifecycle policies, ensuring only recent, non-deprecated models are used in your pipelines.

## Overview

The policy system prevents usage of:
- **Old models** (beyond configured age limit)
- **Deprecated models** (marked by providers)
- **Blocklisted models** (explicitly forbidden)

It uses **3 data sources** for maximum reliability:
1. **OpenRouter** (`openrouter.ai/api/v1/models`) - public, ~300 models
2. **models.dev** (`models.dev/api.json`) - community, ~200 models
3. **Native APIs** (OpenAI/Anthropic) - authoritative when API keys provided

## Quick Start

### 1. Configure Environment

```bash
# .env
LLM_POLICY_MODE=frontier_lag
LLM_POLICY_MAX_AGE_DAYS=180
LLM_POLICY_STRICT=true
LLM_POLICY_MIN_SOURCES_AGREE=2

LLM_REGISTRY_USE_OPENROUTER=true
LLM_REGISTRY_USE_MODELS_DEV=true
LLM_REGISTRY_CACHE_PATH=/tmp/redsl_registry.json
```

### 2. Use in Code

```python
from redsl.llm import safe_completion, check_model_policy, ModelRejectedError

# Check without API call
result = check_model_policy("gpt-4o")
print(f"Allowed: {result['allowed']}, Reason: {result['reason']}")

# Safe completion with policy enforcement
try:
    response = safe_completion(
        model="claude-opus-4.7",
        messages=[{"role": "user", "content": "Hello"}]
    )
except ModelRejectedError as e:
    print(f"Model rejected: {e}")
```

### 3. CLI Usage

```bash
# Check a model
redsl model-policy check gpt-4o

# List allowed models
redsl model-policy list --limit 20

# Show configuration
redsl model-policy config

# Refresh registry cache
redsl model-policy refresh
```

## Policy Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `frontier_lag` | Max lag behind newest model (default) | Balance stability and freshness |
| `absolute_age` | Max age from today | Strict bleeding-edge requirement |
| `lifecycle` | Only check deprecation | Lenient, production-safe |

### Example with 180 days

**frontier_lag** (recommended): A model released 200 days ago is allowed if the newest model is only 20 days newer.

**absolute_age**: A model released 200 days ago is rejected because it's >180 days old.

## Configuration Reference

```bash
# =============================================================================
# POLICY SETTINGS
# =============================================================================

# Policy mode: frontier_lag | absolute_age | lifecycle
LLM_POLICY_MODE=frontier_lag

# Maximum age/lag in days
LLM_POLICY_MAX_AGE_DAYS=180

# Strict mode: true = raise error on rejection, false = use fallback
LLM_POLICY_STRICT=true

# Action when release date unknown: deny | allow
LLM_POLICY_UNKNOWN_RELEASE=deny

# Minimum sources agreeing on date (1-3)
LLM_POLICY_MIN_SOURCES_AGREE=2

# Max date disagreement between sources before warning (days)
LLM_POLICY_SOURCE_DISAGREEMENT_DAYS=14

# =============================================================================
# REGISTRY SOURCES
# =============================================================================

LLM_REGISTRY_USE_OPENROUTER=true
LLM_REGISTRY_USE_MODELS_DEV=true
LLM_REGISTRY_USE_OPENAI=false
LLM_REGISTRY_USE_ANTHROPIC=false

# =============================================================================
# CACHE
# =============================================================================

LLM_REGISTRY_CACHE_PATH=/tmp/redsl_registry.json
LLM_REGISTRY_CACHE_TTL_SECONDS=21600      # 6 hours
LLM_REGISTRY_CACHE_STALE_GRACE_SECONDS=604800  # 7 days

# =============================================================================
# OVERRIDES
# =============================================================================

# Always block (comma-separated)
LLM_MODEL_BLOCKLIST=gpt-4,gpt-4-0314,gpt-3.5-turbo

# Always allow (comma-separated)
LLM_MODEL_ALLOWLIST=

# Fallback map: old_model:new_model,comma-separated
LLM_MODEL_FALLBACK_MAP=gpt-4:gpt-4o,gpt-3.5-turbo:gpt-4o-mini
```

## API Reference

### Functions

```python
from redsl.llm import (
    safe_completion,      # Drop-in litellm.completion replacement
    check_model_policy,   # Check without API call
    list_allowed_models,  # List all allowed models
    ModelRejectedError,   # Exception raised on rejection
    get_gate,             # Access the ModelAgeGate directly
)
```

### safe_completion

```python
def safe_completion(model: str, **kwargs) -> dict:
    """
    Drop-in replacement for litellm.completion with policy enforcement.

    Args:
        model: Model identifier (e.g., "gpt-4o", "anthropic/claude-opus-4")
        **kwargs: Passed to litellm.completion

    Returns:
        LiteLLM completion response

    Raises:
        ModelRejectedError: If model violates policy (strict mode)
    """
```

### check_model_policy

```python
def check_model_policy(model: str) -> dict:
    """
    Check if model is allowed without making API call.

    Returns dict with keys:
        - allowed: bool
        - model: str (normalized model ID)
        - reason: str
        - age_days: int | None
        - sources_used: list[str]
    """
```

## Integration Examples

### With LLMLayer

```python
from redsl.llm import LLMLayer, safe_completion
from redsl.config import LLMConfig

config = LLMConfig(model="gpt-4o")
layer = LLMLayer(config)

# Use safe_completion instead of layer.call() for policy enforcement
response = safe_completion(
    model=config.model,
    messages=[{"role": "user", "content": "Refactor this code"}]
)
```

### Fallback Chain

```python
# .env
LLM_POLICY_STRICT=false
LLM_MODEL_FALLBACK_MAP=gpt-4o:gpt-4o-mini,claude-opus-4:claude-sonnet-4

# Code - will automatically fallback if policy rejects
try:
    response = safe_completion(model="gpt-4o", messages=[...])
except ModelRejectedError:
    # Fallback didn't work either
    pass
```

### Testing Mode

```python
# Allow unknown models in CI/dev when network unavailable
# .env
LLM_POLICY_UNKNOWN_RELEASE=allow
LLM_POLICY_MIN_SOURCES_AGREE=1
```

## Troubleshooting

### Model rejected: "only 1 source(s) provided date, need 2"

Some models only appear in one registry. Options:
1. Lower `LLM_POLICY_MIN_SOURCES_AGREE=1`
2. Add the model to `LLM_MODEL_ALLOWLIST`
3. Enable native provider API for authoritative source

### "not_in_registry"

Model not found in any configured source. Check:
1. Model name format (try `provider/model` format)
2. Registry sources are enabled
3. Run `redsl model-policy refresh` to update cache

### Cache stale errors

If network fails and cache is >7 days old:
1. Set `LLM_POLICY_UNKNOWN_RELEASE=allow` temporarily
2. Or increase `LLM_REGISTRY_CACHE_STALE_GRACE_SECONDS`

## Security Considerations

1. **Production**: Use `LLM_POLICY_STRICT=true` and `LLM_POLICY_UNKNOWN_RELEASE=deny`
2. **Blocklist**: Explicitly block known deprecated models
3. **Fallbacks**: Configure fallback chain to newer models
4. **Cache**: Protect cache file from tampering (signed cache coming soon)
