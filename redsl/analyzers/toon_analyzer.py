"""
Analizator danych toon — przetwarza pliki .toon.yaml i buduje AnalysisResult.

Obsługuje:
- project_toon, duplication_toon, validation_toon, functions_toon
- Fallback na PythonAnalyzer gdy brak plików toon
- Uzupełnianie metryk quality metrics z PythonAnalyzer
"""

from __future__ import annotations

import functools
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .metrics import AnalysisResult, CodeMetrics
from .parsers import ToonParser

if TYPE_CHECKING:
    from .python_analyzer import PythonAnalyzer
    from .resolver import PathResolver

logger = logging.getLogger(__name__)


class ToonAnalyzer:
    """Analizator plików toon — przetwarza dane z code2llm."""

    def __init__(self, python_analyzer: "PythonAnalyzer", resolver: "PathResolver") -> None:
        self.parser = ToonParser()
        self._python = python_analyzer
        self._resolver = resolver

    @functools.lru_cache(maxsize=32)
    def analyze_project(self, project_dir: Path) -> AnalysisResult:
        """Przeprowadź pełną analizę projektu."""
        result = AnalysisResult()

        toon_files = self._find_toon_files(project_dir)

        if not toon_files:
            return self._python.analyze_python_files(project_dir)

        project_key = self._select_project_key(toon_files)
        if project_key:
            self._process_project_ton(toon_files[project_key], result)

        self._process_duplicates(toon_files, result)
        self._process_validation(toon_files, result)
        self._resolve_and_filter_metrics(result.metrics, project_dir)
        self._python.add_quality_metrics(result, project_dir)
        self._calculate_statistics(result)

        logger.info(
            "Analysis complete: %d files, %d lines, avg CC=%.1f, %d critical",
            result.total_files,
            result.total_lines,
            result.avg_cc,
            result.critical_count,
        )
        return result

    def analyze_from_toon_content(
        self,
        project_toon: str = "",
        duplication_toon: str = "",
        validation_toon: str = "",
    ) -> AnalysisResult:
        """Analizuj z bezpośredniego contentu toon (bez plików)."""
        result = AnalysisResult()

        if project_toon:
            data = self.parser.parse_project_toon(project_toon)
            result.alerts = data.get("alerts", [])

            for mod in data.get("modules", []):
                result.metrics.append(
                    CodeMetrics(
                        file_path=mod["path"],
                        module_lines=mod["lines"],
                        function_count=mod["functions"],
                        class_count=mod["classes"],
                        cyclomatic_complexity=mod["max_cc"],
                    )
                )

            func_index: dict[str, CodeMetrics] = {
                m.function_name: m for m in result.metrics if m.function_name
            }
            for alert in data.get("alerts", []):
                func_name = alert.get("name")
                alert_type = alert.get("type", "")
                value = alert.get("value", 0)
                existing = func_index.get(func_name)
                if existing is None:
                    existing = CodeMetrics(
                        file_path="detected_from_alert",
                        function_name=func_name,
                        cyclomatic_complexity=value if "cc" in alert_type else 0,
                        fan_out=value if "fan" in alert_type else 0,
                    )
                    result.metrics.append(existing)
                    func_index[func_name] = existing
                else:
                    if "cc" in alert_type:
                        existing.cyclomatic_complexity = max(existing.cyclomatic_complexity, value)
                    elif "fan" in alert_type:
                        existing.fan_out = max(existing.fan_out, value)

        if duplication_toon:
            result.duplicates = self.parser.parse_duplication_toon(duplication_toon)

        result.total_files = len(set(m.file_path for m in result.metrics))
        result.total_lines = sum(m.module_lines for m in result.metrics)

        return result

    def _find_toon_files(self, project_dir: Path) -> dict[str, Path]:
        """Znajdź pliki toon w projekcie — obsługuje wiele wzorców i formatów."""
        files: dict[str, Path] = {}
        for pattern, key in [
            ("*project*toon*", "project"),
            ("*analysis*toon*", "analysis"),
            ("*evolution*toon*", "evolution"),
            ("*duplication*toon*", "duplication"),
            ("*validation*toon*", "validation"),
            ("*map*toon*", "map"),
        ]:
            found = list(project_dir.glob(pattern))
            if found:
                files[key] = found[0]

        if "project" not in files and "analysis" not in files:
            toon_candidates = [
                f
                for f in project_dir.glob("*.toon")
                if "duplication" not in f.name
                and "validation" not in f.name
                and "evolution" not in f.name
                and "map" not in f.name
            ]
            if toon_candidates:
                files["project"] = toon_candidates[0]

        logger.info("Found toon files: %s", list(files.keys()))
        return files

    def _select_project_key(self, toon_files: dict[str, Path]) -> str | None:
        """T005: wybierz klucz projektu — 'project' lub 'analysis' jako fallback."""
        if "project" in toon_files:
            return "project"
        if "analysis" in toon_files:
            return "analysis"
        return None

    def _process_project_ton(self, toon_file: Path, result: AnalysisResult) -> None:
        """Parsuj plik project_toon i zaktualizuj result."""
        raw_content = toon_file.read_text(encoding="utf-8")

        if raw_content.lstrip().startswith("project:") and "function_details:" in raw_content:
            project_data = self.parser.parse_functions_toon(raw_content)
        else:
            project_data = self.parser.parse_project_toon(raw_content)

        health = project_data.get("health", {})
        result.project_name = health.get("name", str(toon_file.parent))
        result.avg_cc = health.get("CC\u0304", 0.0)
        result.critical_count = health.get("critical", 0)
        result.alerts = project_data.get("alerts", [])

        result._header_files = health.get("total_files", 0)  # type: ignore[attr-defined]
        result._header_lines = health.get("total_lines", 0)  # type: ignore[attr-defined]

        self._convert_modules_to_metrics(project_data.get("modules", []), result)
        self._process_hotspots(project_data.get("hotspots", []), result)
        self._process_alerts(project_data.get("alerts", []), result)

    def _convert_modules_to_metrics(
        self, modules: list[dict], result: AnalysisResult
    ) -> None:
        """Konwertuj moduły z toon na CodeMetrics."""
        for mod in modules:
            result.metrics.append(CodeMetrics(
                file_path=mod["path"],
                module_lines=mod["lines"],
                function_count=mod["functions"],
                class_count=mod["classes"],
                cyclomatic_complexity=mod["max_cc"],
            ))

    def _process_hotspots(self, hotspots: list[dict], result: AnalysisResult) -> None:
        """Dodaj fan-out z hotspotów do istniejących metryk."""
        for hotspot in hotspots:
            for m in result.metrics:
                if hotspot["name"] in (m.function_name or "") or hotspot["name"] in m.file_path:
                    m.fan_out = max(m.fan_out, hotspot["fan_out"])

    def _process_alerts(self, alerts: list[dict], result: AnalysisResult) -> None:
        """Przetwórz alerty i zaktualizuj lub dodaj metryki."""
        func_index: dict[str, CodeMetrics] = {
            m.function_name: m for m in result.metrics if m.function_name
        }

        for alert in alerts:
            func_name = alert.get("name", "")
            alert_type = alert.get("type", "")
            value = alert.get("value", 0)

            existing = func_index.get(func_name)
            if existing is None:
                existing = CodeMetrics(
                    file_path="detected_from_alert",
                    function_name=func_name,
                )
                result.metrics.append(existing)
                func_index[func_name] = existing

            if "cc" in alert_type:
                existing.cyclomatic_complexity = max(existing.cyclomatic_complexity, value)
            elif "fan" in alert_type:
                existing.fan_out = max(existing.fan_out, value)

    def _process_duplicates(
        self, toon_files: dict[str, Path], result: AnalysisResult
    ) -> None:
        """Parsuj duplikaty i dodaj metryki."""
        if "duplication" not in toon_files:
            return

        dups = self.parser.parse_duplication_toon(
            toon_files["duplication"].read_text(encoding="utf-8")
        )
        result.duplicates = dups

        for dup in dups:
            for f in dup.get("files", []):
                for m in result.metrics:
                    if m.file_path == f["path"]:
                        m.duplicate_lines += dup.get("lines", 0)
                        m.duplicate_similarity = max(
                            m.duplicate_similarity, dup.get("similarity", 0.0)
                        )

    def _process_validation(
        self, toon_files: dict[str, Path], result: AnalysisResult
    ) -> None:
        """Parsuj walidację i dodaj metryki lintera."""
        if "validation" not in toon_files:
            return

        issues = self.parser.parse_validation_toon(
            toon_files["validation"].read_text(encoding="utf-8")
        )
        for issue in issues:
            for m in result.metrics:
                if m.file_path == issue.get("file", ""):
                    if issue.get("severity") == "error":
                        m.linter_errors += 1
                    else:
                        m.linter_warnings += 1

    def _resolve_and_filter_metrics(
        self, metrics: list[CodeMetrics], project_dir: Path
    ) -> None:
        """Rozwiąż ścieżki i usuń ghost-metrics."""
        self._resolver.resolve_metrics_paths(metrics, project_dir)

        valid_metrics = [
            m
            for m in metrics
            if ".py" in m.file_path or (project_dir / m.file_path).exists()
        ]
        metrics[:] = valid_metrics

    def _calculate_statistics(self, result: AnalysisResult) -> None:
        """Oblicz finalne statystyki projektu."""
        cc_values = [
            m.cyclomatic_complexity for m in result.metrics if m.cyclomatic_complexity > 0
        ]
        if cc_values:
            result.avg_cc = round(sum(cc_values) / len(cc_values), 2)

        result.total_files = len(
            {m.file_path for m in result.metrics if not m.function_name}
        )
        result.total_lines = sum(
            m.module_lines for m in result.metrics if not m.function_name
        )

        hdr_files = getattr(result, "_header_files", 0)
        hdr_lines = getattr(result, "_header_lines", 0)
        if hdr_files and hdr_files > result.total_files:
            result.total_files = hdr_files
        if hdr_lines and hdr_lines > result.total_lines:
            result.total_lines = hdr_lines
