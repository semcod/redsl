# Model Policy - Quick Start Guide

## Installation & Setup (New Project)

```bash
# 1. Install ReDSL
pip install redsl

# 2. Create .env file
cat > .env << 'EOF'
# API Keys (at least one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Model Policy (frontier_lag = recommended)
LLM_POLICY_MODE=frontier_lag
LLM_POLICY_MAX_AGE_DAYS=180
LLM_POLICY_STRICT=true
LLM_POLICY_MIN_SOURCES_AGREE=1

# Data Sources (2+ recommended)
LLM_REGISTRY_USE_OPENROUTER=true
LLM_REGISTRY_USE_MODELS_DEV=true
EOF

# 3. Verify setup
redsl model-policy config
redsl model-policy refresh
redsl model-policy list --limit 10
```

## Basic Usage

### Check Model Policy

```python
from redsl.llm import check_model_policy

result = check_model_policy("gpt-4o")
print(f"Allowed: {result['allowed']}")
print(f"Reason: {result['reason']}")
print(f"Age: {result['age_days']} days")
```

### Safe Completion (with policy enforcement)

```python
from redsl.llm import safe_completion, ModelRejectedError

try:
    response = safe_completion(
        model="claude-opus-4.7",
        messages=[{"role": "user", "content": "Hello"}]
    )
    print(response.choices[0].message.content)
except ModelRejectedError as e:
    print(f"Model rejected: {e}")
```

### List Allowed Models

```python
from redsl.llm import list_allowed_models

models = list_allowed_models()
print(f"Allowed models: {len(models)}")
for m in models[:10]:
    print(f"  {m}")
```

## CLI Commands

```bash
# Check specific model
redsl model-policy check gpt-4o

# List allowed models
redsl model-policy list --limit 20 --provider openai

# Show configuration
redsl model-policy config

# Refresh registry cache
redsl model-policy refresh

# JSON output for scripting
redsl model-policy check gpt-4o --json-output
```

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_POLICY_MODE` | `frontier_lag` | `frontier_lag`, `absolute_age`, or `lifecycle` |
| `LLM_POLICY_MAX_AGE_DAYS` | `180` | Max age/lag in days |
| `LLM_POLICY_STRICT` | `true` | `true`=error on rejection, `false`=fallback |
| `LLM_POLICY_MIN_SOURCES_AGREE` | `2` | Min sources confirming date (1-3) |
| `LLM_POLICY_UNKNOWN_RELEASE` | `deny` | `deny` or `allow` unknown dates |
| `LLM_MODEL_BLOCKLIST` | `''` | Comma-separated blocked models |
| `LLM_MODEL_ALLOWLIST` | `''` | Comma-separated allowed models |
| `LLM_MODEL_FALLBACK_MAP` | `''` | Format: `old:new,old2:new2` |

## Policy Modes Explained

**frontier_lag** (recommended): Model is allowed if released within N days of the newest model. GPT-4o (2 years old) is rejected because Claude-Opus-4.7 (2 days old) is the frontier.

**absolute_age**: Model is allowed if younger than N days from today. More strict - rejects anything old.

**lifecycle**: Only checks deprecation flag. Most lenient - accepts any age unless deprecated.

## Troubleshooting

**"only 1 source(s) provided date, need 2"**
- Lower `LLM_POLICY_MIN_SOURCES_AGREE=1`
- Or add model to `LLM_MODEL_ALLOWLIST`
- Or enable native provider API

**"not_in_registry"**
- Check model name format (try `provider/model`)
- Run `redsl model-policy refresh`
- Some models may not be in public registries

**Model unexpectedly rejected**
- Check current policy: `redsl model-policy config`
- Verify model age: `redsl model-policy check <model>`
- Adjust `LLM_POLICY_MAX_AGE_DAYS` if needed

## Next Steps

- See full documentation: `docs/model-policy.md`
- Run example: `cd examples/11-model-policy && python main.py`
- Integrate with your code: Replace `litellm.completion()` with `redsl.llm.safe_completion()`
