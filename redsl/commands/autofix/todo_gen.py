"""TODO.md generation for autofix package."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_MAX_TODO_ITEMS = 25
_MAX_GATE_TODO_ITEMS = 10


def _count_todo_issues(todo_file: Path) -> int:
    """Count active TODO items in TODO.md (unchecked items)."""
    if not todo_file.exists():
        return 0
    content = todo_file.read_text(encoding="utf-8")
    # Count - [ ] items (unchecked)
    return len(re.findall(r"^- \[ \]", content, re.MULTILINE))


def _append_gate_violations_to_todo(todo_file: Path, violations: list[str]) -> None:
    """Append gate violations to TODO.md as manual fix items."""
    if not violations:
        return
    lines = ["", "## Quality Gate Violations (manual fixes needed)", ""]
    for v in violations[:_MAX_GATE_TODO_ITEMS]:
        lines.append(f"- [ ] {v}")
    if len(violations) > _MAX_GATE_TODO_ITEMS:
        lines.append(f"- [ ] ... and {len(violations) - _MAX_GATE_TODO_ITEMS} more")
    lines.append("")
    todo_file.write_text(todo_file.read_text(encoding="utf-8") + "\n".join(lines), encoding="utf-8")


def _generate_todo_md(project: Path, metrics: dict, gate_violations: list[str]) -> str:
    """Generate TODO.md content from metrics and gate violations."""
    lines = [
        f"# {project.name} - Refactoring TODO",
        "",
        f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Code Quality Issues",
        "",
    ]

    # Add hotspots from metrics
    hotspots = []
    if metrics.get("functions"):
        hotspots = sorted(
            metrics["functions"],
            key=lambda f: f.get("cc", 0),
            reverse=True
        )[:_MAX_TODO_ITEMS]

    for f in hotspots:
        if f.get("cc", 0) > 5:
            lines.append(f"- [ ] `{f.get('path', 'unknown')}` — CC={f.get('cc', 0)} (complex)")

    # Add gate violations
    if gate_violations:
        lines += ["", "## Quality Gate Violations", ""]
        for v in gate_violations[:_MAX_GATE_TODO_ITEMS]:
            lines.append(f"- [ ] {v}")

    if not hotspots and not gate_violations:
        lines += [
            "",
            "- [x] No issues found — project is clean!",
            "",
        ]

    return "\n".join(lines)
