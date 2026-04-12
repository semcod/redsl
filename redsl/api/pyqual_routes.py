"""PyQual analysis and fix endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from redsl.api.models import PyQualAnalyzeRequest, PyQualFixRequest


def _register_pyqual_routes(app: Any) -> None:

    @app.post("/pyqual/analyze")
    async def pyqual_analyze(req: PyQualAnalyzeRequest):
        """Python code quality analysis."""
        from redsl.commands import pyqual as pyqual_commands

        config_path = Path(req.config) if req.config else None
        results = pyqual_commands.run_pyqual_analysis(
            Path(req.project_path),
            config_path,
            req.format,
        )
        return results

    @app.post("/pyqual/fix")
    async def pyqual_fix(req: PyQualFixRequest):
        """Apply automatic quality fixes."""
        from redsl.commands import pyqual as pyqual_commands

        config_path = Path(req.config) if req.config else None
        pyqual_commands.run_pyqual_fix(Path(req.project_path), config_path)
        return {"status": "fixes_applied"}
