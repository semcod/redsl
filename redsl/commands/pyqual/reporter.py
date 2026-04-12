"""Generowanie raportów i rekomendacji na podstawie wyników analizy."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class Reporter:
    """Generuje rekomendacje i zapisuje raporty analizy jakości."""

    def calculate_metrics(self, files: list[Path], results: dict[str, Any], config: dict) -> None:
        """Oblicz metryki złożoności i utrzymywalności kodu."""
        try:
            from radon.complexity import cc_visit
            from radon.metrics import mi_visit
        except ImportError:
            logger.warning("Radon not installed, skipping complexity and maintainability metrics")
            results["metrics"].update({
                "total_lines": 0,
                "average_complexity": 0,
                "max_complexity": 0,
                "average_maintainability": 0,
            })
            return

        total_lines = 0
        complexities: list[float] = []
        maintainability_scores: list[float] = []

        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8")
                total_lines += len(content.splitlines())
                self._collect_file_metrics(content, file_path, complexities, maintainability_scores,
                                           cc_visit, mi_visit)
            except Exception as e:
                logger.warning("Failed to calculate metrics for %s: %s", file_path, e)

        self._store_metrics_results(results, complexities, maintainability_scores, total_lines, files, config)

    @staticmethod
    def _store_metrics_results(
        results: dict[str, Any],
        complexities: list[float],
        maintainability_scores: list[float],
        total_lines: int,
        files: list[Path],
        config: dict,
    ) -> None:
        """Store calculated metrics and violation counts into results."""
        max_cc = config.get("metrics", {}).get("complexity", {}).get("max_complexity", 10)
        min_mi = config.get("metrics", {}).get("maintainability", {}).get("min_maintainability", 70)

        results["metrics"].update({
            "total_lines": total_lines,
            "average_complexity": sum(complexities) / len(files) if files else 0,
            "max_complexity": max(complexities) if complexities else 0,
            "average_maintainability": (
                sum(maintainability_scores) / len(maintainability_scores)
                if maintainability_scores else 0
            ),
        })
        results["summary"]["complexity_violations"] = sum(1 for c in complexities if c > max_cc)
        results["summary"]["maintainability_violations"] = sum(
            1 for m in maintainability_scores if m < min_mi
        )

    @staticmethod
    def _collect_file_metrics(
        content: str,
        file_path: Path,
        complexities: list,
        maintainability_scores: list,
        cc_visit: Any,
        mi_visit: Any,
    ) -> None:
        """Zbierz metryki z jednego pliku."""
        try:
            cc_results = cc_visit(content)
            if cc_results:
                max_func_cc = max(item.complexity for item in cc_results)
                complexities.append(max_func_cc)
        except Exception as e:
            logger.debug("Failed to calculate complexity for %s: %s", file_path, e)

        try:
            mi = mi_visit(content, multi=True)
            maintainability_scores.append(mi)
        except Exception as e:
            logger.debug("Failed to calculate maintainability for %s: %s", file_path, e)

    def generate_recommendations(self, results: dict[str, Any]) -> None:
        """Generuj rekomendacje poprawy na podstawie znalezionych problemów."""
        recommendations: list[dict] = []
        summary = results["summary"]

        _issue_rules = [
            ("unused_imports", "cleanup", "high",
             lambda n: f"Remove {n} unused imports", "REMOVE_UNUSED_IMPORTS"),
            ("magic_numbers", "quality", "medium",
             lambda n: f"Extract {n} magic numbers to constants", "EXTRACT_CONSTANTS"),
            ("print_statements", "quality", "medium",
             lambda n: f"Remove or replace {n} print statements", "FIX_MODULE_EXECUTION_BLOCK"),
            ("missing_docstrings", "documentation", "low",
             lambda n: f"Add docstrings to {n} functions/classes", None),
            ("complexity_violations", "refactoring", "high",
             lambda n: f"Reduce complexity in {n} functions", None),
            ("security_issues", "security", "critical",
             lambda n: f"Fix {n} security issues", None),
        ]

        for key, rtype, priority, msg_fn, action in _issue_rules:
            count = summary.get(key, 0)
            if count > 0:
                recommendations.append({
                    "type": rtype,
                    "priority": priority,
                    "message": msg_fn(count),
                    "action": action,
                })

        recommendations.sort(key=lambda r: _PRIORITY_ORDER.get(r["priority"], 4))
        results["recommendations"] = recommendations

    @staticmethod
    def save_report(results: dict[str, Any], output_path: Path, fmt: str = "yaml") -> None:
        """Zapisz raport analizy do pliku."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if fmt == "yaml":
            with open(output_path, "w") as f:
                yaml.dump(results, f, default_flow_style=False, indent=2)
        elif fmt == "json":
            with open(output_path, "w") as f:
                json.dump(results, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

        logger.info("Report saved to %s", output_path)
