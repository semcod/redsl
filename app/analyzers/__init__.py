"""
Analizator kodu — parser plików toon.yaml + metryki.

Konwertuje dane z:
- project_toon.yaml  (health, alerts, hotspots)
- analysis_toon.yaml (layers, CC, pipelines)
- evolution_toon.yaml (recommendations, risks)
- duplication_toon.yaml (duplicate blocks)
- validation_toon.yaml (linter errors, warnings)

na zunifikowane konteksty DSL do ewaluacji przez DSLEngine.
"""

from __future__ import annotations

import logging
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CodeMetrics:
    """Metryki pojedynczej funkcji/modułu."""

    file_path: str
    function_name: str | None = None
    module_lines: int = 0
    function_count: int = 0
    class_count: int = 0
    cyclomatic_complexity: float = 0.0
    fan_out: int = 0
    nested_depth: int = 0
    duplicate_lines: int = 0
    duplicate_similarity: float = 0.0
    missing_type_hints: int = 0
    is_public_api: bool = False
    linter_errors: int = 0
    linter_warnings: int = 0

    def to_dsl_context(self) -> dict[str, Any]:
        """Konwertuj na kontekst DSL do ewaluacji reguł."""
        return {
            "file_path": self.file_path,
            "function_name": self.function_name,
            "module_lines": self.module_lines,
            "function_count": self.function_count,
            "class_count": self.class_count,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "fan_out": self.fan_out,
            "nested_depth": self.nested_depth,
            "duplicate_lines": self.duplicate_lines,
            "duplicate_similarity": self.duplicate_similarity,
            "missing_type_hints": self.missing_type_hints,
            "is_public_api": self.is_public_api,
            "linter_errors": self.linter_errors,
            "linter_warnings": self.linter_warnings,
        }


@dataclass
class AnalysisResult:
    """Wynik analizy projektu."""

    project_name: str = ""
    total_files: int = 0
    total_lines: int = 0
    avg_cc: float = 0.0
    critical_count: int = 0
    metrics: list[CodeMetrics] = field(default_factory=list)
    alerts: list[dict[str, Any]] = field(default_factory=list)
    duplicates: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dsl_contexts(self) -> list[dict[str, Any]]:
        """Konwertuj na listę kontekstów DSL."""
        return [m.to_dsl_context() for m in self.metrics]


