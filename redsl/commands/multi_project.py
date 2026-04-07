"""
Multi-project orchestration — punkt 3.4 z planu ewolucji.

Uruchamia ReDSL analizę / cykle refaktoryzacji na wielu projektach jednocześnie.

Użycie:
    from redsl.commands.multi_project import MultiProjectRunner

    runner = MultiProjectRunner(config)
    report = runner.analyze([Path("proj_a"), Path("proj_b")])
    for name, result in report.results.items():
        print(name, result.avg_cc)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from redsl.analyzers import AnalysisResult, CodeAnalyzer
from redsl.config import AgentConfig

logger = logging.getLogger(__name__)


@dataclass
class ProjectAnalysis:
    """Wyniki analizy pojedynczego projektu."""

    name: str
    path: Path
    result: AnalysisResult | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.result is not None and self.error is None

    @property
    def avg_cc(self) -> float:
        return self.result.avg_cc if self.result else 0.0

    @property
    def critical_count(self) -> int:
        return self.result.critical_count if self.result else 0

    @property
    def total_files(self) -> int:
        return self.result.total_files if self.result else 0


@dataclass
class MultiProjectReport:
    """Zbiorczy raport z analizy wielu projektów."""

    results: dict[str, ProjectAnalysis] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def total_projects(self) -> int:
        return len(self.results)

    @property
    def successful(self) -> int:
        return sum(1 for r in self.results.values() if r.ok)

    @property
    def failed(self) -> int:
        return self.total_projects - self.successful

    @property
    def aggregate_avg_cc(self) -> float:
        ccs = [r.avg_cc for r in self.results.values() if r.ok]
        return round(sum(ccs) / len(ccs), 2) if ccs else 0.0

    @property
    def aggregate_critical(self) -> int:
        return sum(r.critical_count for r in self.results.values() if r.ok)

    @property
    def aggregate_files(self) -> int:
        return sum(r.total_files for r in self.results.values() if r.ok)

    def worst_projects(self, n: int = 5) -> list[ProjectAnalysis]:
        """Zwróć n projektów z najwyższym avg CC."""
        ok = [r for r in self.results.values() if r.ok]
        return sorted(ok, key=lambda r: r.avg_cc, reverse=True)[:n]

    def summary(self) -> str:
        """Tekstowe podsumowanie raportu."""
        lines = [
            f"Multi-Project Analysis: {self.successful}/{self.total_projects} ok",
            f"  Total files:    {self.aggregate_files}",
            f"  Aggregate CC:   {self.aggregate_avg_cc:.1f}",
            f"  Critical issues:{self.aggregate_critical}",
        ]
        if self.failed:
            lines.append(f"  Failed:         {self.failed} project(s)")
            for err in self.errors[:5]:
                lines.append(f"    - {err}")
        if self.successful:
            worst = self.worst_projects(3)
            lines.append("  Worst CC:")
            for proj in worst:
                lines.append(f"    {proj.name}: CC={proj.avg_cc:.1f}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_projects": self.total_projects,
            "successful": self.successful,
            "failed": self.failed,
            "aggregate_avg_cc": self.aggregate_avg_cc,
            "aggregate_critical": self.aggregate_critical,
            "aggregate_files": self.aggregate_files,
            "projects": {
                name: {
                    "avg_cc": pa.avg_cc,
                    "critical_count": pa.critical_count,
                    "total_files": pa.total_files,
                    "ok": pa.ok,
                    "error": pa.error,
                }
                for name, pa in self.results.items()
            },
        }


class MultiProjectRunner:
    """Uruchamia ReDSL na wielu projektach."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        self.config = config or AgentConfig.from_env()
        self._analyzer = CodeAnalyzer()

    def analyze(
        self,
        project_dirs: list[Path],
        fail_fast: bool = False,
    ) -> MultiProjectReport:
        """Analizuj wiele projektów i zbierz wyniki.

        Args:
            project_dirs: Lista katalogów projektów
            fail_fast:    Przerwij przy pierwszym błędzie

        Returns:
            MultiProjectReport z wynikami dla każdego projektu.
        """
        report = MultiProjectReport()

        for proj_dir in project_dirs:
            name = proj_dir.name
            logger.info("Analyzing project: %s", proj_dir)
            pa = self._analyze_one(proj_dir)
            report.results[name] = pa

            if pa.error:
                report.errors.append(f"{name}: {pa.error}")
                if fail_fast:
                    logger.error("fail_fast: stopping after error in %s", name)
                    break

        logger.info(
            "Multi-project analysis done: %d/%d ok, aggregate CC=%.1f",
            report.successful, report.total_projects, report.aggregate_avg_cc,
        )
        return report

    def analyze_from_paths(
        self,
        paths: list[str],
        fail_fast: bool = False,
    ) -> MultiProjectReport:
        """Analiza z listy ścieżek jako string."""
        return self.analyze([Path(p) for p in paths], fail_fast=fail_fast)

    def run_cycles(
        self,
        project_dirs: list[Path],
        max_actions_per_project: int = 3,
        fail_fast: bool = False,
    ) -> dict[str, Any]:
        """Uruchom pełne cykle refaktoryzacji na wielu projektach.

        Args:
            project_dirs:            Lista katalogów projektów
            max_actions_per_project: Limit akcji na projekt
            fail_fast:               Przerwij przy pierwszym błędzie

        Returns:
            Słownik {project_name: CycleReport} z raportami cykli.
        """
        from redsl.orchestrator import RefactorOrchestrator

        orchestrator = RefactorOrchestrator(self.config)
        cycle_reports: dict[str, Any] = {}

        for proj_dir in project_dirs:
            name = proj_dir.name
            logger.info("Running refactor cycle: %s", proj_dir)
            try:
                report = orchestrator.run_cycle(proj_dir, max_actions=max_actions_per_project)
                cycle_reports[name] = report
                logger.info(
                    "  %s: %d applied, %d rejected",
                    name, report.proposals_applied, report.proposals_rejected,
                )
            except Exception as e:
                logger.error("Cycle failed for %s: %s", name, e)
                cycle_reports[name] = {"error": str(e)}
                if fail_fast:
                    break

        return cycle_reports

    def rank_by_priority(
        self,
        report: MultiProjectReport,
        key: str = "avg_cc",
    ) -> list[ProjectAnalysis]:
        """Posortuj projekty według priorytetu refaktoryzacji.

        Args:
            report: Wyniki analizy
            key:    Klucz sortowania: 'avg_cc' | 'critical_count' | 'total_files'

        Returns:
            Lista ProjectAnalysis od najgorszego do najlepszego.
        """
        ok = [r for r in report.results.values() if r.ok]
        return sorted(ok, key=lambda r: getattr(r, key, 0), reverse=True)

    def _analyze_one(self, proj_dir: Path) -> ProjectAnalysis:
        pa = ProjectAnalysis(name=proj_dir.name, path=proj_dir)
        if not proj_dir.exists():
            pa.error = f"Directory not found: {proj_dir}"
            return pa
        try:
            pa.result = self._analyzer.analyze_project(proj_dir)
        except Exception as e:
            pa.error = str(e)
            logger.warning("Analysis failed for %s: %s", proj_dir, e)
        return pa


def run_multi_analysis(project_dirs: list[Path], config: AgentConfig | None = None) -> MultiProjectReport:
    """Convenience function — analiza wielu projektów."""
    return MultiProjectRunner(config).analyze(project_dirs)
