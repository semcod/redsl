"""
DSL Engine — standaryzowany język decyzji refaktoryzacji.

Reguły DSL opisują KIEDY i JAK refaktoryzować kod.
Engine ewaluuje warunki, oblicza priorytety i zwraca plan działań.

Format reguły:
    Rule(
        name="split_high_cc",
        conditions=[Condition("cyclomatic_complexity", Operator.GT, 15)],
        action=RefactorAction.EXTRACT_FUNCTIONS,
        priority=0.9,
        description="Rozbij funkcję o CC > 15 na mniejsze"
    )
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Operator(str, Enum):
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    EQ = "eq"
    NEQ = "neq"
    IN = "in"
    CONTAINS = "contains"


class RefactorAction(str, Enum):
    EXTRACT_FUNCTIONS = "extract_functions"
    SPLIT_MODULE = "split_module"
    DEDUPLICATE = "deduplicate"
    RENAME_VARIABLES = "rename_variables"
    ADD_TYPE_HINTS = "add_type_hints"
    REMOVE_DEAD_CODE = "remove_dead_code"
    REDUCE_FAN_OUT = "reduce_fan_out"
    SIMPLIFY_CONDITIONALS = "simplify_conditionals"
    EXTRACT_CLASS = "extract_class"
    INLINE_FUNCTION = "inline_function"
    DO_NOTHING = "do_nothing"


# ---------------------------------------------------------------------------
# Condition & Rule
# ---------------------------------------------------------------------------

@dataclass
class Condition:
    """Pojedynczy warunek DSL."""

    field: str
    operator: Operator
    value: Any

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Ewaluuj warunek na danym kontekście."""
        actual = context.get(self.field)
        if actual is None:
            return False

        match self.operator:
            case Operator.GT:
                return actual > self.value
            case Operator.GTE:
                return actual >= self.value
            case Operator.LT:
                return actual < self.value
            case Operator.LTE:
                return actual <= self.value
            case Operator.EQ:
                return actual == self.value
            case Operator.NEQ:
                return actual != self.value
            case Operator.IN:
                return actual in self.value
            case Operator.CONTAINS:
                return self.value in actual
        return False

    def __repr__(self) -> str:
        return f"{self.field} {self.operator.value} {self.value}"


