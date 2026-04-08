"""
Radon analyzer wrapper — opcjonalne źródło CC przez radon cc -j.

T008: Integracja radon jako alternatywnego źródła metryk CC.
Używane gdy dostępne, w przeciwnym razie fallback do ast.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def is_radon_available() -> bool:
    """Sprawdź czy radon jest zainstalowany i dostępny."""
    return shutil.which("radon") is not None


def _normalize_radon_path(path_value: str, project_dir: Path | None = None) -> str:
    """Normalize a radon path to a stable project-relative key when possible."""
    raw_path = Path(path_value)

    if project_dir is not None and raw_path.is_absolute():
        try:
            return str(raw_path.resolve().relative_to(project_dir.resolve()))
        except (OSError, ValueError):
            return str(raw_path.resolve())

    return raw_path.as_posix()


def run_radon_cc(project_dir: Path, excludes: list[str] | None = None) -> dict[str, Any]:
    """
    Uruchom `radon cc -j` i zwróć sparsowane wyniki.

    Returns:
        Dict mapping file paths to list of complexity results per function/class.
    """
    if not is_radon_available():
        logger.debug("radon not available")
        return {}

    cmd = ["radon", "cc", "-j", str(project_dir)]

    if excludes:
        for pattern in excludes:
            cmd.extend(["--exclude", pattern])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if result.returncode != 0 and not result.stdout:
            logger.warning("radon cc failed: %s", result.stderr[:200])
            return {}

        # radon zwraca JSON dict: {filepath: [{name, lineno, col_offset, complexity, rank}, ...]}
        return json.loads(result.stdout) if result.stdout else {}
    except subprocess.TimeoutExpired:
        logger.warning("radon cc timeout after 120s")
        return {}
    except json.JSONDecodeError as e:
        logger.warning("radon cc invalid JSON: %s", e)
        return {}
    except Exception as e:
        logger.warning("radon cc error: %s", e)
        return {}


def extract_max_cc_per_file(
    radon_results: dict[str, Any],
    project_dir: Path | None = None,
) -> dict[str, int]:
    """
    Ekstraktuj maksymalne CC per plik z wyników radon.

    Returns:
        Dict: {relative_path: max_cc}
    """
    max_cc_by_file: dict[str, int] = {}

    for abs_path, entries in radon_results.items():
        if not isinstance(entries, list):
            continue

        normalized_path = _normalize_radon_path(abs_path, project_dir)

        max_cc = 0
        for entry in entries:
            if isinstance(entry, dict):
                cc = entry.get("complexity", 0)
                max_cc = max(max_cc, cc)

        if max_cc > 0:
            existing = max_cc_by_file.get(normalized_path, 0)
            max_cc_by_file[normalized_path] = max(existing, max_cc)

    return max_cc_by_file


def enhance_metrics_with_radon(
    metrics: list[Any],
    project_dir: Path,
) -> None:
    """
    Uzupełnij metryki o dokładne CC z radon (jeśli dostępne).

    Args:
        metrics: Lista obiektów CodeMetrics (modyfikowane w miejscu)
        project_dir: Ścieżka do projektu
    """
    radon_results = run_radon_cc(project_dir)
    if not radon_results:
        return

    max_cc_by_file = extract_max_cc_per_file(radon_results, project_dir)
    basename_index: dict[str, list[int]] = {}
    for path_key, cc in max_cc_by_file.items():
        basename_index.setdefault(Path(path_key).name, []).append(cc)

    updated = 0
    for metric in metrics:
        if not metric.file_path:
            continue

        metric_path = Path(metric.file_path).as_posix()
        file_name = Path(metric_path).name

        cc = max_cc_by_file.get(metric_path)
        if cc is None:
            name_matches = basename_index.get(file_name, [])
            if len(name_matches) == 1:
                cc = name_matches[0]

        if cc is None or cc <= metric.cyclomatic_complexity:
            continue

        metric.cyclomatic_complexity = cc
        updated += 1

    if updated:
        logger.info("Enhanced %d metrics with radon CC data", updated)
