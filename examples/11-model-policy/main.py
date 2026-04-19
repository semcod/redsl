#!/usr/bin/env python3
"""
Example: Using ReDSL Model Policy in a new project.

This demonstrates how to:
1. Check model policy without making API calls
2. Use safe_completion() instead of litellm.completion()
3. Handle ModelRejectedError
4. List allowed models
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add redsl to path if running from examples/
examples_dir = Path(__file__).parent
if (examples_dir / ".." / ".." / "redsl").exists():
    sys.path.insert(0, str(examples_dir / ".." / ".."))

from dotenv import load_dotenv

# Load environment from .env file in this directory
load_dotenv(Path(__file__).parent / ".env")

from redsl.llm import (
    check_model_policy,
    list_allowed_models,
    safe_completion,
    ModelRejectedError,
)


def demo_policy_check():
    """Demonstrate checking models against policy."""
    print("=" * 60)
    print("DEMO 1: Policy Check (no API calls made)")
    print("=" * 60)

    test_models = [
        "gpt-4o",
        "openai/gpt-4o",
        "claude-sonnet-4",
        "anthropic/claude-3-5-sonnet-20241022",
        "gpt-4",  # likely blocked
        "gpt-3.5-turbo",  # likely blocked
    ]

    for model in test_models:
        result = check_model_policy(model)
        status = "✅ ALLOWED" if result["allowed"] else "❌ REJECTED"
        print(f"\n{model}")
        print(f"  Status: {status}")
        print(f"  Reason: {result['reason']}")
        if result["age_days"] is not None:
            print(f"  Age: {result['age_days']} days")
        if result["sources_used"]:
            print(f"  Sources: {', '.join(result['sources_used'])}")


def demo_list_allowed():
    """Demonstrate listing all allowed models."""
    print("\n" + "=" * 60)
    print("DEMO 2: List Allowed Models")
    print("=" * 60)

    allowed = list_allowed_models()
    print(f"\nTotal allowed models: {len(allowed)}")
    print(f"First 10 allowed models:")
    for i, model in enumerate(allowed[:10], 1):
        print(f"  {i}. {model}")
    if len(allowed) > 10:
        print(f"  ... and {len(allowed) - 10} more")


def demo_safe_completion():
    """Demonstrate safe completion with policy enforcement."""
    print("\n" + "=" * 60)
    print("DEMO 3: Safe Completion (requires API key)")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  OPENAI_API_KEY not set - skipping API call demo")
        print("   Set your API key in .env to test actual calls")
        return

    # This model should be allowed by frontier_lag policy
    test_model = "gpt-4o-mini"

    print(f"\nTrying safe_completion with model: {test_model}")

    try:
        response = safe_completion(
            model=test_model,
            messages=[{"role": "user", "content": "Say 'Model policy test OK'"}],
            max_tokens=20,
        )
        content = response["choices"][0]["message"]["content"]
        print(f"✅ Success! Response: {content.strip()}")
    except ModelRejectedError as e:
        print(f"❌ Model rejected by policy: {e}")
    except Exception as e:
        print(f"⚠️  API error: {e}")


def demo_strict_mode():
    """Demonstrate strict vs non-strict mode."""
    print("\n" + "=" * 60)
    print("DEMO 4: Policy Configuration Info")
    print("=" * 60)

    print("\nCurrent Policy Settings (from environment):")
    print(f"  LLM_POLICY_MODE: {os.getenv('LLM_POLICY_MODE', 'frontier_lag (default)')}")
    print(f"  LLM_POLICY_MAX_AGE_DAYS: {os.getenv('LLM_POLICY_MAX_AGE_DAYS', '180 (default)')}")
    print(f"  LLM_POLICY_STRICT: {os.getenv('LLM_POLICY_STRICT', 'true (default)')}")
    print(f"  LLM_POLICY_MIN_SOURCES_AGREE: {os.getenv('LLM_POLICY_MIN_SOURCES_AGREE', '2 (default)')}")

    print("\nData Sources:")
    print(f"  OpenRouter: {os.getenv('LLM_REGISTRY_USE_OPENROUTER', 'true')}")
    print(f"  models.dev: {os.getenv('LLM_REGISTRY_USE_MODELS_DEV', 'true')}")
    print(f"  OpenAI Native: {os.getenv('LLM_REGISTRY_USE_OPENAI', 'false')}")
    print(f"  Anthropic Native: {os.getenv('LLM_REGISTRY_USE_ANTHROPIC', 'false')}")

    blocklist = os.getenv("LLM_MODEL_BLOCKLIST", "")
    if blocklist:
        print(f"\nBlocklist: {blocklist}")

    fallback = os.getenv("LLM_MODEL_FALLBACK_MAP", "")
    if fallback:
        print(f"Fallback map: {fallback}")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("ReDSL Model Policy Example")
    print("=" * 60)
    print("\nThis example shows how to use ReDSL's model age policy")
    print("to ensure only recent, non-deprecated LLMs are used.")

    try:
        demo_policy_check()
    except Exception as e:
        print(f"\n⚠️  Policy check failed: {e}")
        print("   This may require network access to fetch model registry.")

    try:
        demo_list_allowed()
    except Exception as e:
        print(f"\n⚠️  List allowed failed: {e}")

    demo_strict_mode()
    demo_safe_completion()

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Configure .env with your API keys")
    print("2. Adjust LLM_POLICY_MAX_AGE_DAYS to your needs")
    print("3. Replace litellm.completion() with redsl.llm.safe_completion()")
    print("4. Handle ModelRejectedError in your error handling")


if __name__ == "__main__":
    main()
