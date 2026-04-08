"""Intent — commit intent classification and risk assessment.

Classifies the current working-tree changes into one of:
  refactor / feature / bugfix / test / docs / chore / mixed

and estimates the risk level (low / medium / high) so the scheduler
and quality gate can adapt their behaviour.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_INTENT_KEYWORDS: dict[str, list[str]] = {
    "refactor": [
        "refactor", "extract", "split", "rename", "restructure",
        "simplify", "cleanup", "clean up", "move", "reorganize",
    ],
    "bugfix": [
        "fix", "bug", "error", "crash", "exception", "traceback",
        "regression", "revert", "hotfix", "patch",
    ],
    "feature": [
        "add", "implement", "new", "introduce", "create", "support",
        "enable", "extend", "feature",
    ],
    "test": [
        "test", "spec", "assert", "coverage", "pytest", "unittest",
    ],
    "docs": [
        "doc", "docs", "docstring", "readme", "changelog", "comment",
        "typing", "annotate",
    ],
    "chore": [
        "chore", "bump", "update dep", "upgrade", "version",
        "ci", "config", "lint", "format",
    ],
}

_HIGH_RISK_PATTERNS = [
    r"__init__\.py",
    r"config\.py",
    r"orchestrator\.py",
    r"engine\.py",
    r"api\.py",
    r"cli\.py",
]

_MEDIUM_RISK_PATTERNS = [
    r"bridge\.py",
    r"models?\.py",
    r"executor\.py",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_commit_intent(project_dir: Path) -> dict:
    """Analyse the current working-tree changes and return an intent report.

    Returns a dict with keys:
      intent    — primary intent label
      intents   — list of all detected labels (sorted by strength)
      risk      — "low" | "medium" | "high"
      changed_files — list of changed .py paths
      summary   — human-readable one-liner
    """
    project_dir = Path(project_dir).resolve()

    commit_msgs = _recent_commit_messages(project_dir, n=5)
    changed_files = _changed_python_files(project_dir)

    intent_scores: dict[str, float] = {k: 0.0 for k in _INTENT_KEYWORDS}
    _score_from_messages(commit_msgs, intent_scores)
    _score_from_files(changed_files, intent_scores)

    primary, active = _select_primary_and_active(intent_scores)
    risk = _assess_risk(changed_files, primary)

    return {
        "intent": primary,
        "intents": active,
        "risk": risk,
        "changed_files": changed_files,
        "summary": f"{primary.upper()} ({risk} risk) — {len(changed_files)} file(s) changed",
    }


def _score_from_messages(commit_msgs: list[str], scores: dict[str, float]) -> None:
    for msg in commit_msgs:
        msg_lower = msg.lower()
        for label, keywords in _INTENT_KEYWORDS.items():
            for kw in keywords:
                if kw in msg_lower:
                    scores[label] += 1.0


def _score_from_files(changed_files: list[str], scores: dict[str, float]) -> None:
    for fp in changed_files:
        if "test" in fp or fp.startswith("tests/"):
            scores["test"] += 0.5
        if fp.endswith("_test.py") or fp.startswith("test_"):
            scores["test"] += 0.5


def _select_primary_and_active(scores: dict[str, float]) -> tuple[str, list[str]]:
    primary = max(scores, key=lambda k: scores[k])
    if scores[primary] == 0.0:
        primary = "mixed"
    active = [k for k, v in sorted(scores.items(), key=lambda x: -x[1]) if v > 0]
    if not active:
        active = ["mixed"]
    return primary, active


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _recent_commit_messages(project_dir: Path, n: int = 5) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "log", f"-{n}", "--format=%s"],
            capture_output=True, text=True, cwd=str(project_dir), timeout=10,
        )
        if proc.returncode == 0:
            return [m.strip() for m in proc.stdout.strip().splitlines() if m.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return []


def _changed_python_files(project_dir: Path) -> list[str]:
    paths: set[str] = set()
    for flags in (["--cached"], []):
        try:
            proc = subprocess.run(
                ["git", "diff", "--name-only", *flags],
                capture_output=True, text=True, cwd=str(project_dir), timeout=10,
            )
            if proc.returncode == 0:
                for line in proc.stdout.strip().splitlines():
                    if line.endswith(".py"):
                        paths.add(line.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    return sorted(paths)


def _assess_risk(changed_files: list[str], intent: str) -> str:
    if intent == "bugfix":
        return "high"
    for fp in changed_files:
        name = Path(fp).name
        for pat in _HIGH_RISK_PATTERNS:
            if re.search(pat, name):
                return "high"
        for pat in _MEDIUM_RISK_PATTERNS:
            if re.search(pat, name):
                return "medium"
    if intent in ("refactor", "feature"):
        return "medium"
    return "low"
