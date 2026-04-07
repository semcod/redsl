"""
Generator reguł DSL — uczy się wzorców z historii refaktoryzacji.

Punkt 3.3 z planu ewolucji:
- Analizuje zapisy pamięci agenta (udane refaktoryzacje)
- Grupuje wzorce po (action, kontekst metryk)
- Generuje nowe reguły DSL w formacie YAML
- Zapisuje do config/learned_rules.yaml

Użycie:
    from redsl.dsl.rule_generator import RuleGenerator
    gen = RuleGenerator(memory)
    rules = gen.generate(min_support=3)
    gen.save(rules, Path("config/learned_rules.yaml"))
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_METRIC_THRESHOLDS = {
    "cyclomatic_complexity": [5, 10, 15, 20],
    "module_lines": [100, 200, 400],
    "fan_out": [5, 10, 15],
    "function_count": [5, 10, 20],
    "unused_imports": [1, 3, 5],
    "magic_numbers": [1, 3, 5],
}

_MIN_CONFIDENCE = 0.60
_DEFAULT_PRIORITY = 0.70


@dataclass
class LearnedRule:
    """Reguła DSL wygenerowana z wzorców w pamięci."""

    name: str
    action: str
    conditions: list[dict[str, Any]]
    priority: float
    support: int
    confidence: float
    description: str = ""
    tags: list[str] = field(default_factory=list)

    def to_yaml_dict(self) -> dict[str, Any]:
        """Serializuj do formatu YAML kompatybilnego z DSLEngine."""
        return {
            "name": self.name,
            "action": self.action,
            "conditions": self.conditions,
            "priority": round(self.priority, 3),
            "description": self.description or f"Learned rule: {self.name}",
            "tags": self.tags,
            "_meta": {
                "support": self.support,
                "confidence": round(self.confidence, 3),
                "source": "rule_generator",
            },
        }


class RuleGenerator:
    """Generuje nowe reguły DSL z historii refaktoryzacji w pamięci agenta."""

    def __init__(self, memory: Any | None = None) -> None:
        """
        Args:
            memory: AgentMemory instance (lub None → pusty generator)
        """
        self._memory = memory

    def generate(
        self,
        min_support: int = 3,
        min_confidence: float = _MIN_CONFIDENCE,
    ) -> list[LearnedRule]:
        """Wygeneruj reguły DSL z wzorców w pamięci.

        Args:
            min_support:    Min. liczba obserwacji by uznać wzorzec
            min_confidence: Min. confidence (success_rate)

        Returns:
            Lista wygenerowanych reguł, posortowana po priorytecie.
        """
        if self._memory is None:
            logger.warning("RuleGenerator: no memory provided, returning empty rules")
            return []

        patterns = self._extract_patterns()
        rules = self._patterns_to_rules(patterns, min_support, min_confidence)
        rules.sort(key=lambda r: r.priority, reverse=True)

        logger.info("RuleGenerator: generated %d rules (min_support=%d)", len(rules), min_support)
        return rules

    def generate_from_history(
        self,
        history: list[dict[str, Any]],
        min_support: int = 2,
        min_confidence: float = _MIN_CONFIDENCE,
    ) -> list[LearnedRule]:
        """Wygeneruj reguły z bezpośrednio podanej historii (bez memory).

        Args:
            history: Lista dict z kluczami: action, success, details (cc, fan_out, etc.)
            min_support: Min. obserwacje
            min_confidence: Min. success rate

        Returns:
            Lista wygenerowanych reguł.
        """
        patterns = self._history_to_patterns(history)
        rules = self._patterns_to_rules(patterns, min_support, min_confidence)
        rules.sort(key=lambda r: r.priority, reverse=True)
        return rules

    def save(self, rules: list[LearnedRule], output_path: Path) -> None:
        """Zapisz wygenerowane reguły do pliku YAML.

        Args:
            rules:       Lista reguł do zapisania
            output_path: Ścieżka docelowa (np. config/learned_rules.yaml)
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "learned_rules": [r.to_yaml_dict() for r in rules],
            "_meta": {
                "count": len(rules),
                "generator": "RuleGenerator v1",
            },
        }
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2,
                      allow_unicode=True)
        logger.info("Saved %d learned rules to %s", len(rules), output_path)

    def load_and_register(self, rules_path: Path, dsl_engine: Any) -> int:
        """Wczytaj i zarejestruj reguły w DSLEngine.

        Args:
            rules_path: Ścieżka do pliku YAML z regułami
            dsl_engine: Instancja DSLEngine

        Returns:
            Liczba zarejestrowanych reguł.
        """
        if not rules_path.exists():
            logger.debug("Learned rules file not found: %s", rules_path)
            return 0

        with open(rules_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        rules_data = data.get("learned_rules", [])
        if not rules_data:
            return 0

        dsl_engine.add_rules_from_yaml(rules_data)
        logger.info("Registered %d learned rules from %s", len(rules_data), rules_path)
        return len(rules_data)

    def _extract_patterns(self) -> dict[str, list[dict]]:
        """Wyciągnij wzorce z pamięci agenta."""
        patterns: dict[str, list[dict]] = defaultdict(list)

        try:
            history = self._memory.get_action_history() if hasattr(self._memory, "get_action_history") else []
            for entry in history:
                action = entry.get("action", "")
                success = entry.get("success", False)
                details = entry.get("details", {})
                if action and success:
                    patterns[action].append(details)
        except Exception as e:
            logger.warning("Could not extract patterns from memory: %s", e)

        return dict(patterns)

    @staticmethod
    def _history_to_patterns(history: list[dict]) -> dict[str, list[dict]]:
        """Konwertuj płaską historię na wzorce grupowane po akcji."""
        patterns: dict[str, list[dict]] = defaultdict(list)
        for entry in history:
            action = entry.get("action", "")
            if action and entry.get("success", False):
                patterns[action].append(entry.get("details", {}))
        return dict(patterns)

    @staticmethod
    def _patterns_to_rules(
        patterns: dict[str, list[dict]],
        min_support: int,
        min_confidence: float,
    ) -> list[LearnedRule]:
        """Konwertuj wzorce na reguły DSL."""
        rules: list[LearnedRule] = []

        for action, observations in patterns.items():
            if len(observations) < min_support:
                continue

            success_rate = len(observations) / max(len(observations), 1)
            if success_rate < min_confidence:
                continue

            conditions = _derive_conditions(action, observations)
            if not conditions:
                continue

            priority = _DEFAULT_PRIORITY + 0.05 * min(len(observations) / 10, 1.0)

            rules.append(LearnedRule(
                name=f"learned_{action.lower()}_{len(observations)}obs",
                action=action,
                conditions=conditions,
                priority=round(priority, 3),
                support=len(observations),
                confidence=round(success_rate, 3),
                description=f"Auto-learned from {len(observations)} successful {action} refactors",
                tags=["learned", action.lower()],
            ))

        return rules


def _derive_conditions(action: str, observations: list[dict]) -> list[dict]:
    """Wyprowadź warunki DSL z obserwacji dla danej akcji."""
    _action_metric_map = {
        "EXTRACT_FUNCTIONS": "cyclomatic_complexity",
        "SPLIT_MODULE": "module_lines",
        "REMOVE_DEAD_CODE": "fan_out",
        "EXTRACT_CONSTANTS": "magic_numbers",
        "REMOVE_UNUSED_IMPORTS": "unused_imports",
        "ADD_RETURN_TYPES": "missing_return_types",
    }

    metric = _action_metric_map.get(action)
    if not metric:
        return []

    values = [
        obs.get(metric, obs.get("cyclomatic_complexity", 0))
        for obs in observations
        if isinstance(obs.get(metric, obs.get("cyclomatic_complexity")), (int, float))
    ]

    if not values:
        return []

    avg = sum(values) / len(values)
    threshold = _find_nearest_threshold(avg, _METRIC_THRESHOLDS.get(metric, [10]))

    return [{"metric": metric, "operator": "gt", "value": threshold}]


def _find_nearest_threshold(value: float, thresholds: list[int]) -> int:
    """Znajdź najbliższy próg z listy dla podanej wartości."""
    if not thresholds:
        return int(value * 0.8)
    return min(thresholds, key=lambda t: abs(t - value * 0.85))
