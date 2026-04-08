"""
Analiza inkrementalna — analizuj tylko zmienione pliki (git diff).

Punkt 2.4 z planu ewolucji:
- get_changed_files(project_dir, since)     → lista zmienionych .py
- IncrementalAnalyzer                        → analizuje tylko te pliki
- EvolutionaryCache                          → cache wyników per-plik (hash-based)

Strategia:
1. git diff --name-only <since> → lista plików
2. Jeśli lista pusta → pełna analiza (fallback)
3. Jeśli pliki → analizuj tylko zmienione + scal z cached poprzednim wynikiem
"""

from __future__ import annotations

import hashlib
import json
import logging
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from .metrics import AnalysisResult, CodeMetrics

if TYPE_CHECKING:
    from .analyzer import CodeAnalyzer

logger = logging.getLogger(__name__)

_CACHE_FILE = ".redsl_analysis_cache.json"


def get_changed_files(project_dir: Path, since: str = "HEAD") -> list[Path]:
    """Pobierz listę zmienionych plików .py od podanego commita/ref.

    Args:
        project_dir: Katalog projektu (git root)
        since:       Git ref (commit hash, branch, "HEAD~1", etc.)

    Returns:
        Lista ścieżek do zmienionych plików .py (tylko istniejące).
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", since],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            logger.debug("git diff failed (returncode=%d): %s", result.returncode, result.stderr)
            return []

        changed: list[Path] = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.endswith(".py"):
                full_path = project_dir / line
                if full_path.exists():
                    changed.append(full_path)

        logger.info("Changed files since %s: %d .py files", since, len(changed))
        return changed

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.debug("git not available or timed out: %s", e)
        return []


def get_staged_files(project_dir: Path) -> list[Path]:
    """Pobierz listę staged plików .py (git diff --cached)."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return []
        return [
            project_dir / line.strip()
            for line in result.stdout.splitlines()
            if line.strip().endswith(".py") and (project_dir / line.strip()).exists()
        ]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def _file_hash(file_path: Path) -> str:
    """Oblicz MD5 hash zawartości pliku dla cache invalidation."""
    try:
        content = file_path.read_bytes()
        return hashlib.md5(content).hexdigest()
    except OSError:
        return ""


class EvolutionaryCache:
    """Cache wyników analizy per-plik oparty o hash pliku.

    Pozwala pomijać ponowną analizę niezmiennych plików między cyklami.
    """

    def __init__(self, project_dir: Path) -> None:
        self._path = project_dir / _CACHE_FILE
        self._data: dict[str, dict] = self._load()

    def _load(self) -> dict[str, dict]:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def save(self) -> None:
        try:
            self._path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        except OSError as e:
            logger.warning("Could not save analysis cache: %s", e)

    def get(self, file_path: Path) -> dict | None:
        """Zwróć cached metryki dla pliku lub None jeśli cache miss/stale."""
        key = str(file_path)
        entry = self._data.get(key)
        if entry is None:
            return None
        if entry.get("hash") != _file_hash(file_path):
            return None
        return entry.get("metrics")

    def set(self, file_path: Path, metrics: dict) -> None:
        """Zapisz metryki dla pliku do cache."""
        self._data[str(file_path)] = {
            "hash": _file_hash(file_path),
            "metrics": metrics,
        }

    def invalidate(self, file_path: Path) -> None:
        """Usuń plik z cache (wymuś ponowną analizę)."""
        self._data.pop(str(file_path), None)

    def clear(self) -> None:
        """Wyczyść cały cache."""
        self._data.clear()


