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

import ast
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
    """Parser plików toon — obsługuje wiele formatów wyjścia code2llm."""

    def parse_project_toon(self, content: str) -> dict[str, Any]:
        """Parsuj plik toon — obsługuje formaty: legacy, code2llm v2 (HEALTH[N]/LAYERS), M[N] list."""
        result: dict[str, Any] = {
            "health": {},
            "alerts": [],
            "hotspots": [],
            "refactors": [],
            "modules": [],
        }

        # T017: Parsuj header line: # project | 113f 20532L | python:109 | date
        for line in content.splitlines()[:3]:
            if line.startswith("#"):
                hdr = self._parse_header_line(line)
                if hdr:
                    result["health"].update(hdr)

        section = ""
        module_list_mode = False  # T003: M[N]: file,lines format
        for line in content.splitlines():
            stripped = line.strip()

            # --- Wykrywanie sekcji ---
            if re.match(r'HEALTH(\[\d+\])?:', stripped):
                section = "health"
                module_list_mode = False
                continue
            elif re.match(r'ALERTS', stripped):
                section = "alerts"
                module_list_mode = False
                continue
            elif stripped.startswith("HOTSPOTS"):
                section = "hotspots"
                module_list_mode = False
                continue
            elif stripped.startswith("REFACTOR"):
                section = "refactors"
                module_list_mode = False
                continue
            elif re.match(r'MODULES', stripped):
                section = "modules"
                module_list_mode = False
                continue
            elif stripped.startswith("EVOLUTION"):
                section = "evolution"
                module_list_mode = False
                continue
            elif stripped.startswith("LAYERS:"):
                # T002: code2llm v2 — sekcja LAYERS zamiast MODULES
                section = "layers"
                module_list_mode = False
                continue
            elif re.match(r'M\[\d+\]:', stripped):
                # T003: format M[186]: z listą file,lines
                section = "modules"
                module_list_mode = True
                continue

            # --- Parsowanie zawartości sekcji ---

            # Legacy HEALTH: key=val
            if section == "health" and "=" in stripped and not stripped.startswith("🟡"):
                parts = stripped.split()
                for part in parts:
                    if "=" in part:
                        key, val = part.split("=", 1)
                        result["health"][key.strip()] = _try_number(val.strip())

            # T001: code2llm v2 HEALTH[N]: 🟡 CC func CC=41 (limit:10)
            elif section == "health" and ("🟡" in stripped or "🔴" in stripped or "⚠" in stripped):
                alert = self._parse_emoji_alert_line(stripped)
                if alert:
                    result["alerts"].append(alert)

            # Legacy ALERTS: !!! cc_exceeded func = 36 (limit:15)
            elif section == "alerts" and stripped.startswith("!"):
                alert = self._parse_alert_line(stripped)
                if alert:
                    result["alerts"].append(alert)

            elif section == "hotspots" and stripped.startswith("★"):
                hotspot = self._parse_hotspot_line(stripped)
                if hotspot:
                    result["hotspots"].append(hotspot)

            # Legacy MODULES: M[file] 450L C:3 F:12 CC↑35
            elif section == "modules" and not module_list_mode and stripped.startswith("M["):
                module = self._parse_module_line(stripped)
                if module:
                    result["modules"].append(module)

            # T003: M[N]: file,line_count list
            elif section == "modules" and module_list_mode and "," in stripped and stripped:
                module = self._parse_module_list_line(stripped)
                if module:
                    result["modules"].append(module)

            # T002: LAYERS: │ !! module_name 721L 1C CC=5
            elif section == "layers" and ("│" in line or stripped.startswith("│")):
                module = self._parse_layers_line(stripped)
                if module:
                    result["modules"].append(module)

            elif section == "refactors" and stripped.startswith("["):
                refactor = self._parse_refactor_line(stripped)
                if refactor:
                    result["refactors"].append(refactor)

        return result

    def parse_duplication_toon(self, content: str) -> list[dict[str, Any]]:
        """Parsuj duplication_toon — obsługuje formaty legacy i code2llm [hash] ! STRU."""
        duplicates = []
        current: dict[str, Any] | None = None

        for line in content.splitlines():
            stripped = line.strip()

            # T010: Nowa grupa duplikatów — oba formaty:
            # Legacy:     [STRU name L=25 N=3 saved=50 sim=1.00
            # code2llm:  [1899ff8e67d31c77] ! STRU  setup_logging  L=25 N=3 saved=50 sim=1.00
            if re.search(r'(STRU|EXAC)', stripped) and stripped.startswith("["):
                if current:
                    duplicates.append(current)
                match = re.search(
                    r'(STRU|EXAC)\s+([\w./-]+)\s+L=(\d+)\s+N=(\d+)\s+saved=(\d+)\s+sim=([\d.]+)',
                    stripped
                )
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

            elif current and stripped and ":" in stripped:
                # Linia z plikiem: path/file.py:start-end lub path/file.py:line
                file_match = re.match(r'([\w/._-]+(?:\.py|\.[a-z]+)):(\d+)(?:-(\d+))?', stripped)
                if file_match:
                    current["files"].append({
                        "path": file_match.group(1),
                        "start": int(file_match.group(2)),
                        "end": int(file_match.group(3)) if file_match.group(3) else int(file_match.group(2)),
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

    def _parse_header_line(self, line: str) -> dict[str, Any] | None:
        """T017: Parsuj nagłówek: # project | 113f 20532L | python:109 | date"""
        cleaned = line.lstrip("# ").strip()
        parts = [p.strip() for p in cleaned.split("|")]
        if not parts:
            return None
        name_candidate = parts[0]
        result: dict[str, Any] = {}
        if name_candidate and "=" not in name_candidate and not name_candidate.startswith("CC"):
            result["name"] = name_candidate
        for part in parts[1:]:
            files_match = re.search(r'(\d+)f', part)
            lines_match = re.search(r'(\d+)L', part)
            cc_match = re.search(r'CC[̄=](\d+\.?\d*)', part)
            critical_match = re.search(r'critical:(\d+)', part)
            if files_match:
                result["total_files"] = int(files_match.group(1))
            if lines_match:
                result["total_lines"] = int(lines_match.group(1))
            if cc_match:
                result["CC\u0304"] = float(cc_match.group(1))
            if critical_match:
                result["critical"] = int(critical_match.group(1))
        return result if result else None

    def _parse_emoji_alert_line(self, line: str) -> dict[str, Any] | None:
        """T001: Parsuj linie code2llm v2: 🟡 CC func_name CC=41 (limit:10)"""
        # Usuń emoji i leading whitespace
        cleaned = re.sub(r'[🟡🔴⚠️\s]+', ' ', line).strip()
        # Wykryj typ alertu i nazwę funkcji
        # Format: CC func_name CC=41 (limit:10)
        #      lub: FAN func_name FAN=26 (limit:10)
        match = re.match(
            r'(CC|FAN|DUP|LINES|CYCLE)\s+([\w.]+)\s+(?:CC|FAN|DUP|LINES|CYCLE)?[=\s]+(\d+)(?:\s*\(limit:(\d+)\))?',
            cleaned
        )
        if not match:
            # Fallback: szukaj CC= pattern
            val_match = re.search(r'CC=(\d+)', line)
            name_match = re.search(r'CC\s+([\w.]+)', line.replace('🟡', '').replace('🔴', ''))
            if val_match and name_match:
                return {
                    "type": "cc_exceeded",
                    "name": name_match.group(1).strip(),
                    "severity": 2,
                    "value": int(val_match.group(1)),
                    "limit": 10,
                }
            return None
        alert_type_map = {"CC": "cc_exceeded", "FAN": "high_fan_out", "DUP": "duplicate_block"}
        raw_type = match.group(1)
        return {
            "type": alert_type_map.get(raw_type, raw_type.lower()),
            "name": match.group(2),
            "severity": 2,
            "value": int(match.group(3)),
            "limit": int(match.group(4)) if match.group(4) else 10,
        }

    def _parse_alert_line(self, line: str) -> dict[str, Any] | None:
        severity = line.count("!")
        cleaned = line.lstrip("! ").strip()
        parts = cleaned.split(None, 2)
        if len(parts) >= 2:
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
        """Legacy format: M[file] 450L C:3 F:12 CC↑35"""
        match = re.match(r'M\[(.+?)\]\s+(\d+)L\s+C:(\d+)\s+F:(\d+)\s+CC[↑=](\d+)', line)
        if match:
            return {
                "path": match.group(1),
                "lines": int(match.group(2)),
                "classes": int(match.group(3)),
                "functions": int(match.group(4)),
                "max_cc": int(match.group(5)),
            }
        return None

    def _parse_module_list_line(self, line: str) -> dict[str, Any] | None:
        """T003: Format M[N] list: file_path,line_count"""
        parts = line.split(",")
        if len(parts) >= 2 and parts[-1].strip().isdigit():
            return {
                "path": parts[0].strip(),
                "lines": int(parts[-1].strip()),
                "classes": 0,
                "functions": 0,
                "max_cc": 0,
            }
        return None

    def _parse_layers_line(self, line: str) -> dict[str, Any] | None:
        """T002: Format LAYERS: │ !! module_name 721L 1C CC=5"""
        # Usuń prefix │ i symbole alertów
        cleaned = re.sub(r'[│├└─!\s]+', ' ', line).strip()
        # Format: name 721L 1C Nm CC=5
        match = re.match(
            r'([\w./]+)\s+(\d+)L\s+(\d+)C\s+\S+\s+CC[=↑](\d+)',
            cleaned
        )
        if match:
            return {
                "path": match.group(1),
                "lines": int(match.group(2)),
                "classes": int(match.group(3)),
                "functions": 0,
                "max_cc": int(match.group(4)),
            }
        return None

    def _parse_refactor_line(self, line: str) -> dict[str, str] | None:
        match = re.match(r'\[(\d+)\]\s+(.+)', line)
        if match:
            return {"index": match.group(1), "description": match.group(2).strip()}
        return None

    def parse_functions_toon(self, content: str) -> dict[str, Any]:
        """T006: Parsuj project.functions.toon — format YAML per-funkcja z CC.

        Format:
            project: name
            modules[N]{path,lang,items}:
              file.py,python,14
            function_details:
              file.py:
                functions[N]{name,kind,sig,loc,async,lines,cc,does}:
                  func,method,(),21-35,false,15,7,description
        """
        result: dict[str, Any] = {
            "health": {},
            "alerts": [],
            "modules": [],
            "functions": [],
        }

        current_file = ""
        section = ""
        fields_order: list[str] = []

        for line in content.splitlines():
            stripped = line.strip()

            if stripped.startswith("project:"):
                result["health"]["name"] = stripped.split(":", 1)[1].strip()
                continue

            if re.match(r'modules\[\d+\]', stripped):
                section = "modules"
                continue

            if stripped == "function_details:":
                section = "function_details"
                continue

            if section == "modules" and "," in stripped:
                parts = stripped.split(",")
                if len(parts) >= 2:
                    result["modules"].append({
                        "path": parts[0].strip(),
                        "lines": 0,
                        "classes": 0,
                        "functions": int(parts[2]) if len(parts) > 2 and parts[2].strip().isdigit() else 0,
                        "max_cc": 0,
                    })

            elif section == "function_details":
                # Linia pliku: "  file.py:"
                file_match = re.match(r'^\s{2}([\w./]+\.\w+):\s*$', line)
                if file_match:
                    current_file = file_match.group(1)
                    fields_order = []
                    continue

                # Nagłówek kolumn: "functions[N]{name,kind,sig,loc,async,lines,cc,does}:"
                header_match = re.match(r'functions\[\d+\]\{(.+)\}:', stripped)
                if header_match:
                    fields_order = [f.strip() for f in header_match.group(1).split(",")]
                    continue

                # Linia funkcji — CSV wg fields_order
                if current_file and fields_order and "," in stripped and not stripped.endswith(":"):
                    func = self._parse_function_csv_line(stripped, fields_order, current_file)
                    if func:
                        result["functions"].append(func)
                        # Aktualizuj max_cc w module
                        for mod in result["modules"]:
                            if mod["path"] == current_file:
                                mod["max_cc"] = max(mod["max_cc"], func.get("cc", 0))
                                break
                        # Generuj alert jeśli CC > 10
                        cc = func.get("cc", 0)
                        if cc > 10:
                            result["alerts"].append({
                                "type": "cc_exceeded",
                                "name": func["name"].split(".")[-1],
                                "severity": 3 if cc > 20 else 2 if cc > 15 else 1,
                                "value": cc,
                                "limit": 10,
                                "file": current_file,
                            })

        return result

    def _parse_function_csv_line(
        self, line: str, fields: list[str], file_path: str
    ) -> dict[str, Any] | None:
        """Parsuj CSV linię funkcji wg pól z nagłówka."""
        # Uwaga: sig może zawierać przecinki w cudzysłowach
        parts = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', line)
        if len(parts) < len(fields):
            return None
        result: dict[str, Any] = {"file": file_path}
        for i, field_name in enumerate(fields):
            if i >= len(parts):
                break
            val = parts[i].strip().strip('"')
            if field_name in ("lines", "cc"):
                result[field_name] = int(val) if val.isdigit() else 0
            elif field_name == "async":
                result[field_name] = val.lower() == "true"
            else:
                result[field_name] = val
        return result


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

        # 1b. T004: jeśli brak jakichkolwiek toon — fallback na AST Python
        if not toon_files:
            return self._analyze_python_files(project_dir)

        # 2. Parsuj project_toon — T005: fallback na 'analysis' jeśli brak 'project'
        project_key = "project" if "project" in toon_files else ("analysis" if "analysis" in toon_files else None)
        if project_key:
            raw_content = toon_files[project_key].read_text(encoding="utf-8")
            # T006: wykryj format functions.toon (starts with "project:" = YAML)
            if raw_content.lstrip().startswith("project:") and "function_details:" in raw_content:
                project_data = self.parser.parse_functions_toon(raw_content)
            else:
                project_data = self.parser.parse_project_toon(raw_content)
            health = project_data.get("health", {})
            result.project_name = health.get("name", str(project_dir))
            result.avg_cc = health.get("CC̄", 0.0)
            result.critical_count = health.get("critical", 0)
            result.alerts = project_data.get("alerts", [])

            # T017: dane z nagłówka jako fallback dla total_files/total_lines
            header_files = health.get("total_files", 0)
            header_lines = health.get("total_lines", 0)

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

            # T009: Indeks metryk po nazwie funkcji — deduplikacja
            func_index: dict[str, CodeMetrics] = {
                m.function_name: m for m in result.metrics if m.function_name
            }

            for alert in project_data.get("alerts", []):
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

            # T017: zachowaj dane nagłówka do użycia po ghost-filter
            result._header_files = header_files  # type: ignore[attr-defined]
            result._header_lines = header_lines  # type: ignore[attr-defined]

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

        # Rozwiąż ścieżki 'detected_from_alert' i krótkie nazwy z LAYERS
        self.resolve_metrics_paths(result.metrics, project_dir)

        # Usuń ghost-metrics: moduły z LAYERS bez rozwiązanej ścieżki .py
        result.metrics = [
            m for m in result.metrics
            if ".py" in m.file_path or (project_dir / m.file_path).exists()
        ]

        # Oblicz avg_cc z rzeczywistych metryk
        cc_values = [m.cyclomatic_complexity for m in result.metrics if m.cyclomatic_complexity > 0]
        if cc_values:
            result.avg_cc = round(sum(cc_values) / len(cc_values), 2)

        # Oblicz totals z metryk
        result.total_files = len({m.file_path for m in result.metrics if not m.function_name})
        result.total_lines = sum(m.module_lines for m in result.metrics if not m.function_name)

        # T017: użyj danych z nagłówka jako lepszy fallback gdy metryki niepełne
        hdr_files = getattr(result, "_header_files", 0)
        hdr_lines = getattr(result, "_header_lines", 0)
        if hdr_files and hdr_files > result.total_files:
            result.total_files = hdr_files
        if hdr_lines and hdr_lines > result.total_lines:
            result.total_lines = hdr_lines

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

            # T009: Deduplikacja — nie twórz duplikatu jeśli funkcja już jest w metrykach
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

        # Tfix1: Fallback — dowolny *.toon jako "project" jeśli żaden wzorzec nie pasuje
        if "project" not in files and "analysis" not in files:
            toon_candidates = [
                f for f in project_dir.glob("*.toon")
                if "duplication" not in f.name and "validation" not in f.name
                and "evolution" not in f.name and "map" not in f.name
            ]
            if toon_candidates:
                files["project"] = toon_candidates[0]

        logger.info("Found toon files: %s", list(files.keys()))
        return files

    def _analyze_python_files(self, project_dir: Path) -> AnalysisResult:
        """T004: Fallback — analiza .py przez stdlib ast gdy brak toon plików."""
        result = AnalysisResult()
        result.project_name = project_dir.name

        py_files = [
            f for f in project_dir.rglob("*.py")
            if not any(part in f.parts for part in (".venv", "venv", "dist", "__pycache__", ".git"))
        ]

        for py_file in py_files:
            try:
                source = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue

            lines = len(source.splitlines())
            rel_path = str(py_file.relative_to(project_dir))

            func_count = 0
            class_count = 0
            max_cc = 0
            high_cc_funcs: list[str] = []

            # Iteruj tylko po top-level i class-level funkcjach
            top_nodes = list(ast.iter_child_nodes(tree))
            for top in top_nodes:
                if isinstance(top, ast.ClassDef):
                    class_count += 1
                    for item in ast.iter_child_nodes(top):
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            func_count += 1
                            cc = self._ast_cyclomatic_complexity(item)
                            max_cc = max(max_cc, cc)
                            if cc > 10:
                                high_cc_funcs.append(item.name)
                                result.metrics.append(CodeMetrics(
                                    file_path=rel_path,
                                    function_name=item.name,
                                    module_lines=lines,
                                    cyclomatic_complexity=cc,
                                ))
                                result.alerts.append({
                                    "type": "cc_exceeded",
                                    "name": item.name,
                                    "severity": 3 if cc > 20 else 2,
                                    "value": cc,
                                    "limit": 10,
                                })
                elif isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_count += 1
                    cc = self._ast_cyclomatic_complexity(top)
                    max_cc = max(max_cc, cc)
                    if cc > 10:
                        high_cc_funcs.append(top.name)
                        result.metrics.append(CodeMetrics(
                            file_path=rel_path,
                            function_name=top.name,
                            module_lines=lines,
                            cyclomatic_complexity=cc,
                        ))
                        result.alerts.append({
                            "type": "cc_exceeded",
                            "name": top.name,
                            "severity": 3 if cc > 20 else 2,
                            "value": cc,
                            "limit": 10,
                        })

            # Metryka modułu (bez duplikowania jeśli już są per-funkcja)
            result.metrics.append(CodeMetrics(
                file_path=rel_path,
                module_lines=lines,
                function_count=func_count,
                class_count=class_count,
                cyclomatic_complexity=max_cc,
            ))

        result.total_files = len(py_files)
        result.total_lines = sum(m.module_lines for m in result.metrics if not m.function_name)
        result.critical_count = sum(1 for a in result.alerts if a.get("severity", 0) >= 2)

        cc_vals = [m.cyclomatic_complexity for m in result.metrics if m.cyclomatic_complexity > 0]
        result.avg_cc = round(sum(cc_vals) / len(cc_vals), 2) if cc_vals else 0.0

        logger.info(
            "AST fallback: %d py files, %d lines, %d critical CC",
            result.total_files, result.total_lines, result.critical_count,
        )
        return result

    @staticmethod
    def _ast_cyclomatic_complexity(node: ast.AST) -> int:
        """Oblicz CC dla funkcji — nie wchodzi w zagniedzone definicje funkcji/klas."""
        branch_types = (
            ast.If, ast.For, ast.While, ast.ExceptHandler,
            ast.With, ast.Assert, ast.comprehension,
        )
        count = 1

        def _walk(n: ast.AST) -> None:
            nonlocal count
            for child in ast.iter_child_nodes(n):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue  # nie licz złożoności zagnieżdżonych definicji
                if isinstance(child, branch_types):
                    count += 1
                elif isinstance(child, ast.BoolOp):
                    count += len(child.values) - 1
                _walk(child)

        _walk(node)
        return count

    def resolve_file_path(self, project_dir: Path, func_name: str) -> str | None:
        """Znajdź plik .py zawierający definicję funkcji/metody o podanej nazwie."""
        short_name = func_name.split(".")[-1]  # handle Class.method
        pattern = re.compile(
            rf'^\s*(?:async\s+)?def\s+{re.escape(short_name)}\s*\(',
            re.MULTILINE,
        )
        skip = {".venv", "venv", "dist", "__pycache__", ".git", "node_modules"}
        for py_file in project_dir.rglob("*.py"):
            if any(part in py_file.parts for part in skip):
                continue
            try:
                text = py_file.read_text(encoding="utf-8", errors="ignore")
                if pattern.search(text):
                    return str(py_file.relative_to(project_dir))
            except OSError:
                continue
        return None

    @staticmethod
    def extract_function_source(abs_path: Path, func_name: str) -> str:
        """Wytnij źródło jednej funkcji/metody z pliku używając AST."""
        short_name = func_name.split(".")[-1]
        try:
            source = abs_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
            lines = source.splitlines(keepends=True)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name == short_name:
                        start = node.lineno - 1
                        end = node.end_lineno if hasattr(node, "end_lineno") else len(lines)
                        return "".join(lines[start:end])
        except (OSError, SyntaxError):
            pass
        return ""

    def find_worst_function(self, abs_path: Path) -> tuple[str, int] | None:
        """Znajdź funkcję z najwyższym CC w pliku. Zwraca (name, cc) lub None."""
        try:
            source = abs_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
            worst: tuple[str, int] | None = None
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    cc = self._ast_cyclomatic_complexity(node)
                    if worst is None or cc > worst[1]:
                        worst = (node.name, cc)
            return worst
        except (OSError, SyntaxError):
            return None

    def resolve_metrics_paths(self, metrics: list[CodeMetrics], project_dir: Path) -> None:
        """Napraw ścieżki 'detected_from_alert' i krótkie nazwy modułów z LAYERS.

        Przeszukuje project_dir aby znaleźć prawdziwe ścieżki dla funkcji z alertów.
        Modyfikuje metryki in-place.
        """
        _cache: dict[str, str | None] = {}
        for m in metrics:
            if m.file_path in ("detected_from_alert", "unknown") or (
                m.function_name and not Path(project_dir / m.file_path).exists()
            ):
                func_name = m.function_name or m.file_path
                if func_name not in _cache:
                    _cache[func_name] = self.resolve_file_path(project_dir, func_name)
                resolved = _cache[func_name]
                if resolved:
                    m.file_path = resolved
                    logger.debug("Resolved %r → %s", func_name, resolved)


def _try_number(val: str) -> int | float | str:
    """Spróbuj skonwertować na liczbę."""
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return val
