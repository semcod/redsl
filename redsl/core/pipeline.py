"""Lightweight Pipeline Pattern — shared across H2/H3/H4 hotspot refactors.

Usage::

    from redsl.core.pipeline import Pipeline, PipelineStep, StepResult

    class MyStep(PipelineStep):
        name = "my_step"
        def can_run(self, ctx: dict) -> bool:
            return True
        def execute(self, ctx: dict) -> StepResult:
            ctx["result"] = do_work(ctx)
            return StepResult(ok=True, data=ctx)

    result = Pipeline([MyStep()]).run({})
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StepResult:
    ok: bool
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class PipelineStep(ABC):
    """Abstract base for a single pipeline step."""

    name: str = ""

    def can_run(self, ctx: dict[str, Any]) -> bool:  # noqa: ARG002
        """Return False to skip this step (default: always run)."""
        return True

    @abstractmethod
    def execute(self, ctx: dict[str, Any]) -> StepResult: ...


@dataclass
class PipelineResult:
    ok: bool
    ctx: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    steps_run: list[str] = field(default_factory=list)


class Pipeline:
    """Run a sequence of PipelineStep objects against a shared context dict."""

    def __init__(self, steps: list[PipelineStep]) -> None:
        self.steps = steps

    def run(self, ctx: dict[str, Any]) -> PipelineResult:
        errors: list[str] = []
        steps_run: list[str] = []
        for step in self.steps:
            if not step.can_run(ctx):
                continue
            result = step.execute(ctx)
            steps_run.append(step.name)
            ctx.update(result.data)
            if not result.ok:
                errors.extend(result.errors)
                break
        return PipelineResult(ok=not errors, ctx=ctx, errors=errors, steps_run=steps_run)
