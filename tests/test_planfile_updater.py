"""Tests for planfile_updater — add_decision_tasks, add_quality_task."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from redsl.execution.planfile_updater import add_decision_tasks, add_quality_task


def _make_decision(target_file: str, action: str, score: float = 0.8, rationale: str = "", rule: str = ""):
    d = MagicMock()
    d.target_file = target_file
    action_mock = MagicMock()
    action_mock.value = action
    d.action = action_mock
    d.score = score
    d.rationale = rationale
    d.rule_name = rule
    return d


# ---------------------------------------------------------------------------
# add_decision_tasks
# ---------------------------------------------------------------------------

class TestAddDecisionTasks:
    def test_creates_planfile_when_missing(self, tmp_path: Path) -> None:
        decisions = [_make_decision("foo/bar.py", "extract_functions", score=0.9)]
        added = add_decision_tasks(tmp_path, decisions)
        assert added == 1
        planfile = tmp_path / "planfile.yaml"
        assert planfile.exists()
        data = yaml.safe_load(planfile.read_text())
        tasks = data["tasks"]
        assert len(tasks) == 1
        t = tasks[0]
        assert t["status"] == "todo"
        assert t["action"] == "extract_functions"
        assert t["file"] == "foo/bar.py"
        assert t["score"] == 0.9
        assert t["source"] == "redsl:dry_run"

    def test_appends_to_existing_planfile(self, tmp_path: Path) -> None:
        planfile = tmp_path / "planfile.yaml"
        planfile.write_text(yaml.dump({"tasks": [
            {"id": "t1", "status": "todo", "action": "rename", "file": "a.py"}
        ]}))
        decisions = [_make_decision("b.py", "extract_functions")]
        added = add_decision_tasks(tmp_path, decisions)
        assert added == 1
        data = yaml.safe_load(planfile.read_text())
        assert len(data["tasks"]) == 2

    def test_skips_duplicate_file_action(self, tmp_path: Path) -> None:
        planfile = tmp_path / "planfile.yaml"
        planfile.write_text(yaml.dump({"tasks": [
            {"id": "t1", "status": "todo", "action": "extract_functions", "file": "a.py"}
        ]}))
        decisions = [_make_decision("a.py", "extract_functions")]
        added = add_decision_tasks(tmp_path, decisions)
        assert added == 0

    def test_does_not_skip_different_action(self, tmp_path: Path) -> None:
        planfile = tmp_path / "planfile.yaml"
        planfile.write_text(yaml.dump({"tasks": [
            {"id": "t1", "status": "todo", "action": "rename", "file": "a.py"}
        ]}))
        decisions = [_make_decision("a.py", "extract_functions")]
        added = add_decision_tasks(tmp_path, decisions)
        assert added == 1

    def test_empty_decisions_returns_zero(self, tmp_path: Path) -> None:
        assert add_decision_tasks(tmp_path, []) == 0

    def test_sets_rationale_as_description(self, tmp_path: Path) -> None:
        d = _make_decision("x.py", "split_module", rationale="Too complex function")
        add_decision_tasks(tmp_path, [d])
        data = yaml.safe_load((tmp_path / "planfile.yaml").read_text())
        assert data["tasks"][0]["description"] == "Too complex function"

    def test_custom_source_and_priority(self, tmp_path: Path) -> None:
        d = _make_decision("x.py", "remove_dead_code")
        add_decision_tasks(tmp_path, [d], source="redsl:batch", priority=1)
        data = yaml.safe_load((tmp_path / "planfile.yaml").read_text())
        t = data["tasks"][0]
        assert t["source"] == "redsl:batch"
        assert t["priority"] == 1

    def test_works_with_new_schema_planfile(self, tmp_path: Path) -> None:
        planfile = tmp_path / "planfile.yaml"
        planfile.write_text(yaml.dump({
            "apiVersion": "redsl.plan/v1",
            "spec": {"tasks": []}
        }))
        decisions = [_make_decision("m.py", "add_type_hints")]
        added = add_decision_tasks(tmp_path, decisions)
        assert added == 1
        data = yaml.safe_load(planfile.read_text())
        assert len(data["spec"]["tasks"]) == 1


# ---------------------------------------------------------------------------
# add_quality_task
# ---------------------------------------------------------------------------

class TestAddQualityTask:
    def test_creates_task(self, tmp_path: Path) -> None:
        result = add_quality_task(tmp_path, title="Fix gates", description="gates failed", priority=2)
        assert result is True
        data = yaml.safe_load((tmp_path / "planfile.yaml").read_text())
        t = data["tasks"][0]
        assert t["title"] == "Fix gates"
        assert t["status"] == "todo"
        assert t["source"] == "redsl:pyqual_gates"

    def test_skips_duplicate_todo_title(self, tmp_path: Path) -> None:
        add_quality_task(tmp_path, title="Fix gates")
        result = add_quality_task(tmp_path, title="Fix gates")
        assert result is False
        data = yaml.safe_load((tmp_path / "planfile.yaml").read_text())
        assert len(data["tasks"]) == 1

    def test_allows_same_title_if_done(self, tmp_path: Path) -> None:
        planfile = tmp_path / "planfile.yaml"
        planfile.write_text(yaml.dump({"tasks": [
            {"id": "q1", "title": "Fix gates", "status": "done"}
        ]}))
        result = add_quality_task(tmp_path, title="Fix gates")
        assert result is True