class IncrementalAnalyzer:
    """Analizuje tylko zmienione pliki i scala z cached wynikami.

    Gdy nie ma zmian → pełna analiza.
    Gdy są zmiany → analizuj tylko zmienione, resztę wczytaj z cache.
    """

    def __init__(self, base_analyzer: "CodeAnalyzer") -> None:
        self._analyzer = base_analyzer

    def analyze_changed(
        self,
        project_dir: Path,
        since: str = "HEAD",
        use_cache: bool = True,
    ) -> AnalysisResult:
        """Analizuj projekt inkrementalnie.

        Args:
            project_dir: Katalog projektu
            since:       Git ref do porównania (domyślnie HEAD — unstaged changes)
            use_cache:   Czy używać EvolutionaryCache

        Returns:
            AnalysisResult — pełne wyniki (zmienione + cached)
        """
        changed = get_changed_files(project_dir, since)

        if not changed:
            logger.info("No changed files detected — running full analysis")
            result = self._analyzer.analyze_project(project_dir)
            if use_cache:
                cache = EvolutionaryCache(project_dir)
                self._populate_cache(result, project_dir, cache)
                cache.save()
            return result

        logger.info("Incremental analysis: %d changed files", len(changed))

        if not use_cache:
            return self._analyze_subset(changed, project_dir)

        cache = EvolutionaryCache(project_dir)
        return self._merge_with_cache(changed, project_dir, cache)

    def _analyze_subset(self, files: list[Path], project_dir: Path) -> AnalysisResult:
        """Analizuj tylko podany podzbiór plików."""
        from .python_analyzer import PythonAnalyzer

        py = PythonAnalyzer()
        result = AnalysisResult(project_name=project_dir.name)

        for py_file in files:
            file_data = py._parse_single_file(py_file, project_dir)
            if file_data:
                py._accumulate_file_metrics(file_data, result)

        result.total_files = len(files)
        result.total_lines = sum(m.module_lines for m in result.metrics if not m.function_name)
        cc_vals = [m.cyclomatic_complexity for m in result.metrics if m.cyclomatic_complexity > 0]
        result.avg_cc = round(sum(cc_vals) / len(cc_vals), 2) if cc_vals else 0.0

        return result

    def _collect_cached_metrics(
        self,
        project_dir: Path,
        changed_rel: set[str],
        cache: EvolutionaryCache,
    ) -> list[CodeMetrics]:
        """Collect cached metrics for files that haven't changed."""
        cached_metrics: list[CodeMetrics] = []
        for py_file in project_dir.rglob("*.py"):
            rel = str(py_file.relative_to(project_dir))
            if rel in changed_rel:
                continue
            cached = cache.get(py_file)
            if cached:
                try:
                    m = CodeMetrics(**{
                        k: v for k, v in cached.items()
                        if k in CodeMetrics.__dataclass_fields__
                    })
                    cached_metrics.append(m)
                except (TypeError, AttributeError):
                    pass
        return cached_metrics

    @staticmethod
    def _calculate_result_stats(result: AnalysisResult) -> None:
        """Calculate statistics (avg_cc, total_files, total_lines) for result."""
        cc_vals = [m.cyclomatic_complexity for m in result.metrics if m.cyclomatic_complexity > 0]
        result.avg_cc = round(sum(cc_vals) / len(cc_vals), 2) if cc_vals else 0.0
        result.total_files = len({m.file_path for m in result.metrics if not m.function_name})
        result.total_lines = sum(m.module_lines for m in result.metrics if not m.function_name)

    def _merge_with_cache(
        self, changed: list[Path], project_dir: Path, cache: EvolutionaryCache
    ) -> AnalysisResult:
        """Scal świeżo przeanalizowane pliki z cached poprzednimi wynikami."""
        fresh = self._analyze_subset(changed, project_dir)
        changed_rel = {str(f.relative_to(project_dir)) for f in changed}

        merged = AnalysisResult(project_name=project_dir.name)
        merged.metrics.extend(fresh.metrics)

        # Add cached metrics for unchanged files
        cached_metrics = self._collect_cached_metrics(project_dir, changed_rel, cache)
        merged.metrics.extend(cached_metrics)

        # Update cache with fresh results
        self._populate_cache(fresh, project_dir, cache)
        cache.save()

        # Calculate final statistics
        self._calculate_result_stats(merged)

        logger.info(
            "Incremental merge: %d fresh + %d cached → %d total metrics",
            len(fresh.metrics), len(cached_metrics), len(merged.metrics),
        )
        return merged

    @staticmethod
    def _populate_cache(
        result: AnalysisResult, project_dir: Path, cache: EvolutionaryCache
    ) -> None:
        """Zapisz wyniki analizy do cache."""
        for m in result.metrics:
            if m.function_name:
                continue
            try:
                full_path = project_dir / m.file_path
                if full_path.exists():
                    cache.set(full_path, {
                        k: getattr(m, k)
                        for k in CodeMetrics.__dataclass_fields__
                    })
            except (OSError, AttributeError):
                pass