@dataclass
class Rule:
    """Reguła DSL: warunki → akcja z priorytetem."""

    name: str
    conditions: list[Condition]
    action: RefactorAction
    priority: float = 0.5
    description: str = ""
    tags: list[str] = field(default_factory=list)

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Czy wszystkie warunki są spełnione?"""
        return all(c.evaluate(context) for c in self.conditions)

    def score(self, context: dict[str, Any]) -> float:
        """Oblicz wynik reguły (priorytet * impact)."""
        if not self.evaluate(context):
            return 0.0

        impact = self._calculate_impact(context)
        return self.priority * impact

    def _calculate_impact(self, context: dict[str, Any]) -> float:
        """Heurystyka oceny wpływu refaktoryzacji."""
        impact = 1.0

        cc = context.get("cyclomatic_complexity", 0)
        if cc > 30:
            impact *= 2.0
        elif cc > 20:
            impact *= 1.5

        lines = context.get("module_lines", 0)
        if lines > 500:
            impact *= 1.8
        elif lines > 300:
            impact *= 1.3

        fan = context.get("fan_out", 0)
        if fan > 20:
            impact *= 1.5

        dup = context.get("duplicate_lines", 0)
        if dup > 30:
            impact *= 1.6

        return min(impact, 5.0)


# ---------------------------------------------------------------------------
# Decision (wynik ewaluacji)
# ---------------------------------------------------------------------------

@dataclass
class Decision:
    """Wynik ewaluacji reguł — decyzja co refaktoryzować."""

    rule_name: str
    action: RefactorAction
    score: float
    target_file: str
    target_function: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    rationale: str = ""

    @property
    def should_execute(self) -> bool:
        return self.action != RefactorAction.DO_NOTHING and self.score > 0.0


# ---------------------------------------------------------------------------
# DSL Engine
# ---------------------------------------------------------------------------

class DSLEngine:
    """
    Silnik ewaluacji reguł DSL.

    Przyjmuje zbiór reguł i konteksty plików/funkcji,
    zwraca posortowaną listę decyzji refaktoryzacji.
    """

    def __init__(self) -> None:
        self.rules: list[Rule] = []
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Załaduj domyślny zestaw reguł refaktoryzacji."""
        self.rules = [
            Rule(
                name="split_extreme_cc",
                conditions=[
                    Condition("cyclomatic_complexity", Operator.GT, 30),
                ],
                action=RefactorAction.EXTRACT_FUNCTIONS,
                priority=0.95,
                description="Funkcja o CC > 30 — krytyczna, wymaga natychmiastowego rozbicia",
                tags=["critical", "complexity"],
            ),
            Rule(
                name="split_high_cc",
                conditions=[
                    Condition("cyclomatic_complexity", Operator.GT, 15),
                ],
                action=RefactorAction.EXTRACT_FUNCTIONS,
                priority=0.85,
                description="Funkcja o CC > 15 — rozbij na mniejsze, jednocelowe funkcje",
                tags=["complexity"],
            ),
            Rule(
                name="split_god_module",
                conditions=[
                    Condition("module_lines", Operator.GT, 400),
                    Condition("function_count", Operator.GT, 15),
                ],
                action=RefactorAction.SPLIT_MODULE,
                priority=0.90,
                description="God module — zbyt duży plik z za dużą liczbą funkcji",
                tags=["structure"],
            ),
            Rule(
                name="deduplicate_exact",
                conditions=[
                    Condition("duplicate_similarity", Operator.GTE, 1.0),
                    Condition("duplicate_lines", Operator.GT, 10),
                ],
                action=RefactorAction.DEDUPLICATE,
                priority=0.80,
                description="Dokładne duplikaty kodu — wyciągnij do wspólnego modułu",
                tags=["duplication"],
            ),
            Rule(
                name="deduplicate_structural",
                conditions=[
                    Condition("duplicate_similarity", Operator.GTE, 0.90),
                    Condition("duplicate_lines", Operator.GT, 15),
                ],
                action=RefactorAction.DEDUPLICATE,
                priority=0.70,
                description="Strukturalne duplikaty — zunifikuj wzorzec",
                tags=["duplication"],
            ),
            Rule(
                name="reduce_fan_out",
                conditions=[
                    Condition("fan_out", Operator.GT, 15),
                ],
                action=RefactorAction.REDUCE_FAN_OUT,
                priority=0.75,
                description="Za wysoki fan-out — wprowadź fasadę lub mediator",
                tags=["coupling"],
            ),
            Rule(
                name="split_moderate_cc",
                conditions=[
                    Condition("cyclomatic_complexity", Operator.GT, 10),
                ],
                action=RefactorAction.EXTRACT_FUNCTIONS,
                priority=0.60,
                description="Funkcja o CC > 10 — rozważ wydzielenie mniejszych funkcji",
                tags=["complexity"],
            ),
            Rule(
                name="simplify_branching",
                conditions=[
                    Condition("cyclomatic_complexity", Operator.GT, 10),
                    Condition("nested_depth", Operator.GT, 4),
                ],
                action=RefactorAction.SIMPLIFY_CONDITIONALS,
                priority=0.65,
                description="Głęboko zagnieżdżone warunki — zastosuj early return / guard clauses",
                tags=["complexity", "readability"],
            ),
            Rule(
                name="add_types_to_public_api",
                conditions=[
                    Condition("missing_type_hints", Operator.GT, 5),
                    Condition("is_public_api", Operator.EQ, True),
                ],
                action=RefactorAction.ADD_TYPE_HINTS,
                priority=0.50,
                description="Publiczne API bez typów — dodaj type hints",
                tags=["typing", "quality"],
            ),
        ]

    def add_rule(self, rule: Rule) -> None:
        """Dodaj regułę do silnika."""
        self.rules.append(rule)
        logger.info("Added rule: %s (action=%s, priority=%.2f)", rule.name, rule.action, rule.priority)

    def add_rules_from_yaml(self, rules_data: list[dict]) -> None:
        """Załaduj reguły z formatu YAML/dict."""
        for rd in rules_data:
            conditions = []
            when = rd.get("when", {})
            for field_name, constraint in when.items():
                if isinstance(constraint, dict):
                    for op_str, val in constraint.items():
                        conditions.append(Condition(field_name, Operator(op_str), val))
                else:
                    conditions.append(Condition(field_name, Operator.EQ, constraint))

            then = rd.get("then", {})
            rule = Rule(
                name=rd.get("name", "custom_rule"),
                conditions=conditions,
                action=RefactorAction(then.get("action", "do_nothing")),
                priority=then.get("priority", 0.5),
                description=rd.get("description", ""),
                tags=rd.get("tags", []),
            )
            self.add_rule(rule)

    def evaluate(self, contexts: list[dict[str, Any]]) -> list[Decision]:
        """
        Ewaluuj wszystkie reguły na liście kontekstów.
        Zwraca posortowaną listę decyzji (najwyższy score first).
        """
        decisions: list[Decision] = []

        for ctx in contexts:
            file_path = ctx.get("file_path", "unknown")
            func_name = ctx.get("function_name")

            for rule in self.rules:
                score = rule.score(ctx)
                if score > 0:
                    decisions.append(Decision(
                        rule_name=rule.name,
                        action=rule.action,
                        score=score,
                        target_file=file_path,
                        target_function=func_name,
                        context=ctx,
                        rationale=rule.description,
                    ))

        decisions.sort(key=lambda d: d.score, reverse=True)
        logger.info("Evaluated %d contexts → %d decisions", len(contexts), len(decisions))
        return decisions

    def top_decisions(self, contexts: list[dict[str, Any]], limit: int = 10) -> list[Decision]:
        """Zwróć top-N decyzji — zdeduplikowane po (file, function)."""
        all_decisions = self.evaluate(contexts)
        seen: set[tuple[str, str | None]] = set()
        unique: list[Decision] = []
        for d in all_decisions:
            key = (d.target_file, d.target_function)
            if key not in seen:
                seen.add(key)
                unique.append(d)
            if len(unique) >= limit:
                break
        return unique

    def explain(self, decision: Decision) -> str:
        """Wyjaśnij decyzję w czytelnej formie."""
        lines = [
            f"Decyzja: {decision.action.value}",
            f"Reguła: {decision.rule_name}",
            f"Cel: {decision.target_file}",
        ]
        if decision.target_function:
            lines.append(f"Funkcja: {decision.target_function}")
        lines.append(f"Score: {decision.score:.2f}")
        lines.append(f"Uzasadnienie: {decision.rationale}")
        return "\n".join(lines)
