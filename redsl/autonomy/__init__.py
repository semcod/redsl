"""Autonomy package — self-driving quality control for reDSL.

Modules:
  quality_gate    — pre-commit / CI gate that blocks quality regressions
  auto_fix        — automatic violation repair pipeline
  growth_control  — LOC / complexity budget enforcement
  scheduler       — periodic self-improvement loop
  review          — staged-change code review assistant
  smart_scorer    — multi-dimensional decision scoring
  adaptive_executor — runtime strategy adaptation
  intent          — commit intent classification and risk assessment
"""

from __future__ import annotations

from .quality_gate import GateVerdict, run_quality_gate, install_pre_commit_hook
from .growth_control import GrowthBudget, GrowthController, ModuleBudget, check_module_budget
from .review import review_staged_changes
from .intent import analyze_commit_intent
from .smart_scorer import smart_score
from .adaptive_executor import AdaptiveExecutor

__all__ = [
    "GateVerdict",
    "run_quality_gate",
    "install_pre_commit_hook",
    "GrowthBudget",
    "GrowthController",
    "ModuleBudget",
    "check_module_budget",
    "review_staged_changes",
    "analyze_commit_intent",
    "smart_score",
    "AdaptiveExecutor",
]
