"""Persistent history for redsl decisions, reflections, and outcomes.

The `.redsl/` directory in each analysed project holds:
- ``history.jsonl``  — append-only stream of every decision, thought,
  reflection, and outcome (including reasons for skipping / rejecting code).

HistoryReader allows querying that stream for duplicate detection, decision
auditing, and routing-improvement analytics.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _default_history_dir(project_dir: Path) -> Path:
    return project_dir / ".redsl"


@dataclass(slots=True)
class HistoryEvent:
    """A single persisted event in the refactor history."""

    event_type: str
    project_dir: str
    cycle_number: int | None = None
    decision_rule: str | None = None
    target_file: str | None = None
    action: str | None = None
    status: str | None = None
    reason: str | None = None
    thought: str | None = None
    reflection: str | None = None
    outcome_reason: str | None = None
    details: dict[str, Any] | None = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class HistoryWriter:
    """Append-only history logger backed by .redsl/history.jsonl."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = Path(project_dir)
        self.history_dir = _default_history_dir(self.project_dir)
        self.history_file = self.history_dir / "history.jsonl"

    def record(self, event: HistoryEvent) -> None:
        self.history_dir.mkdir(parents=True, exist_ok=True)
        payload = asdict(event)
        with self.history_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def record_event(self, event_type: str, **kwargs: Any) -> None:
        self.record(HistoryEvent(event_type=event_type, project_dir=str(self.project_dir), **kwargs))

    def decision_signature(
        self,
        *,
        rule: str,
        target_file: str,
        action: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Build a stable hash for deduplicating similar refactor decisions."""
        payload = {
            "rule": rule,
            "target_file": target_file,
            "action": action,
            "context": context or {},
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def has_recent_signature(self, signature: str, limit: int = 500) -> bool:
        """Return True if a matching decision signature already exists in history."""
        if not self.history_file.exists():
            return False

        lines = self.history_file.read_text(encoding="utf-8").splitlines()[-limit:]
        for line in reversed(lines):
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if payload.get("details", {}).get("signature") == signature:
                return True
        return False


class HistoryReader:
    """Read-only access to .redsl/history.jsonl for querying and dedup."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = Path(project_dir)
        self.history_file = _default_history_dir(self.project_dir) / "history.jsonl"

    def load_events(self) -> list[dict[str, Any]]:
        """Load all events from history file."""
        if not self.history_file.exists():
            return []
        events: list[dict[str, Any]] = []
        for line in self.history_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                logger.debug("Skipping malformed history line")
        return events

    def filter_by_file(self, target_file: str) -> list[dict[str, Any]]:
        """Return events related to a specific file."""
        return [e for e in self.load_events() if e.get("target_file") == target_file]

    def filter_by_type(self, event_type: str) -> list[dict[str, Any]]:
        """Return events of a given type."""
        return [e for e in self.load_events() if e.get("event_type") == event_type]

    def has_recent_proposal(
        self,
        target_file: str,
        action: str,
        *,
        max_age_hours: int = 24,
    ) -> bool:
        """Check if a similar proposal was already generated recently.

        Used by the dedup guard to avoid re-generating the same refactor.
        """
        cutoff = datetime.now(timezone.utc).timestamp() - max_age_hours * 3600
        for ev in reversed(self.load_events()):
            if ev.get("event_type") not in (
                "proposal_generated",
                "proposal_applied",
                "proposal_rejected",
                "proposal_skipped_duplicate",
            ):
                continue
            if ev.get("target_file") != target_file or ev.get("action") != action:
                continue
            try:
                ts = datetime.fromisoformat(ev["created_at"]).timestamp()
            except (KeyError, ValueError):
                continue
            if ts >= cutoff:
                return True
        return False

    def has_recent_ticket(self, title_prefix: str, *, max_age_hours: int = 48) -> bool:
        """Check if a ticket with similar title was created recently."""
        cutoff = datetime.now(timezone.utc).timestamp() - max_age_hours * 3600
        for ev in reversed(self.load_events()):
            if ev.get("event_type") != "ticket_created":
                continue
            ev_title = (ev.get("details") or {}).get("title", "")
            if ev_title.startswith(title_prefix[:40]):
                try:
                    ts = datetime.fromisoformat(ev["created_at"]).timestamp()
                except (KeyError, ValueError):
                    continue
                if ts >= cutoff:
                    return True
        return False

    def generate_decision_report(self) -> str:
        """Generate a Markdown report of all decisions, thoughts and outcomes."""
        events = self.load_events()
        if not events:
            return "# ReDSL Decision History\n\nNo events recorded yet.\n"

        lines = ["# ReDSL Decision History\n"]
        current_cycle: int | None = None

        for ev in events:
            cycle = ev.get("cycle_number")
            if cycle is not None and cycle != current_cycle:
                current_cycle = cycle
                lines.append(f"\n## Cycle {cycle}\n")

            ts = ev.get("created_at", "?")[:19]
            etype = ev.get("event_type", "?")
            target = ev.get("target_file", "")
            action = ev.get("action", "")
            header = f"- **[{ts}] {etype}**"
            if target:
                header += f" `{target}`"
            if action:
                header += f" → {action}"
            lines.append(header)

            if ev.get("thought"):
                lines.append(f"  - 💭 Thought: {ev['thought']}")
            if ev.get("reflection"):
                lines.append(f"  - 🪞 Reflection: {ev['reflection'][:300]}")
            if ev.get("outcome_reason"):
                lines.append(f"  - ❌ Outcome: {ev['outcome_reason']}")
            if ev.get("reason"):
                lines.append(f"  - Reason: {ev['reason']}")

        lines.append("")
        return "\n".join(lines)
