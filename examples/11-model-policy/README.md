# Example 11: Model Policy Gate

Demonstrates how to use ReDSL's model age policy system to ensure only recent, non-deprecated LLMs are used.

## Quick Start

```bash
# 1. Install ReDSL
pip install redsl

# 2. Copy .env.template to .env and configure
# - Set your API keys
# - Adjust LLM_POLICY_MAX_AGE_DAYS (default: 180)
# - Choose LLM_POLICY_MODE: frontier_lag | absolute_age | lifecycle

# 3. Run the example
cd examples/11-model-policy
python main.py
```

## How It Works

The policy system uses **3 data sources** (OpenRouter, models.dev, optional native APIs):

1. **OpenRouter** (`openrouter.ai/api/v1/models`) - public, no auth, ~300 models
2. **models.dev** (`models.dev/api.json`) - community, ~200 models  
3. **Native APIs** (OpenAI/Anthropic) - requires API key, authoritative

### Policy Modes

| Mode | Description | Example with 180 days |
|------|-------------|----------------------|
| `frontier_lag` | Max lag behind newest model (recommended) | GPT-4o allowed, GPT-4 blocked |
| `absolute_age` | Max age from today | Only models <180 days old |
| `lifecycle` | Only check deprecation | Any age, but deprecated blocked |

### Using in Your Code

```python
from redsl.llm import safe_completion, check_model_policy, ModelRejectedError

# Check without calling
result = check_model_policy("gpt-4o")
print(f"Allowed: {result['allowed']}, Reason: {result['reason']}")

# Safe call - raises ModelRejectedError if policy blocks
try:
    response = safe_completion(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello"}]
    )
except ModelRejectedError as e:
    print(f"Model rejected: {e}")

# List all allowed models
from redsl.llm import list_allowed_models
allowed = list_allowed_models()
print(f"Allowed models: {len(allowed)}")
```

### Configuration (.env)

```bash
# Recommended: frontier_lag with 180 days
LLM_POLICY_MODE=frontier_lag
LLM_POLICY_MAX_AGE_DAYS=180
LLM_POLICY_STRICT=true

# Block old models explicitly
LLM_MODEL_BLOCKLIST=gpt-4,gpt-4-0314,gpt-3.5-turbo

# Fallback chain (when strict=false)
LLM_MODEL_FALLBACK_MAP=gpt-4:gpt-4o,gpt-3.5-turbo:gpt-4o-mini
```

## Files

- `main.py` - Example usage
- `policy_check.py` - Standalone policy checker
- `.env.template` - Configuration template
