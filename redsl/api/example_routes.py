"""Example scenario endpoints and runner helpers."""

from __future__ import annotations

from typing import Any

from redsl.api.models import ExampleRunRequest

_RUNNERS_CACHE: dict[str, Any] = {}


def _get_runner_map() -> dict[str, Any]:
    """Lazy mapping of example names to their runner factories."""
    return {
        "basic_analysis": lambda: __import__("redsl.examples.basic_analysis", fromlist=["run_basic_analysis_example"]).run_basic_analysis_example,
        "custom_rules": lambda: __import__("redsl.examples.custom_rules", fromlist=["run_custom_rules_example"]).run_custom_rules_example,
        "full_pipeline": lambda: __import__("redsl.examples.full_pipeline", fromlist=["run_full_pipeline_example"]).run_full_pipeline_example,
        "memory_learning": lambda: __import__("redsl.examples.memory_learning", fromlist=["run_memory_learning_example"]).run_memory_learning_example,
        "api_integration": lambda: __import__("redsl.examples.api_integration", fromlist=["run_api_integration_example"]).run_api_integration_example,
        "awareness": lambda: __import__("redsl.examples.awareness", fromlist=["run_awareness_example"]).run_awareness_example,
        "pyqual": lambda: __import__("redsl.examples.pyqual_example", fromlist=["run_pyqual_example"]).run_pyqual_example,
        "audit": lambda: __import__("redsl.examples.audit", fromlist=["run_audit_example"]).run_audit_example,
        "pr_bot": lambda: __import__("redsl.examples.pr_bot", fromlist=["run_pr_bot_example"]).run_pr_bot_example,
        "badge": lambda: __import__("redsl.examples.badge", fromlist=["run_badge_example"]).run_badge_example,
    }


def _get_runner(name: str) -> Any | None:
    """Get or create a cached runner for the given example name."""
    if name not in _RUNNERS_CACHE:
        factory = _get_runner_map().get(name)
        if factory is None:
            return None
        _RUNNERS_CACHE[name] = factory()
    return _RUNNERS_CACHE[name]


def _serialize_example_result(result: dict | None) -> dict[str, Any]:
    """Serialize example result — strip non-JSON-safe objects."""
    safe_result: dict[str, Any] = {}
    for k, v in (result or {}).items():
        if k == "scenario":
            safe_result[k] = v
        elif k == "decisions":
            safe_result[k] = [
                {"action": d.action.value, "target_file": d.target_file, "score": d.score, "rule_name": d.rule_name}
                for d in v
            ]
        elif k in (
            "stats", "base_url", "summary", "results",
            "score", "grade", "metrics", "badge_url",
            "pr", "delta", "risk_flags", "suggestions", "conclusion",
        ):
            safe_result[k] = v
    return safe_result


def _register_example_routes(app: Any) -> None:
    """Endpoints for running and listing packaged example scenarios."""

    @app.get("/examples")
    async def list_examples():
        """List available example scenarios (reads from examples/ directory)."""
        from redsl.examples._common import list_available_examples

        return {"examples": list_available_examples()}

    @app.post("/examples/run")
    async def run_example(req: ExampleRunRequest):
        """Run an example scenario and return its result dict."""
        import contextlib
        import io

        runner = _get_runner(req.name)
        if runner is None:
            from redsl.examples._common import EXAMPLE_REGISTRY

            return {"error": f"Unknown example: {req.name}", "available": list(EXAMPLE_REGISTRY.keys())}

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            result = runner(scenario=req.scenario)

        return {"output": buf.getvalue(), "result": _serialize_example_result(result)}

    @app.get("/examples/{name}/yaml")
    async def get_example_yaml(name: str, scenario: str = "default"):
        """Return the raw YAML scenario data for an example."""
        from redsl.examples._common import load_example_yaml

        try:
            data = load_example_yaml(name, scenario=scenario)
            return data
        except Exception as e:
            return {"error": str(e)}
