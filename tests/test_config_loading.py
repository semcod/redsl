#!/usr/bin/env python3
"""Test script to verify LLM configuration loading."""

from pathlib import Path
from redsl.config import AgentConfig

# Test 1: Default config
print("Test 1: Default AgentConfig()")
config1 = AgentConfig()
print(f"  LLM model: {config1.llm.model}")
print(f"  LLM provider_key present: {bool(config1.llm.provider_key)}")
print(f"  Reflection rounds: {config1.refactor.reflection_rounds}")
print()

# Test 2: From environment
print("Test 2: AgentConfig.from_env()")
config2 = AgentConfig.from_env()
print(f"  LLM model: {config2.llm.model}")
print(f"  LLM provider_key present: {bool(config2.llm.provider_key)}")
print(f"  Reflection rounds: {config2.refactor.reflection_rounds}")
print()

# Test 3: Check .env file
env_file = Path(".env")
if env_file.exists():
    print("Test 3: .env file contents (relevant lines)")
    content = env_file.read_text()
    for line in content.splitlines():
        if any(key in line for key in ["LLM_MODEL", "OPENROUTER_API_KEY", "OPENAI_API_KEY"]):
            print(f"  {line}")
else:
    print("Test 3: .env file not found")