class ToonParser:
    """Parser plików toon.yaml — format wyjścia narzędzi code2llm."""

    def parse_project_toon(self, content: str) -> dict[str, Any]:
        """Parsuj project_toon.yaml — health, alerts, hotspots, refactor."""
        result: dict[str, Any] = {
            "health": {},
            "alerts": [],
            "hotspots": [],
            "refactors": [],
            "modules": [],
        }

        section = ""
        for line in content.splitlines():
            stripped = line.strip()

            if stripped.startswith("HEALTH:"):
                section = "health"
                continue
            elif stripped.startswith("ALERTS"):
                section = "alerts"
                continue
            elif stripped.startswith("HOTSPOTS"):
                section = "hotspots"
                continue
            elif stripped.startswith("REFACTOR"):
                section = "refactors"
                continue
            elif stripped.startswith("MODULES"):
                section = "modules"
                continue
            elif stripped.startswith("EVOLUTION"):
                section = "evolution"
                continue

            if section == "health" and "=" in stripped:
                parts = stripped.split()
                for part in parts:
                    if "=" in part:
                        key, val = part.split("=", 1)
                        result["health"][key.strip()] = _try_number(val.strip())

            elif section == "alerts" and stripped.startswith("!"):
                alert = self._parse_alert_line(stripped)
                if alert:
                    result["alerts"].append(alert)

            elif section == "hotspots" and stripped.startswith("★"):
                hotspot = self._parse_hotspot_line(stripped)
                if hotspot:
                    result["hotspots"].append(hotspot)

            elif section == "modules" and stripped.startswith("M["):
                module = self._parse_module_line(stripped)
                if module:
                    result["modules"].append(module)

            elif section == "refactors" and stripped.startswith("["):
                refactor = self._parse_refactor_line(stripped)
                if refactor:
                    result["refactors"].append(refactor)

        return result

    def parse_duplication_toon(self, content: str) -> list[dict[str, Any]]:
        """Parsuj duplication_toon.yaml — duplikaty kodu."""
        duplicates = []
        current: dict[str, Any] | None = None

        for line in content.splitlines():
            stripped = line.strip()

            # Nowa grupa duplikatów
            if stripped.startswith("[") and "STRU" in stripped or "EXAC" in stripped:
                if current:
                    duplicates.append(current)

                match = re.search(r'(STRU|EXAC)\s+(\w+)\s+L=(\d+)\s+N=(\d+)\s+saved=(\d+)\s+sim=([\d.]+)', stripped)
                if match:
                    current = {
                        "type": match.group(1),
                        "name": match.group(2),
                        "lines": int(match.group(3)),
                        "occurrences": int(match.group(4)),
                        "saved_lines": int(match.group(5)),
                        "similarity": float(match.group(6)),
                        "files": [],
                    }

            elif current and stripped and ":" in stripped and "/" in stripped:
                # Linia z plikiem
                file_match = re.match(r'([\w/._-]+):(\d+)-(\d+)', stripped)
                if file_match:
                    current["files"].append({
                        "path": file_match.group(1),
                        "start": int(file_match.group(2)),
                        "end": int(file_match.group(3)),
                    })

        if current:
            duplicates.append(current)

        return duplicates

    def parse_validation_toon(self, content: str) -> list[dict[str, Any]]:
        """Parsuj validation_toon.yaml — błędy walidacji."""
        issues = []
        current_file = ""

        for line in content.splitlines():
            stripped = line.strip()

            # Plik z wynikiem
            if stripped and "," in stripped and "/" in stripped and not stripped.startswith("issues"):
                parts = stripped.split(",")
                if len(parts) >= 2:
                    current_file = parts[0].strip()

            elif stripped and "," in stripped and current_file:
                parts = stripped.split(",")
                if len(parts) >= 4:
                    issues.append({
                        "file": current_file,
                        "rule": parts[0].strip(),
                        "severity": parts[1].strip(),
                        "message": parts[2].strip(),
                        "line": int(parts[3].strip()) if parts[3].strip().isdigit() else 0,
                    })

        return issues

    # -- Parsery pomocnicze --

    def _parse_alert_line(self, line: str) -> dict[str, Any] | None:
        severity = line.count("!")
        cleaned = line.lstrip("! ").strip()
        parts = cleaned.split(None, 2)
        if len(parts) >= 3:
            # np. "cc_exceeded _extract_entities = 36 (limit:15)"
            alert_type = parts[0]
            name = parts[1]
            rest = parts[2] if len(parts) > 2 else ""

            value_match = re.search(r'=\s*(\d+)', rest)
            limit_match = re.search(r'limit:(\d+)', rest)

            return {
                "type": alert_type,
                "name": name,
                "severity": severity,
                "value": int(value_match.group(1)) if value_match else 0,
                "limit": int(limit_match.group(1)) if limit_match else 0,
            }
        return None

    def _parse_hotspot_line(self, line: str) -> dict[str, Any] | None:
        cleaned = line.lstrip("★ ").strip()
        match = re.match(r'(\w+)\s+fan=(\d+)', cleaned)
        if match:
            return {"name": match.group(1), "fan_out": int(match.group(2))}
        return None

    def _parse_module_line(self, line: str) -> dict[str, Any] | None:
        match = re.match(r'M\[(.+?)\]\s+(\d+)L\s+C:(\d+)\s+F:(\d+)\s+CC↑(\d+)', line)
        if match:
            return {
                "path": match.group(1),
                "lines": int(match.group(2)),
                "classes": int(match.group(3)),
                "functions": int(match.group(4)),
                "max_cc": int(match.group(5)),
            }
        return None

    def _parse_refactor_line(self, line: str) -> dict[str, str] | None:
        match = re.match(r'\[(\d+)\]\s+(.+)', line)
        if match:
            return {"index": match.group(1), "description": match.group(2).strip()}
        return None


