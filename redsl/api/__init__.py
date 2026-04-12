"""
ReDSL REST API — FastAPI endpoints mirroring CLI commands.

Endpoints:
- POST /refactor            — Run refactoring on a project
- POST /batch/semcod        — Batch refactor semcod projects
- POST /batch/hybrid        — Hybrid quality refactoring (no LLM)
- GET  /debug/config        — Get configuration info
- GET  /debug/decisions     — Get DSL decisions for a project
- POST /pyqual/analyze      — Python code quality analysis
- POST /pyqual/fix          — Apply automatic quality fixes
- GET  /examples            — List packaged example scenarios
- POST /examples/run        — Run a packaged example scenario
- GET  /examples/{name}/yaml — Get raw YAML data for an example
- GET  /health              — Health check
"""

from __future__ import annotations

import logging

from redsl.orchestrator import RefactorOrchestrator

logger = logging.getLogger(__name__)


def _build_api_orchestrator():
    from redsl.config import AgentConfig

    return RefactorOrchestrator(AgentConfig.from_env())


_get_orchestrator = _build_api_orchestrator


def create_app():
    """Tworzenie aplikacji FastAPI."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    from redsl.api.debug_routes import _register_debug_routes
    from redsl.api.example_routes import _register_example_routes
    from redsl.api.health_routes import _register_health_route
    from redsl.api.pyqual_routes import _register_pyqual_routes
    from redsl.api.refactor_routes import _register_refactor_routes
    from redsl.api.webhook_routes import _register_webhook_routes

    app = FastAPI(
        title="Conscious Refactor Agent",
        description="Autonomiczny system refaktoryzacji kodu z LLM, pamięcią i DSL",
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    orchestrator = _build_api_orchestrator()
    _register_health_route(app, orchestrator)
    _register_refactor_routes(app, orchestrator)
    _register_debug_routes(app, orchestrator)
    _register_pyqual_routes(app)
    _register_webhook_routes(app)
    _register_example_routes(app)
    return app


app = create_app()
