"""
ReDSL REST API — FastAPI endpoints mirroring CLI commands.

Endpoints:
- POST /refactor        — Run refactoring on a project
- POST /batch/semcod    — Batch refactor semcod projects
- POST /batch/hybrid    — Hybrid quality refactoring (no LLM)
- GET  /debug/config    — Get configuration info
- GET  /debug/decisions — Get DSL decisions for a project
- POST /pyqual/analyze  — Python code quality analysis
- POST /pyqual/fix      — Apply automatic quality fixes
- GET  /health          — Health check
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
    project_path: str = Field(description="Path to project directory")
    max_actions: int = Field(10, description="Maximum number of actions to apply")
    dry_run: bool = Field(True, description="Show what would be done without applying changes")
    format: str = Field("text", description="Output format: text, yaml, or json")


class BatchSemcodRequest(BaseModel):
    semcod_root: str = Field(description="Path to semcod root directory")
    max_actions: int = Field(10, description="Maximum actions per project")
    format: str = Field("text", description="Output format: text, yaml, or json")


class BatchHybridRequest(BaseModel):
    semcod_root: str = Field(description="Path to semcod root directory")
    max_changes: int = Field(30, description="Maximum changes per project")


class DebugConfigRequest(BaseModel):
    show_env: bool = Field(False, description="Show environment variables")


class DebugDecisionsRequest(BaseModel):
    project_path: str = Field(description="Path to project directory")
    limit: int = Field(20, description="Maximum number of decisions to return")


class PyQualAnalyzeRequest(BaseModel):
    project_path: str = Field(description="Path to project directory")
    config: str | None = Field(None, description="Path to pyqual.yaml config")
    format: str = Field("yaml", description="Output format: yaml or json")


class PyQualFixRequest(BaseModel):
    project_path: str = Field(description="Path to project directory")
    config: str | None = Field(None, description="Path to pyqual.yaml config")


class RulesRequest(BaseModel):
    rules: list[dict[str, Any]] = Field(description="List of DSL rules in YAML format")


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

    from redsl.config import AgentConfig
    from redsl.execution import explain_decisions, get_memory_stats
    from redsl.orchestrator import RefactorOrchestrator

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
            "memory": get_memory_stats(orchestrator),
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
        explanation = explain_decisions(orchestrator, Path(req.project_dir))
        return {"explanation": explanation}

    @app.post("/refactor")
    async def refactor(req: RefactorRequest):
        """Run refactoring on a project."""
        from .formatters import format_refactor_plan
        from .config import AgentConfig
        
        # Load config from environment
        config = AgentConfig.from_env()
        config.refactor.dry_run = req.dry_run
        if req.dry_run:
            config.refactor.reflection_rounds = 0
        
        orchestrator = RefactorOrchestrator(config)
        
        # Get decisions and format output
        project_path = Path(req.project_path)
        analysis = orchestrator.analyzer.analyze_project(project_path)
        contexts = analysis.to_dsl_contexts()
        decisions = orchestrator.dsl_engine.evaluate(contexts)
        decisions = sorted(decisions, key=lambda d: d.score, reverse=True)[:req.max_actions]
        
        # Format output based on requested format
        if req.format == "yaml":
            import yaml
            formatted = format_refactor_plan(decisions, "yaml", analysis)
            return yaml.safe_load(formatted)
        elif req.format == "json":
            import json
            formatted = format_refactor_plan(decisions, "json", analysis)
            return json.loads(formatted)
        else:
            formatted = format_refactor_plan(decisions, "text", analysis)
            return {"output": formatted}

    @app.post("/rules")
    async def add_rules(req: RulesRequest):
        """Dodaj niestandardowe reguły DSL."""
        orchestrator.add_custom_rules(req.rules)
        return {"status": "ok", "rules_count": len(orchestrator.dsl_engine.rules)}

    @app.get("/memory/stats")
    async def memory_stats():
        """Statystyki pamięci agenta."""
        return get_memory_stats(orchestrator)

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

    # Batch endpoints
    @app.post("/batch/semcod")
    async def batch_semcod(req: BatchSemcodRequest):
        """Batch refactor semcod projects."""
        from .commands import batch as batch_commands
        from .formatters import format_batch_results
        
        results = batch_commands.run_semcod_batch(Path(req.semcod_root), req.max_actions)
        
        # Convert results to format expected by formatter
        formatted_results = []
        for detail in results.get("project_details", []):
            formatted_results.append({
                "project_name": detail["name"],
                "status": "success",
                "files_processed": detail.get("files", 0),
                "changes_applied": detail["applied"],
                "todo_reduction": detail.get("todo_reduction", 0)
            })
        
        # Format output based on requested format
        if req.format == "yaml":
            import yaml
            formatted = format_batch_results(formatted_results, "yaml")
            return yaml.safe_load(formatted)
        elif req.format == "json":
            import json
            formatted = format_batch_results(formatted_results, "json")
            return json.loads(formatted)
        else:
            formatted = format_batch_results(formatted_results, "text")
            return {"output": formatted}

    @app.post("/batch/hybrid")
    async def batch_hybrid(req: BatchHybridRequest):
        """Hybrid quality refactoring (no LLM needed)."""
        from .commands import hybrid as hybrid_commands
        
        results = hybrid_commands.run_hybrid_batch(Path(req.semcod_root), req.max_changes)
        return {"status": "completed", "results": results}

    # Debug endpoints
    @app.get("/debug/config")
    async def debug_config(show_env: bool = False):
        """Get configuration info."""
        from .config import AgentConfig
        
        config = AgentConfig.from_env()
        info = {
            "llm_model": config.llm.model,
            "dry_run": config.refactor.dry_run,
            "max_actions": config.refactor.max_actions,
            "reflection_rounds": config.refactor.reflection_rounds,
        }
        
        if show_env:
            import os
            info["env_vars"] = {
                k: v for k, v in os.environ.items() 
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
                    "target": str(d.target_path),
                    "score": d.score,
                    "rule": d.rule.name if d.rule else None,
                    "rationale": getattr(d, "rationale", ""),
                }
                for d in decisions
            ]
        }

    # PyQual endpoints
    @app.post("/pyqual/analyze")
    async def pyqual_analyze(req: PyQualAnalyzeRequest):
        """Python code quality analysis."""
        from .commands import pyqual as pyqual_commands
        
        config_path = Path(req.config) if req.config else None
        results = pyqual_commands.run_pyqual_analysis(
            Path(req.project_path), 
            config_path, 
            req.format
        )
        return results

    @app.post("/pyqual/fix")
    async def pyqual_fix(req: PyQualFixRequest):
        """Apply automatic quality fixes."""
        from .commands import pyqual as pyqual_commands
        
        config_path = Path(req.config) if req.config else None
        pyqual_commands.run_pyqual_fix(Path(req.project_path), config_path)
        return {"status": "fixes_applied"}

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy", "version": "1.1.0"}

    return app


# Punkt wejścia dla uvicorn
app = create_app()
