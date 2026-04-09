from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

import yaml

# Maps CLI-friendly names to example directory names
EXAMPLE_REGISTRY: dict[str, str] = {
    "basic_analysis": "01-basic-analysis",
    "custom_rules": "02-custom-rules",
    "full_pipeline": "03-full-pipeline",
    "memory_learning": "04-memory-learning",
    "api_integration": "05-api-integration",
    "awareness": "06-awareness",
    "pyqual": "07-pyqual",
    "audit": "08-audit",
    "pr_bot": "09-pr-bot",
    "badge": "10-badge",
}


def _examples_root() -> Path:
    """Return the absolute path to the top-level ``examples/`` directory."""
    env = os.environ.get("REDSL_EXAMPLES_DIR")
    if env:
        return Path(env)
    # redsl/examples/_common.py  →  redsl/  →  repo root
    return Path(__file__).resolve().parent.parent.parent / "examples"


def _resolve_yaml_path(example_name: str, scenario: str = "default") -> Path:
    """Resolve the YAML path inside ``examples/<dir>/<scenario>.yaml``."""
    dir_name = EXAMPLE_REGISTRY.get(example_name, example_name)
    root = _examples_root()
    yaml_file = root / dir_name / f"{scenario}.yaml"
    if not yaml_file.exists():
        raise FileNotFoundError(
            f"Scenario YAML not found: {yaml_file}  "
            f"(examples root: {root}, name: {example_name}, scenario: {scenario})"
        )
    return yaml_file


def load_example_yaml(
    example_name: str,
    scenario: str = "default",
    source: str | Path | None = None,
) -> dict[str, Any]:
    if source is not None:
        yaml_path = Path(source)
    else:
        yaml_path = _resolve_yaml_path(example_name, scenario)

    text = yaml_path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping for {example_name}")
    return data


def list_available_examples() -> list[dict[str, Any]]:
    """Return metadata for every example that has at least a ``default.yaml``."""
    root = _examples_root()
    items: list[dict[str, Any]] = []
    for key, dir_name in sorted(EXAMPLE_REGISTRY.items(), key=lambda kv: kv[1]):
        default_yaml = root / dir_name / "default.yaml"
        if not default_yaml.exists():
            continue
        data = yaml.safe_load(default_yaml.read_text(encoding="utf-8"))
        title = data.get("title", key) if isinstance(data, dict) else key
        has_advanced = (root / dir_name / "advanced.yaml").exists()
        items.append({"name": key, "dir": dir_name, "title": title, "has_advanced": has_advanced})
    return items


def print_banner(title: str, width: int = 60, char: str = "=") -> None:
    line = (char[:1] or "=") * width
    print(line)
    print(f"  {title}")
    print(line)


def parse_scenario(argv: list[str] | None = None) -> str:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "--scenario",
        choices=["default", "advanced"],
        default="default",
        help="Example scenario to run",
    )
    return parser.parse_args(argv).scenario
