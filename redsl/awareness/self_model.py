"""Agent self-model for introspection and capability tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from redsl.memory import AgentMemory


@dataclass(slots=True)
class CapabilityStat:
    """Track how well the agent performs a capability."""

    name: str
    attempts: int = 0
    successes: int = 0
    failures: int = 0
    notes: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.attempts == 0:
            return 0.0
        return round(self.successes / self.attempts, 3)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "attempts": self.attempts,
            "successes": self.successes,
            "failures": self.failures,
            "success_rate": self.success_rate,
            "notes": list(self.notes),
        }


@dataclass(slots=True)
class AgentCapabilityProfile:
    """Structured self-assessment summary."""

    name: str
    overall_confidence: float
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    capabilities: list[CapabilityStat] = field(default_factory=list)
    recommended_focus: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "overall_confidence": self.overall_confidence,
            "strengths": list(self.strengths),
            "weaknesses": list(self.weaknesses),
            "capabilities": [cap.to_dict() for cap in self.capabilities],
            "recommended_focus": list(self.recommended_focus),
        }


class SelfModel:
    """Introspective model backed by agent memory."""

    def __init__(self, memory: AgentMemory | None = None) -> None:
        self.memory = memory or AgentMemory()
        self.capabilities: dict[str, CapabilityStat] = {}

    def record_outcome(
        self,
        capability: str,
        success: bool,
        details: str = "",
        target: str = "",
    ) -> CapabilityStat:
        stat = self.capabilities.setdefault(capability, CapabilityStat(name=capability))
        stat.attempts += 1
        if success:
            stat.successes += 1
        else:
            stat.failures += 1
        if details:
            stat.notes.append(details)
        self.memory.remember_action(
            action=capability,
            target=target or capability,
            result=details or ("success" if success else "failure"),
            success=success,
            details={"capability": capability},
        )
        return stat

    def assess(self, top_k: int = 5) -> AgentCapabilityProfile:
        capabilities = sorted(self.capabilities.values(), key=lambda stat: stat.success_rate, reverse=True)
        strengths = [cap.name for cap in capabilities if cap.success_rate >= 0.75]
        weaknesses = [cap.name for cap in capabilities if cap.success_rate < 0.5]
        recommended_focus = weaknesses[:top_k]
        overall_confidence = self._overall_confidence(capabilities)
        return AgentCapabilityProfile(
            name="redsl-self-model",
            overall_confidence=overall_confidence,
            strengths=strengths,
            weaknesses=weaknesses,
            capabilities=capabilities[:top_k],
            recommended_focus=recommended_focus,
        )

    def summarize(self) -> dict[str, Any]:
        profile = self.assess()
        return profile.to_dict()

    @staticmethod
    def _overall_confidence(capabilities: list[CapabilityStat]) -> float:
        if not capabilities:
            return 0.0
        total_attempts = sum(cap.attempts for cap in capabilities)
        if total_attempts == 0:
            return 0.0
        weighted = sum(cap.success_rate * cap.attempts for cap in capabilities)
        return round(weighted / total_attempts, 3)


__all__ = ["CapabilityStat", "AgentCapabilityProfile", "SelfModel"]
