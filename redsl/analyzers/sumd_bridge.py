"""sumd_bridge — Bridge to oqlos.sumd for native project analysis.

Provides pure-Python project mapping without external tool dependencies.
Generates structural analysis including AST metrics (CC, fan-out, hotspots).
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SumdMetrics:
    """Metrics extracted from sumd analysis."""

    total_files: int = 0
    total_lines: int = 0
    total_functions: int = 0
    total_classes: int = 0
    cc_mean: float = 0.0
    critical_count: int = 0
    alerts: list[str] = field(default_factory=list)
    hotspots: list[dict] = field(default_factory=list)
    modules: list[dict] = field(default_factory=list)
    functions: list[dict] = field(default_factory=list)


class SumdAnalyzer:
    """Native project analyzer using sumd extractor patterns.

    Pure-Python implementation that doesn't require external tools.
    Generates map.toon.yaml compatible output with AST metrics.
    """

    def __init__(self) -> None:
        self._cc_cache: dict[str, int] = {}

    def analyze(self, project_dir: Path) -> SumdMetrics:
        """Analyze project directory and return metrics.

        Args:
            project_dir: Path to project root

        Returns:
            SumdMetrics with structural analysis
        """
        project_dir = project_dir.resolve()
        pkg_name = project_dir.name

        # Collect all Python modules
        modules = self._collect_modules(project_dir)

        # Analyze each module
        all_functions: list[dict] = []
        all_classes: list[dict] = []
        total_lines = 0

        for rel_path, lines, lang in modules:
            total_lines += lines
            if lang == "py":
                funcs, classes = self._analyze_py_file(project_dir / rel_path)
                all_functions.extend(funcs)
                all_classes.extend(classes)

        # Calculate metrics
        cc_values = [f.get("cc", 1) for f in all_functions]
        cc_mean = sum(cc_values) / len(cc_values) if cc_values else 0.0
        critical = sum(1 for cc in cc_values if cc >= 15)

        # Identify hotspots (high fan-out)
        hotspots = self._identify_hotspots(all_functions)

        # Generate alerts
        alerts = self._generate_alerts(all_functions, modules)

        return SumdMetrics(
            total_files=len(modules),
            total_lines=total_lines,
            total_functions=len(all_functions),
            total_classes=len(all_classes),
            cc_mean=round(cc_mean, 2),
            critical_count=critical,
            alerts=alerts[:5],
            hotspots=hotspots[:5],
            modules=[{"path": m[0], "lines": m[1], "lang": m[2]} for m in modules],
            functions=all_functions,
        )

    def generate_map_toon(self, project_dir: Path) -> str:
        """Generate map.toon.yaml content compatible with redsl.

        Args:
            project_dir: Path to project root

        Returns:
            map.toon.yaml content as string
        """
        metrics = self.analyze(project_dir)
        proj_name = project_dir.name
        from datetime import date

        today = date.today().isoformat()

        lang_counts: dict[str, int] = {}
        for m in metrics.modules:
            lang = m["lang"]
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

        lang_str = ",".join(
            f"{lang}:{cnt}" for lang, cnt in sorted(lang_counts.items(), key=lambda x: -x[1])
        )

        lines: list[str] = []
        a = lines.append

        a(f"# {proj_name} | {metrics.total_files}f {metrics.total_lines}L | {lang_str} | {today}")
        a(
            f"# stats: {metrics.total_functions} func | {metrics.total_classes} cls | "
            f"{len(metrics.modules)} mod | CC̄={metrics.cc_mean} | critical:{metrics.critical_count}"
        )
        a(f"# alerts: {'; '.join(metrics.alerts) if metrics.alerts else 'none'}")
        hotspot_str = "; ".join(
            f"{h['name']} fan={h['fan']}" for h in metrics.hotspots[:5]
        )
        a(f"# hotspots: {hotspot_str if hotspot_str else 'none'}")

        a("")
        a(f"M[{len(metrics.modules)}]:")
        for m in sorted(metrics.modules, key=lambda x: x["path"]):
            a(f"  {m['path']},{m['lines']}")

        a("")
        a("D:")
        # Group functions by module
        by_module: dict[str, list[dict]] = {}
        for f in metrics.functions:
            mod = f.get("module", "unknown")
            by_module.setdefault(mod, []).append(f)

        for mod_path, funcs in sorted(by_module.items()):
            a(f"  {mod_path}:")
            for f in funcs:
                sig = f"({', '.join(f.get('args', []))})" if f.get("args") else "()"
                a(f"    {f['name']}{sig}")

        return "\n".join(lines) + "\n"

    def _collect_modules(self, project_dir: Path) -> list[tuple[str, int, str]]:
        """Collect all source files with line counts.

        Returns list of (relative_path, lines, language) tuples.
        """
        modules: list[tuple[str, int, str]] = []

        # Skip patterns
        skip_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules"}

        for path in project_dir.rglob("*"):
            if not path.is_file():
                continue
            if any(part in skip_dirs for part in path.parts):
                continue

            rel = path.relative_to(project_dir)
            rel_str = str(rel)

            # Skip hidden and cache files
            if rel_str.startswith(".") or ".pyc" in rel_str:
                continue

            # Detect language
            lang = self._detect_language(path)
            if not lang:
                continue

            try:
                lines = len(path.read_text(encoding="utf-8").splitlines())
            except Exception:
                lines = 0

            modules.append((rel_str, lines, lang))

        return sorted(modules)

    def _detect_language(self, path: Path) -> str | None:
        """Detect programming language from file extension."""
        ext = path.suffix.lower()
        mapping = {
            ".py": "py",
            ".js": "js",
            ".ts": "ts",
            ".jsx": "jsx",
            ".tsx": "tsx",
            ".go": "go",
            ".rs": "rs",
            ".java": "java",
            ".kt": "kt",
            ".scala": "scala",
            ".rb": "rb",
            ".php": "php",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "h",
            ".hpp": "hpp",
            ".cs": "cs",
            ".swift": "swift",
            ".m": "objc",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".json": "json",
            ".toml": "toml",
            ".md": "md",
        }
        return mapping.get(ext)

    def _analyze_py_file(self, path: Path) -> tuple[list[dict], list[dict]]:
        """Analyze Python file and return (functions, classes)."""
        try:
            import ast

            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception:
            return [], []

        rel_path = path.name
        functions: list[dict] = []
        classes: list[dict] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = self._extract_function_info(node, rel_path)
                functions.append(func_info)
            elif isinstance(node, ast.ClassDef):
                cls_info = self._extract_class_info(node, rel_path)
                classes.append(cls_info)

        return functions, classes

    def _extract_function_info(self, node: Any, module: str) -> dict:
        """Extract function metadata from AST node."""
        cc = self._calculate_cc(node)
        args = [arg.arg for arg in node.args.args if arg.arg != "self"]

        # Count function calls (fan-out approximation)
        fan_out = 0
        for child in ast.walk(node):  # type: ignore[name-defined]
            if isinstance(child, ast.Call):
                fan_out += 1

        return {
            "name": node.name,
            "module": module,
            "args": args,
            "cc": cc,
            "fan": fan_out,
            "line": node.lineno if hasattr(node, "lineno") else 0,
        }

    def _extract_class_info(self, node: Any, module: str) -> dict:
        """Extract class metadata from AST node."""
        methods: list[dict] = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self._extract_function_info(item, module)
                method_info["name"] = f"{node.name}.{method_info['name']}"
                methods.append(method_info)

        return {
            "name": node.name,
            "module": module,
            "methods": methods,
            "line": node.lineno if hasattr(node, "lineno") else 0,
        }

    def _calculate_cc(self, node: Any) -> int:
        """Calculate cyclomatic complexity for a function node."""
        cc = 1  # Base complexity

        for child in ast.walk(node):  # type: ignore[name-defined]
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                cc += 1
            elif isinstance(child, ast.BoolOp):
                cc += len(child.values) - 1

        return cc

    def _identify_hotspots(self, functions: list[dict]) -> list[dict]:
        """Identify high fan-out functions (hotspots)."""
        if not functions:
            return []

        sorted_funcs = sorted(functions, key=lambda f: f.get("fan", 0), reverse=True)
        return sorted_funcs[:5]

    def _generate_alerts(self, functions: list[dict], modules: list[tuple]) -> list[str]:
        """Generate quality alerts based on metrics."""
        alerts: list[str] = []

        # High CC functions
        high_cc = [f for f in functions if f.get("cc", 1) >= 15]
        for f in high_cc[:3]:
            alerts.append(f"high-cc {f['name']}={f['cc']}")

        # Large files
        large_files = [(m[0], m[1]) for m in modules if m[1] > 500]
        for path, lines in large_files[:3]:
            alerts.append(f"large-file {path}={lines}L")

        return alerts


# Try to import and use oqlos.sumd if available
try:
    from sumd.extractor import (  # type: ignore[import]
        extract_pyproject,
        extract_source_snippets,
        extract_taskfile,
        generate_map_toon as _sumd_generate_map_toon,
    )
    from sumd.parser import parse_file  # type: ignore[import]

    HAS_SUMD = True
except ImportError:
    HAS_SUMD = False


def analyze_with_sumd(project_dir: Path) -> dict[str, Any]:
    """Analyze project using sumd if available, fallback to native analyzer.

    Args:
        project_dir: Path to project root

    Returns:
        dict with 'map_content', 'snippets', 'metrics', 'available'
    """
    project_dir = project_dir.resolve()

    if HAS_SUMD:
        try:
            # Use oqlos.sumd directly
            map_content = _sumd_generate_map_toon(project_dir)
            pkg_name = project_dir.name
            snippets = extract_source_snippets(project_dir, pkg_name)

            # Parse metrics from map content
            metrics = _parse_map_metrics(map_content)

            return {
                "available": True,
                "map_content": map_content,
                "snippets": snippets,
                "metrics": metrics,
                "source": "oqlos.sumd",
            }
        except Exception as e:
            # Fall back to native analyzer
            pass

    # Native fallback
    analyzer = SumdAnalyzer()
    map_content = analyzer.generate_map_toon(project_dir)
    metrics_result = analyzer.analyze(project_dir)

    return {
        "available": True,
        "map_content": map_content,
        "snippets": [],
        "metrics": {
            "files": metrics_result.total_files,
            "lines": metrics_result.total_lines,
            "functions": metrics_result.total_functions,
            "classes": metrics_result.total_classes,
            "cc_mean": metrics_result.cc_mean,
            "critical": metrics_result.critical_count,
        },
        "source": "native",
    }


def _parse_map_metrics(map_content: str) -> dict[str, Any]:
    """Parse metrics from map.toon.yaml content."""
    metrics: dict[str, Any] = {}

    # Parse header line: # proj | 10f 500L | py:10 | 2024-01-01
    for line in map_content.splitlines()[:5]:
        if line.startswith("# stats:"):
            # Extract: X func | Y cls | Z mod | CC̄=W | critical:V
            match = re.search(
                r"(\d+) func.*?(\d+) cls.*?(\d+) mod.*?CC̄=([\d.]+).*?critical:(\d+)",
                line,
            )
            if match:
                metrics["functions"] = int(match.group(1))
                metrics["classes"] = int(match.group(2))
                metrics["modules"] = int(match.group(3))
                metrics["cc_mean"] = float(match.group(4))
                metrics["critical"] = int(match.group(5))

    return metrics


__all__ = [
    "SumdAnalyzer",
    "SumdMetrics",
    "analyze_with_sumd",
    "HAS_SUMD",
]
