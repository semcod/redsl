"""Testy silnika DSL — ewaluacja reguł, scoring, decyzje."""

import pytest
from app.dsl import Condition, Decision, DSLEngine, Operator, RefactorAction, Rule


class TestCondition:
    def test_gt(self):
        c = Condition("cc", Operator.GT, 15)
        assert c.evaluate({"cc": 20}) is True
        assert c.evaluate({"cc": 10}) is False
        assert c.evaluate({"cc": 15}) is False

    def test_gte(self):
        c = Condition("sim", Operator.GTE, 0.95)
        assert c.evaluate({"sim": 1.0}) is True
        assert c.evaluate({"sim": 0.95}) is True
        assert c.evaluate({"sim": 0.90}) is False

    def test_eq(self):
        c = Condition("is_public", Operator.EQ, True)
        assert c.evaluate({"is_public": True}) is True
        assert c.evaluate({"is_public": False}) is False

    def test_missing_field_returns_false(self):
        c = Condition("missing", Operator.GT, 10)
        assert c.evaluate({}) is False

    def test_contains(self):
        c = Condition("tags", Operator.CONTAINS, "critical")
        assert c.evaluate({"tags": ["critical", "complexity"]}) is True
        assert c.evaluate({"tags": ["low"]}) is False

    def test_in_operator(self):
        c = Condition("action", Operator.IN, ["extract", "split"])
        assert c.evaluate({"action": "extract"}) is True
        assert c.evaluate({"action": "rename"}) is False


class TestRule:
    def test_single_condition_evaluates(self):
        rule = Rule(
            name="test",
            conditions=[Condition("cc", Operator.GT, 15)],
            action=RefactorAction.EXTRACT_FUNCTIONS,
            priority=0.9,
        )
        assert rule.evaluate({"cc": 20}) is True
        assert rule.evaluate({"cc": 10}) is False

    def test_multiple_conditions_all_must_pass(self):
        rule = Rule(
            name="test",
            conditions=[
                Condition("module_lines", Operator.GT, 400),
                Condition("function_count", Operator.GT, 15),
            ],
            action=RefactorAction.SPLIT_MODULE,
            priority=0.9,
        )
        assert rule.evaluate({"module_lines": 500, "function_count": 20}) is True
        assert rule.evaluate({"module_lines": 500, "function_count": 5}) is False
        assert rule.evaluate({"module_lines": 100, "function_count": 20}) is False

    def test_score_zero_when_not_matching(self):
        rule = Rule(
            name="test",
            conditions=[Condition("cc", Operator.GT, 15)],
            action=RefactorAction.EXTRACT_FUNCTIONS,
            priority=0.9,
        )
        assert rule.score({"cc": 10}) == 0.0

    def test_score_positive_when_matching(self):
        rule = Rule(
            name="test",
            conditions=[Condition("cc", Operator.GT, 15)],
            action=RefactorAction.EXTRACT_FUNCTIONS,
            priority=0.9,
        )
        score = rule.score({"cc": 36})
        assert score > 0.0

    def test_higher_cc_gives_higher_impact(self):
        rule = Rule(
            name="test",
            conditions=[Condition("cc", Operator.GT, 15)],
            action=RefactorAction.EXTRACT_FUNCTIONS,
            priority=0.9,
        )
        score_low = rule.score({"cc": 16, "cyclomatic_complexity": 16})
        score_high = rule.score({"cc": 36, "cyclomatic_complexity": 36})
        # Both match but high CC has more impact
        assert score_high >= score_low


class TestDSLEngine:
    def test_default_rules_loaded(self):
        engine = DSLEngine()
        assert len(engine.rules) > 0

    def test_evaluate_returns_sorted_decisions(self):
        engine = DSLEngine()
        contexts = [
            {
                "file_path": "module_a.py",
                "cyclomatic_complexity": 36,
                "fan_out": 26,
                "module_lines": 274,
                "function_name": "_extract_entities",
            },
            {
                "file_path": "module_b.py",
                "cyclomatic_complexity": 5,
                "fan_out": 3,
                "module_lines": 50,
            },
        ]
        decisions = engine.evaluate(contexts)
        assert len(decisions) > 0
        # Decisions should be sorted by score descending
        for i in range(len(decisions) - 1):
            assert decisions[i].score >= decisions[i + 1].score

    def test_no_decisions_for_clean_code(self):
        engine = DSLEngine()
        contexts = [
            {
                "file_path": "clean.py",
                "cyclomatic_complexity": 3,
                "fan_out": 2,
                "module_lines": 50,
                "function_count": 3,
            },
        ]
        decisions = engine.evaluate(contexts)
        assert len(decisions) == 0

    def test_god_module_detected(self):
        engine = DSLEngine()
        contexts = [
            {
                "file_path": "god.py",
                "module_lines": 522,
                "function_count": 20,
                "cyclomatic_complexity": 10,
            },
        ]
        decisions = engine.evaluate(contexts)
        actions = [d.action for d in decisions]
        assert RefactorAction.SPLIT_MODULE in actions

    def test_add_custom_rule(self):
        engine = DSLEngine()
        initial = len(engine.rules)
        engine.add_rule(Rule(
            name="custom",
            conditions=[Condition("custom_metric", Operator.GT, 100)],
            action=RefactorAction.EXTRACT_FUNCTIONS,
            priority=0.5,
        ))
        assert len(engine.rules) == initial + 1

    def test_add_rules_from_yaml(self):
        engine = DSLEngine()
        initial = len(engine.rules)
        engine.add_rules_from_yaml([
            {
                "name": "yaml_rule",
                "when": {"cyclomatic_complexity": {"gt": 50}},
                "then": {"action": "extract_functions", "priority": 0.99},
            }
        ])
        assert len(engine.rules) == initial + 1

    def test_top_decisions_limits_output(self):
        engine = DSLEngine()
        contexts = [
            {
                "file_path": f"file_{i}.py",
                "cyclomatic_complexity": 20 + i,
                "fan_out": 15 + i,
                "module_lines": 300,
            }
            for i in range(10)
        ]
        top = engine.top_decisions(contexts, limit=3)
        assert len(top) <= 3

    def test_explain_decision(self):
        engine = DSLEngine()
        decision = Decision(
            rule_name="split_high_cc",
            action=RefactorAction.EXTRACT_FUNCTIONS,
            score=1.7,
            target_file="parser_rules.py",
            target_function="_extract_entities",
            rationale="CC=36 exceeds limit",
        )
        explanation = engine.explain(decision)
        assert "extract_functions" in explanation
        assert "parser_rules.py" in explanation


class TestDecision:
    def test_should_execute_true(self):
        d = Decision(
            rule_name="test",
            action=RefactorAction.EXTRACT_FUNCTIONS,
            score=1.5,
            target_file="x.py",
        )
        assert d.should_execute is True

    def test_should_execute_false_for_do_nothing(self):
        d = Decision(
            rule_name="test",
            action=RefactorAction.DO_NOTHING,
            score=1.0,
            target_file="x.py",
        )
        assert d.should_execute is False

    def test_should_execute_false_for_zero_score(self):
        d = Decision(
            rule_name="test",
            action=RefactorAction.EXTRACT_FUNCTIONS,
            score=0.0,
            target_file="x.py",
        )
        assert d.should_execute is False
