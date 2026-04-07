"""
Analizator plików Python przez stdlib ast.

Używany jako fallback gdy brak plików toon oraz do dodawania quality metrics
do wyników analizy toon.
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path

from .metrics import AnalysisResult, CodeMetrics
from .quality_visitor import CodeQualityVisitor
from .utils import _load_gitignore_patterns, _should_ignore_file

logger = logging.getLogger(__name__)


def ast_max_nesting_depth(node: ast.AST) -> int:
    """Oblicz max glębokość zagnieżdżenia pętli/warunków — nie wchodzi w zagnieżdżone def/class."""
    _depth_nodes = (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.ExceptHandler)

    def _depth(n: ast.AST, current: int) -> int:
        max_d = current
        for child in ast.iter_child_nodes(n):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(child, _depth_nodes):
                max_d = max(max_d, _depth(child, current + 1))
            else:
                max_d = max(max_d, _depth(child, current))
        return max_d

    return _depth(node, 0)


def ast_cyclomatic_complexity(node: ast.AST) -> int:
    """Oblicz CC dla funkcji — nie wchodzi w zagnieżdżone definicje funkcji/klas."""
    branch_types = (
        ast.If,
        ast.For,
        ast.While,
        ast.ExceptHandler,
        ast.With,
        ast.Assert,
        ast.comprehension,
    )
    count = 1

    def _walk(n: ast.AST) -> None:
        nonlocal count
        for child in ast.iter_child_nodes(n):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(child, branch_types):
                count += 1
            elif isinstance(child, ast.BoolOp):
                count += len(child.values) - 1
            _walk(child)

    _walk(node)
    return count


class PythonAnalyzer:
    """Analizator plików .py przez stdlib ast."""

    def analyze_python_files(self, project_dir: Path) -> AnalysisResult:
        """T004: Fallback — analiza .py przez stdlib ast gdy brak toon plików."""
        result = AnalysisResult()
        result.project_name = project_dir.name

        py_files = self._discover_python_files(project_dir)

        for py_file in py_files:
            file_metrics = self._parse_single_file(py_file, project_dir)
            if file_metrics is not None:
                self._accumulate_file_metrics(file_metrics, result)

        result.total_files = len(py_files)
        result.total_lines = sum(m.module_lines for m in result.metrics if not m.function_name)
        result.critical_count = sum(1 for a in result.alerts if a.get("severity", 0) >= 2)

        cc_vals = [m.cyclomatic_complexity for m in result.metrics if m.cyclomatic_complexity > 0]
        result.avg_cc = round(sum(cc_vals) / len(cc_vals), 2) if cc_vals else 0.0

        logger.info(
            "AST fallback: %d py files, %d lines, %d critical CC",
            result.total_files,
            result.total_lines,
            result.critical_count,
        )
        return result

    def _discover_python_files(self, project_dir: Path) -> list[Path]:
        """Skanuj katalog w poszukiwaniu plików .py z uwzględnieniem gitignore."""
        gitignore_patterns = _load_gitignore_patterns(project_dir)
        return [
            f
            for f in project_dir.rglob("*.py")
            if not _should_ignore_file(f, project_dir, gitignore_patterns)
        ]

    def _parse_single_file(
        self, py_file: Path, project_dir: Path
    ) -> dict | None:
        """Parsuj jeden plik .py i zwróć zebrane metryki lub None przy błędzie składni."""
        try:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            return None

        lines = len(source.splitlines())
        rel_path = str(py_file.relative_to(project_dir))

        quality_visitor = CodeQualityVisitor()
        quality_visitor.visit(tree)
        quality_metrics = quality_visitor.get_metrics()

        func_count, class_count, max_cc, high_cc_funcs, alerts = self._scan_top_nodes(
            tree, rel_path, lines
        )

        module_metrics = CodeMetrics(
            file_path=rel_path,
            module_lines=lines,
            function_count=func_count,
            class_count=class_count,
            cyclomatic_complexity=max_cc,
            unused_imports=quality_metrics["unused_imports"],
            magic_numbers=quality_metrics["magic_numbers"],
            module_execution_block=quality_metrics["module_execution_block"],
            missing_return_types=quality_metrics["missing_return_types"],
        )
        module_metrics._quality_details = {
            "unused_import_list": quality_metrics["unused_import_list"],
            "magic_number_list": quality_metrics["magic_number_list"],
            "functions_missing_return": quality_metrics["functions_missing_return"],
            "module_statements": quality_metrics["module_statements"],
        }

        return {
            "module_metrics": module_metrics,
            "high_cc_metrics": high_cc_funcs,
            "alerts": alerts,
            "rel_path": rel_path,
        }

    def _scan_top_nodes(
        self, tree: ast.AST, rel_path: str, lines: int
    ) -> tuple[int, int, int, list[CodeMetrics], list[dict]]:
        """Iteruj po węzłach top-level i class-level, zbieraj CC, nesting i alerty."""
        func_count = 0
        class_count = 0
        max_cc = 0
        high_cc_funcs: list[CodeMetrics] = []
        alerts: list[dict] = []
        is_init_file = rel_path.endswith("__init__.py")

        for top in ast.iter_child_nodes(tree):
            if isinstance(top, ast.ClassDef):
                class_count += 1
                for item in ast.iter_child_nodes(top):
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_count += 1
                        cc = ast_cyclomatic_complexity(item)
                        max_cc = max(max_cc, cc)
                        if cc > 10:
                            depth = ast_max_nesting_depth(item)
                            is_pub = is_init_file or not item.name.startswith("_")
                            high_cc_funcs.append(CodeMetrics(
                                file_path=rel_path,
                                function_name=item.name,
                                module_lines=lines,
                                cyclomatic_complexity=cc,
                                nested_depth=depth,
                                is_public_api=is_pub,
                            ))
                            alerts.append({
                                "type": "cc_exceeded",
                                "name": item.name,
                                "severity": 3 if cc > 20 else 2,
                                "value": cc,
                                "limit": 10,
                            })
            elif isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_count += 1
                cc = ast_cyclomatic_complexity(top)
                max_cc = max(max_cc, cc)
                if cc > 10:
                    depth = ast_max_nesting_depth(top)
                    is_pub = is_init_file or not top.name.startswith("_")
                    high_cc_funcs.append(CodeMetrics(
                        file_path=rel_path,
                        function_name=top.name,
                        module_lines=lines,
                        cyclomatic_complexity=cc,
                        nested_depth=depth,
                        is_public_api=is_pub,
                    ))
                    alerts.append({
                        "type": "cc_exceeded",
                        "name": top.name,
                        "severity": 3 if cc > 20 else 2,
                        "value": cc,
                        "limit": 10,
                    })

        return func_count, class_count, max_cc, high_cc_funcs, alerts

    def _accumulate_file_metrics(self, file_data: dict, result: AnalysisResult) -> None:
        """Dodaj metryki jednego pliku do zbiorczego wyniku."""
        result.metrics.extend(file_data["high_cc_metrics"])
        result.metrics.append(file_data["module_metrics"])
        result.alerts.extend(file_data["alerts"])

    def add_quality_metrics(self, result: AnalysisResult, project_dir: Path) -> None:
        """Dodaj quality metrics do istniejących wyników analizy toon."""
        metrics_by_file: dict[str, CodeMetrics] = {
            m.file_path: m for m in result.metrics if not m.function_name
        }

        gitignore_patterns = _load_gitignore_patterns(project_dir)
        py_files = [
            f
            for f in project_dir.rglob("*.py")
            if not _should_ignore_file(f, project_dir, gitignore_patterns)
        ]

        for py_file in py_files:
            try:
                source = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue

            rel_path = str(py_file.relative_to(project_dir))
            quality_visitor = CodeQualityVisitor()
            quality_visitor.visit(tree)
            quality_metrics = quality_visitor.get_metrics()

            if rel_path in metrics_by_file:
                m = metrics_by_file[rel_path]
                m.unused_imports = quality_metrics["unused_imports"]
                m.magic_numbers = quality_metrics["magic_numbers"]
                m.module_execution_block = quality_metrics["module_execution_block"]
                m.missing_return_types = quality_metrics["missing_return_types"]
                m._quality_details = {
                    "unused_import_list": quality_metrics["unused_import_list"],
                    "magic_number_list": quality_metrics["magic_number_list"],
                    "functions_missing_return": quality_metrics["functions_missing_return"],
                    "module_statements": quality_metrics["module_statements"],
                }
