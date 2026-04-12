"""Debug configuration and decisions endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _register_debug_routes(app: Any, orchestrator: Any) -> None:

    @app.get("/debug/config")
    async def debug_config(show_env: bool = False):
        """Get configuration info."""
        from redsl.config import AgentConfig

        config = AgentConfig.from_env()
        info = {
            "llm_model": config.llm.model,
            "dry_run": config.refactor.dry_run,
            "max_iterations": config.refactor.max_iterations,
            "reflection_rounds": config.refactor.reflection_rounds,
        }

        if show_env:
            import os

            info["env_vars"] = {
                k: v
                for k, v in os.environ.items()
                if k.startswith(("REFACTOR_", "OPENAI_", "OPENROUTER_"))
            }

        return info

    @app.get("/debug/decisions")
    async def debug_decisions(project_path: str, limit: int = 20):
        """Get DSL decisions for a project."""
        analysis = orchestrator.analyzer.analyze_project(Path(project_path))
        contexts = analysis.to_dsl_contexts()
        decisions = orchestrator.dsl_engine.evaluate(contexts)
        decisions = sorted(decisions, key=lambda d: d.score, reverse=True)[:limit]

        return {
            "project_path": project_path,
            "total_decisions": len(decisions),
            "decisions": [
                {
                    "action": d.action.value,
                    "target": str(d.target_file),
                    "score": d.score,
                    "rule": d.rule_name,
                    "rationale": getattr(d, "rationale", ""),
                }
                for d in decisions
            ],
        }
