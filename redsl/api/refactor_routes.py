"""Refactor, analyze, batch, cycle, rules and memory endpoints."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from redsl.api.models import (
    AnalyzeRequest,
    BatchHybridRequest,
    BatchSemcodRequest,
    CycleRequest,
    CycleResponse,
    RefactorRequest,
    RulesRequest,
)
from redsl.orchestrator import RefactorOrchestrator

logger = logging.getLogger(__name__)


def _run_refactor_analysis(req: RefactorRequest) -> tuple[Any, list[Any]]:
    """Build orchestrator, analyze project, return (analysis, top decisions)."""
    from redsl.config import AgentConfig

    config = AgentConfig.from_env()
    config.refactor.dry_run = req.dry_run
    if req.dry_run:
        config.refactor.reflection_rounds = 0

    orch = RefactorOrchestrator(config)
    project_path = Path(req.project_dir)
    analysis = orch.analyzer.analyze_project(project_path)
    contexts = analysis.to_dsl_contexts()
    decisions = orch.dsl_engine.evaluate(contexts)
    decisions = sorted(decisions, key=lambda d: d.score, reverse=True)[: req.max_actions]
    return analysis, decisions


def _format_refactor_result(decisions: list, analysis: Any, fmt: str) -> Any:
    """Format refactoring decisions for API response."""
    from redsl.formatters import format_refactor_plan

    if fmt == "yaml":
        import yaml

        formatted = format_refactor_plan(decisions, "yaml", analysis)
        return yaml.safe_load(formatted)
    elif fmt == "json":
        import json

        formatted = format_refactor_plan(decisions, "json", analysis)
        return json.loads(formatted)
    else:
        formatted = format_refactor_plan(decisions, "text", analysis)
        return {"output": formatted}


def _register_analysis_endpoints(app: Any, orchestrator: Any) -> None:
    """Register /analyze and /decide endpoints."""

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
        from redsl.execution import explain_decisions

        explanation = explain_decisions(orchestrator, Path(req.project_dir))

        analysis = orchestrator.analyzer.analyze_project(Path(req.project_dir))
        contexts = analysis.to_dsl_contexts()
        decisions = orchestrator.dsl_engine.evaluate(contexts)
        decisions = sorted(decisions, key=lambda d: d.score, reverse=True)[:20]

        return {
            "explanation": explanation,
            "decisions": [
                {
                    "action": d.action.value,
                    "target_path": str(d.target_file),
                    "score": d.score,
                    "rule_name": d.rule_name,
                    "rationale": getattr(d, "rationale", ""),
                }
                for d in decisions
            ],
            "metrics": {
                "total_files": analysis.total_files,
                "total_lines": analysis.total_lines,
                "avg_cc": analysis.avg_cc,
                "critical_count": analysis.critical_count,
                "alerts_count": len(analysis.alerts),
            },
        }


def _collect_modified_files(project_path: Path) -> list[str]:
    """Return git-tracked modified/untracked files in *project_path*."""
    import subprocess

    files: list[str] = []
    try:
        r1 = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=str(project_path), capture_output=True, text=True, timeout=10,
        )
        files.extend(f.strip() for f in r1.stdout.strip().split("\n") if f.strip())
        r2 = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=str(project_path), capture_output=True, text=True, timeout=10,
        )
        files.extend(f.strip() for f in r2.stdout.strip().split("\n") if f.strip())
    except Exception:
        pass
    return files


def _clear_project_history(project_path: Path) -> list[str]:
    """Remove history/memory files for *project_path* and return removed paths."""
    removed: list[str] = []
    candidates = [
        project_path / ".redsl" / "history.jsonl",
        Path("/app/.redsl/history.jsonl"),
        Path("/tmp/refactor_memory/chroma.sqlite3"),
    ]
    for p in candidates:
        if p.exists():
            p.unlink()
            removed.append(str(p))
            logger.info("Cleared history: %s", p)
    return removed


def _register_refactor_endpoints(app: Any, orchestrator: Any) -> None:
    """Register /refactor, /cycle, /rules, /memory/stats, /history/clear, /ws/refactor."""
    from fastapi import WebSocket, WebSocketDisconnect

    from redsl.execution import get_memory_stats

    @app.post("/refactor")
    async def refactor(req: RefactorRequest):
        """Run refactoring on a project (plan-only — returns decisions without modifying files)."""
        analysis, decisions = _run_refactor_analysis(req)
        return _format_refactor_result(decisions, analysis, req.format)

    @app.post("/cycle")
    async def run_cycle(req: CycleRequest):
        """Run a full refactoring cycle — actually modifies files on disk via LLM."""
        from redsl.config import AgentConfig

        config = AgentConfig.from_env()
        if req.llm_model:
            config.llm.model = req.llm_model
        config.refactor.dry_run = False
        config.refactor.reflection_rounds = 1

        project_path = Path(req.project_dir)

        if req.clear_history:
            _clear_project_history(project_path)

        orch = RefactorOrchestrator(config)
        report = orch.run_cycle(project_path, max_actions=req.max_actions)

        files_modified = _collect_modified_files(project_path)

        return CycleResponse(
            cycle_number=report.cycle_number,
            analysis_summary=report.analysis_summary,
            decisions_count=report.decisions_count,
            proposals_generated=report.proposals_generated,
            proposals_applied=report.proposals_applied,
            proposals_rejected=report.proposals_rejected,
            errors=report.errors,
            files_modified=files_modified,
        )

    @app.post("/rules")
    async def add_rules(req: RulesRequest):
        """Dodaj niestandardowe reguły DSL."""
        orchestrator.add_custom_rules(req.rules)
        return {"status": "ok", "rules_count": len(orchestrator.dsl_engine.rules)}

    @app.get("/memory/stats")
    async def memory_stats():
        """Statystyki pamięci agenta."""
        return get_memory_stats(orchestrator)

    @app.post("/history/clear")
    async def clear_history(project_dir: str):
        """Clear decision history for a project."""
        removed = _clear_project_history(Path(project_dir))
        return {"status": "cleared", "files_removed": removed}

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
                    Path(project_dir), max_actions=data.get("max_actions", 3)
                )
                await websocket.send_json(
                    {
                        "phase": "complete",
                        "cycle": report.cycle_number,
                        "summary": report.analysis_summary,
                        "applied": report.proposals_applied,
                        "errors": report.errors,
                    }
                )
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")


def _register_batch_routes(app: Any) -> None:
    """Register /batch/semcod and /batch/hybrid endpoints."""

    @app.post("/batch/semcod")
    async def batch_semcod(req: BatchSemcodRequest):
        """Batch refactor semcod projects."""
        from redsl.commands import batch as batch_commands
        from redsl.formatters import format_batch_results

        results = batch_commands.run_semcod_batch(Path(req.semcod_root), req.max_actions)

        formatted_results = []
        for detail in results.get("project_details", []):
            formatted_results.append(
                {
                    "project_name": detail["name"],
                    "status": "success",
                    "files_processed": detail.get("files", 0),
                    "changes_applied": detail["applied"],
                    "todo_reduction": detail.get("todo_reduction", 0),
                }
            )

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
        from redsl.commands import hybrid as hybrid_commands

        results = hybrid_commands.run_hybrid_batch(Path(req.semcod_root), req.max_changes)
        return {"status": "completed", "results": results}


def _register_refactor_routes(app: Any, orchestrator: Any) -> None:
    """Register all analysis, refactoring and batch routes."""
    _register_analysis_endpoints(app, orchestrator)
    _register_refactor_endpoints(app, orchestrator)
    _register_batch_routes(app)
