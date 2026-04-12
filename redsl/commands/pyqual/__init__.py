"""
Python code quality analysis — fasada PyQualAnalyzer.

Subpackage:
- ruff_analyzer   — statyczna analiza stylu (ruff)
- mypy_analyzer   — sprawdzanie typów (mypy)
- bandit_analyzer — analiza bezpieczeństwa (bandit)
- ast_analyzer    — analiza AST (unused imports, magic numbers, docstrings)
- reporter        — rekomendacje i zapis raportów
"""

from __future__ import annotations

import fnmatch
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .ast_analyzer import AstAnalyzer
from .bandit_analyzer import BanditAnalyzer
from .mypy_analyzer import MypyAnalyzer
from .reporter import Reporter
from .ruff_analyzer import RuffAnalyzer

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG: dict = {
    "include": ["**/*.py"],
    "exclude": ["**/__pycache__/**", "**/tests/**", "**/.venv/**", "**/venv/**", "**/.tox/**", "**/node_modules/**", "**/.git/**"],
    "tools": {
        "ruff": {"enabled": True},
        "mypy": {"enabled": True},
        "bandit": {"enabled": True},
    },
    "rules": {
        "unused-imports": {"enabled": True, "severity": "error"},
        "magic-numbers": {"enabled": True, "severity": "warning"},
        "print-statements": {"enabled": True, "severity": "warning"},
        "missing-docstrings": {"enabled": True, "severity": "warning"},
    },
    "metrics": {
        "complexity": {"enabled": True, "max_complexity": 10},
        "maintainability": {"enabled": True, "min_maintainability": 70},
    },
}


class PyQualAnalyzer:
    """Python code quality analyzer — fasada nad wyspecjalizowanymi analizatorami."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize analyzer with configuration."""
        self.config_path = config_path or Path("pyqual.yaml")
        self.config = self._load_config()
        self.results: Dict[str, Any] = {
            "project_root": str(Path.cwd()),
            "timestamp": None,
            "summary": {},
            "issues": {},
            "metrics": {},
            "recommendations": [],
        }
        self._ruff = RuffAnalyzer()
        self._mypy = MypyAnalyzer()
        self._bandit = BanditAnalyzer()
        self._ast = AstAnalyzer()
        self._reporter = Reporter()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            logger.warning("Config file %s not found, using defaults", self.config_path)
            return dict(_DEFAULT_CONFIG)
        import yaml
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def analyze_project(self, project_path: Path) -> Dict[str, Any]:
        """Analyze entire project for code quality."""
        self.results["timestamp"] = datetime.now().isoformat()
        python_files = self._find_python_files(project_path)
        self.results["summary"]["total_files"] = len(python_files)

        self._ruff.analyze(python_files, self.results, self.config)
        self._mypy.analyze(python_files, self.results, self.config)
        self._bandit.analyze(python_files, self.results, self.config)
        self._ast.analyze(python_files, self.results, self.config)
        self._reporter.calculate_metrics(python_files, self.results, self.config)
        self._reporter.generate_recommendations(self.results)

        return self.results

    def _find_python_files(self, project_path: Path) -> List[Path]:
        """Find all Python files matching include/exclude patterns."""
        files = []
        include_patterns = self.config.get("include", ["**/*.py"])
        exclude_patterns = self.config.get("exclude", [])
        project_path = project_path.resolve()

        for pattern in include_patterns:
            for file_path in project_path.glob(pattern):
                if file_path.is_file() and not self._is_excluded(
                    file_path, project_path, exclude_patterns
                ):
                    files.append(file_path)

        return sorted(set(files))

    @staticmethod
    def _is_excluded(
        file_path: Path, project_path: Path, exclude_patterns: list[str]
    ) -> bool:
        """Sprawdź czy plik pasuje do wzorców wykluczeń."""
        rel_path = file_path.relative_to(project_path)
        rel_path_str = str(rel_path)
        parts = rel_path.parts
        for excl_pattern in exclude_patterns:
            if fnmatch.fnmatch(rel_path_str, excl_pattern):
                return True
            # Extract the core directory name from patterns like **/.venv/**
            core = excl_pattern.strip("*").strip("/")
            if core and any(p == core for p in parts):
                return True
        return False

    def save_report(self, output_path: Path, format: str = "yaml") -> None:
        """Save analysis report."""
        self._reporter.save_report(self.results, output_path, format)


def _format_pyqual_issues(summary: Dict[str, Any]) -> str:
    """Format pyqual issues section."""
    return (
        f"  - Unused imports: {summary.get('unused_imports', 0)}\n"
        f"  - Magic numbers: {summary.get('magic_numbers', 0)}\n"
        f"  - Print statements: {summary.get('print_statements', 0)}\n"
        f"  - Missing docstrings: {summary.get('missing_docstrings', 0)}\n"
        f"  - Type issues (mypy): {summary.get('mypy_issues', 0)}\n"
        f"  - Style issues (ruff): {summary.get('ruff_errors', 0)} errors, "
        f"{summary.get('ruff_warnings', 0)} warnings\n"
        f"  - Security issues: {summary.get('security_issues', 0)}"
    )


