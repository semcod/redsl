"""Health check endpoint."""

from __future__ import annotations

from typing import Any


def _register_health_route(app: Any, orchestrator: Any) -> None:
    from redsl.execution import get_memory_stats

    @app.get("/health")
    async def health():
        from redsl import __version__

        return {
            "status": "ok",
            "agent": "conscious-refactor",
            "version": __version__,
            "memory": get_memory_stats(orchestrator),
        }
