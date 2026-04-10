"""Debug information formatters."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from rich.syntax import Syntax

from .core import console


def format_debug_info(info: Dict[str, Any], format: str = "text") -> str:
    """Format debug information."""
    if format == "yaml":
        import yaml
        return yaml.dump(info, default_flow_style=False, sort_keys=False)
    elif format == "json":
        return json.dumps(info, indent=2, default=str)
    else:
        # Rich text format with syntax highlighting
        output = ["\n=== DEBUG INFORMATION ===\n"]

        for key, value in info.items():
            if isinstance(value, (dict, list)):
                output.append(f"{key}:")
                if format == "text":
                    value_str = json.dumps(value, indent=2, default=str)
                    syntax = Syntax(value_str, "json", theme="monokai", line_numbers=True)
                    with console.capture() as capture:
                        console.print(syntax)
                    output.append(capture.get())
            else:
                output.append(f"{key}: {value}")

        return "\n".join(output)
