"""
API refaktoryzacji — FastAPI + WebSocket.

Endpoints:
- POST /analyze         — analiza projektu
- POST /decide          — ewaluacja reguł DSL
- POST /refactor        — pełny cykl refaktoryzacji
- POST /refactor/plan   — wygeneruj plan bez wykonania
- GET  /memory/stats    — statystyki pamięci
- POST /rules           — dodaj niestandardowe reguły DSL
- GET  /health          — health check
- WS   /ws/refactor     — real-time refactoring z feedbackiem
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    project_dir: str = Field(description="Ścieżka do katalogu projektu")
    project_toon: str | None = Field(None, description="Content pliku project_toon.yaml")
    duplication_toon: str | None = Field(None, description="Content pliku duplication_toon.yaml")
    validation_toon: str | None = Field(None, description="Content pliku validation_toon.yaml")


class RefactorRequest(BaseModel):
    project_dir: str = Field(description="Ścieżka do katalogu projektu")
    max_actions: int = Field(5, description="Maks. liczba refaktoryzacji do wykonania")
    dry_run: bool = Field(True, description="Czy tylko wygenerować propozycje (bez zmian)")
    auto_approve: bool = Field(False, description="Automatyczna akceptacja zmian")
    project_toon: str | None = None
    duplication_toon: str | None = None
    validation_toon: str | None = None
    source_files: dict[str, str] | None = None


class RulesRequest(BaseModel):
    rules: list[dict[str, Any]] = Field(description="Lista reguł DSL w formacie YAML")


class DecisionResponse(BaseModel):
    rule_name: str
    action: str
    score: float
    target_file: str
    target_function: str | None
    rationale: str


class CycleResponse(BaseModel):
    cycle_number: int
    analysis_summary: str
    decisions_count: int
    proposals_generated: int
    proposals_applied: int
    proposals_rejected: int
    errors: list[str]
    decisions: list[DecisionResponse] = []


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app():
    """Tworzenie aplikacji FastAPI."""
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware

    from app.config import AgentConfig
    from app.orchestrator import RefactorOrchestrator

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

    # Globalny orchestrator
    config = AgentConfig.from_env()
    orchestrator = RefactorOrchestrator(config)

    # -- Endpoints --

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "agent": "conscious-refactor",
            "memory": orchestrator.get_memory_stats(),
        }

    @app.post("/analyze")
    async def analyze(req: AnalyzeRequest):
        """Analiza projektu — zwraca metryki i alerty."""
        if req.project_toon:
            result = orchestrator.analyzer.analyze_from_toon_content(
                project_toon=req.project_toon or "",
                duplication_toon=req.duplication_toon or "",
                validation_toon=req.validation_toon or "",
            )
        else:
            result = orchestrator.analyzer.analyze_project(Path(req.project_dir))

        return {
            "total_files": result.total_files,
            "total_lines": result.total_lines,
            "avg_cc": result.avg_cc,
            "critical_count": result.critical_count,
            "alerts": result.alerts,
            "metrics": [m.to_dsl_context() for m in result.metrics[:20]],
        }

    @app.post("/decide")
    async def decide(req: AnalyzeRequest):
        """Ewaluacja reguł DSL — zwraca decyzje bez wykonania."""
        explanation = orchestrator.explain_decisions(Path(req.project_dir))
        return {"explanation": explanation}

    @app.post("/refactor", response_model=CycleResponse)
    async def refactor(req: RefactorRequest):
        """Pełny cykl refaktoryzacji."""
        orchestrator.refactor_engine.config.dry_run = req.dry_run
        orchestrator.refactor_engine.config.auto_approve = req.auto_approve

        if req.project_toon:
            report = orchestrator.run_from_toon_content(
                project_toon=req.project_toon or "",
                duplication_toon=req.duplication_toon or "",
                validation_toon=req.validation_toon or "",
                source_files=req.source_files,
                max_actions=req.max_actions,
            )
        else:
            report = orchestrator.run_cycle(
                Path(req.project_dir),
                max_actions=req.max_actions,
            )

        return CycleResponse(
            cycle_number=report.cycle_number,
            analysis_summary=report.analysis_summary,
            decisions_count=report.decisions_count,
            proposals_generated=report.proposals_generated,
            proposals_applied=report.proposals_applied,
            proposals_rejected=report.proposals_rejected,
            errors=report.errors,
        )

    @app.post("/rules")
    async def add_rules(req: RulesRequest):
        """Dodaj niestandardowe reguły DSL."""
        orchestrator.add_custom_rules(req.rules)
        return {"status": "ok", "rules_count": len(orchestrator.dsl_engine.rules)}

    @app.get("/memory/stats")
    async def memory_stats():
        """Statystyki pamięci agenta."""
        return orchestrator.get_memory_stats()

    @app.websocket("/ws/refactor")
    async def ws_refactor(websocket: WebSocket):
        """WebSocket endpoint dla real-time refaktoryzacji."""
        await websocket.accept()

        try:
            while True:
                data = await websocket.receive_json()
                project_dir = data.get("project_dir", ".")

                await websocket.send_json({"phase": "perceive", "status": "analyzing..."})

                report = orchestrator.run_cycle(
                    Path(project_dir),
                    max_actions=data.get("max_actions", 3),
                )

                await websocket.send_json({
                    "phase": "complete",
                    "cycle": report.cycle_number,
                    "summary": report.analysis_summary,
                    "applied": report.proposals_applied,
                    "errors": report.errors,
                })

        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")

    return app


# Punkt wejścia dla uvicorn
app = create_app()