class CodeAnalyzer:
    """
    Główny analizator kodu.
    Łączy dane z toon.yaml, linterów i własnej analizy w zunifikowane metryki.
    """

    def __init__(self) -> None:
        self.parser = ToonParser()

    def analyze_project(self, project_dir: Path) -> AnalysisResult:
        """Przeprowadź pełną analizę projektu."""
        result = AnalysisResult()

        # 1. Szukaj plików toon.yaml
        toon_files = self._find_toon_files(project_dir)

        # 2. Parsuj project_toon
        if "project" in toon_files:
            project_data = self.parser.parse_project_toon(
                toon_files["project"].read_text(encoding="utf-8")
            )
            result.project_name = project_data.get("health", {}).get("name", str(project_dir))
            result.avg_cc = project_data.get("health", {}).get("CC̄", 0.0)
            result.critical_count = project_data.get("health", {}).get("critical", 0)
            result.alerts = project_data.get("alerts", [])

            # Konwertuj moduły na metryki
            for mod in project_data.get("modules", []):
                metrics = CodeMetrics(
                    file_path=mod["path"],
                    module_lines=mod["lines"],
                    function_count=mod["functions"],
                    class_count=mod["classes"],
                    cyclomatic_complexity=mod["max_cc"],
                )
                result.metrics.append(metrics)

            # Konwertuj hotspoty na metryki (uzupełniające)
            for hotspot in project_data.get("hotspots", []):
                for m in result.metrics:
                    if hotspot["name"] in (m.function_name or "") or hotspot["name"] in m.file_path:
                        m.fan_out = max(m.fan_out, hotspot["fan_out"])

            # Dodaj też metryki per-alert (per-function)
            for alert in project_data.get("alerts", []):
                func_name = alert.get("name", "")
                alert_type = alert.get("type", "")
                value = alert.get("value", 0)

                # Szukaj istniejącej metryki lub stwórz nową
                existing = None
                for m in result.metrics:
                    if m.function_name == func_name:
                        existing = m
                        break

                if existing is None:
                    existing = CodeMetrics(
                        file_path="unknown",
                        function_name=func_name,
                    )
                    result.metrics.append(existing)

                if "cc" in alert_type:
                    existing.cyclomatic_complexity = max(existing.cyclomatic_complexity, value)
                elif "fan" in alert_type:
                    existing.fan_out = max(existing.fan_out, value)

        # 3. Parsuj duplikaty
        if "duplication" in toon_files:
            dups = self.parser.parse_duplication_toon(
                toon_files["duplication"].read_text(encoding="utf-8")
            )
            result.duplicates = dups

            # Dodaj metryki duplikatów
            for dup in dups:
                for f in dup.get("files", []):
                    for m in result.metrics:
                        if m.file_path == f["path"]:
                            m.duplicate_lines += dup.get("lines", 0)
                            m.duplicate_similarity = max(
                                m.duplicate_similarity, dup.get("similarity", 0.0)
                            )

        # 4. Parsuj walidację
        if "validation" in toon_files:
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

        # Oblicz totals
        result.total_files = len(result.metrics)
        result.total_lines = sum(m.module_lines for m in result.metrics)

        logger.info(
            "Analysis complete: %d files, %d lines, avg CC=%.1f, %d critical",
            result.total_files, result.total_lines, result.avg_cc, result.critical_count,
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
                result.metrics.append(CodeMetrics(
                    file_path=mod["path"],
                    module_lines=mod["lines"],
                    function_count=mod["functions"],
                    class_count=mod["classes"],
                    cyclomatic_complexity=mod["max_cc"],
                ))

            for alert in data.get("alerts", []):
                existing = CodeMetrics(
                    file_path="detected_from_alert",
                    function_name=alert.get("name"),
                    cyclomatic_complexity=alert.get("value", 0) if "cc" in alert.get("type", "") else 0,
                    fan_out=alert.get("value", 0) if "fan" in alert.get("type", "") else 0,
                )
                result.metrics.append(existing)

        if duplication_toon:
            result.duplicates = self.parser.parse_duplication_toon(duplication_toon)

        result.total_files = len(set(m.file_path for m in result.metrics))
        result.total_lines = sum(m.module_lines for m in result.metrics)

        return result

    def _find_toon_files(self, project_dir: Path) -> dict[str, Path]:
        """Znajdź pliki toon.yaml w projekcie."""
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

        logger.info("Found toon files: %s", list(files.keys()))
        return files


def _try_number(val: str) -> int | float | str:
    """Spróbuj skonwertować na liczbę."""
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return val