def _format_pyqual_metrics(metrics: Dict[str, Any]) -> str:
    """Format pyqual metrics section."""
    return (
        f"  - Average complexity: {metrics.get('average_complexity', 0):.1f}\n"
        f"  - Max complexity: {metrics.get('max_complexity', 0)}\n"
        f"  - Average maintainability: {metrics.get('average_maintainability', 0):.1f}"
    )


def _format_pyqual_recommendations(recommendations: list) -> str:
    """Format pyqual recommendations section."""
    lines = []
    for rec in recommendations[:5]:
        lines.append(f"  - [{rec['priority'].upper()}] {rec['message']}")
    return "\n".join(lines)


def _print_pyqual_report(project_name: str, results: Dict[str, Any], output_file: Path) -> None:
    """Print pyqual analysis report to sections."""
    print(f"\n{'='*60}")
    print("PYQUAL CODE QUALITY REPORT")
    print(f"{'='*60}")
    print(f"Project: {project_name}")
    print(f"Files analyzed: {results['summary']['total_files']}")
    print("\nIssues found:")
    print(_format_pyqual_issues(results['summary']))
    print("\nMetrics:")
    print(_format_pyqual_metrics(results['metrics']))
    print("\nTop recommendations:")
    print(_format_pyqual_recommendations(results["recommendations"]))
    print(f"\nFull report saved to: {output_file}")


def run_pyqual_analysis(
    project_path: Path,
    config_path: Optional[Path] = None,
    output_format: str = "yaml",
) -> Dict[str, Any]:
    """Run pyqual analysis on a project."""
    analyzer = PyQualAnalyzer(config_path)
    results = analyzer.analyze_project(project_path)

    output_file = project_path / f"pyqual_report.{output_format}"
    analyzer.save_report(output_file, output_format)

    _print_pyqual_report(project_path.name, results, output_file)

    return results


def run_pyqual_fix(
    project_path: Path,
    config_path: Optional[Path] = None,
) -> None:
    """Run automatic fixes based on pyqual analysis."""
    from ...analyzers import CodeAnalyzer
    from ...config import AgentConfig
    from ...dsl import RefactorAction
    from ...orchestrator import RefactorOrchestrator
    from ...execution import _execute_direct_refactor

    pyqual_analyzer = PyQualAnalyzer(config_path)
    results = pyqual_analyzer.analyze_project(project_path)

    fixable_actions = [r["action"] for r in results["recommendations"] if r.get("action")]
    if not fixable_actions:
        print("No automatic fixes available.")
        return

    print("\nApplying automatic fixes...")

    config = AgentConfig()
    config.refactor.apply_changes = True
    config.refactor.reflection_rounds = 0

    orchestrator = RefactorOrchestrator(config)
    code_analyzer = CodeAnalyzer()
    analysis = code_analyzer.analyze_project(project_path)
    contexts = analysis.to_dsl_contexts()
    all_decisions = orchestrator.dsl_engine.evaluate(contexts)

    action_map = {
        "REMOVE_UNUSED_IMPORTS": RefactorAction.REMOVE_UNUSED_IMPORTS,
        "EXTRACT_CONSTANTS": RefactorAction.EXTRACT_CONSTANTS,
        "FIX_MODULE_EXECUTION_BLOCK": RefactorAction.FIX_MODULE_EXECUTION_BLOCK,
        "ADD_RETURN_TYPES": RefactorAction.ADD_RETURN_TYPES,
    }

    total_applied = 0
    for action_str in fixable_actions:
        if action_str in action_map:
            action = action_map[action_str]
            for decision in (d for d in all_decisions if d.action == action):
                result = _execute_direct_refactor(orchestrator, decision, project_path)
                if result.applied:
                    total_applied += 1

    print(f"Applied {total_applied} automatic fixes.")

    print("\nRe-running analysis...")
    new_results = pyqual_analyzer.analyze_project(project_path)
    print("\nImprovement:")
    for key, label in [
        ("unused_imports", "Unused imports"),
        ("magic_numbers", "Magic numbers"),
        ("print_statements", "Print statements"),
    ]:
        before = results["summary"].get(key, 0)
        after = new_results["summary"].get(key, 0)
        print(f"  - {label}: {before} → {after}")


__all__ = [
    "PyQualAnalyzer",
    "run_pyqual_analysis",
    "run_pyqual_fix",
    "RuffAnalyzer",
    "MypyAnalyzer",
    "BanditAnalyzer",
    "AstAnalyzer",
    "Reporter",
]
