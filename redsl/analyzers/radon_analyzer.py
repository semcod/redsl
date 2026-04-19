"""
Radon analyzer wrapper — opcjonalne źródło dokładniejszych metryk CC.

T008: Integracja radon jako wzbogacenia wyników AST o dokładniejsze CC.
Używane po analizie AST, gdy dostępne, aby uzupełnić brakujące hotspoty.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .metrics import AnalysisResult, CodeMetrics
from redsl.bridges.base import CliBridge

logger = logging.getLogger(__name__)

RADON_TIMEOUT_SECONDS = 30
MAX_REASONABLE_RADON_CC = 199


class _RadonBridge(CliBridge):
    cli_name = "radon"
    check_args = ["--help"]


def is_radon_available() -> bool:
    """Sprawdź czy radon jest zainstalowany i dostępny."""
    return _RadonBridge.is_available()


def _normalize_radon_path(path_value: str, project_dir: Path | None = None) -> str:
    """Normalize a radon path to a stable project-relative key when possible."""
    raw_path = Path(path_value)

    if project_dir is not None and raw_path.is_absolute():
        try:
            return str(raw_path.resolve().relative_to(project_dir.resolve()))
        except (OSError, ValueError):
            return str(raw_path.resolve())

    return raw_path.as_posix()


def _flatten_radon_blocks(entries: list[Any]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        blocks.append(entry)
        closures = entry.get("closures")
        if isinstance(closures, list) and closures:
            blocks.extend(_flatten_radon_blocks(closures))
    return blocks


def _radon_block_name(entry: dict[str, Any]) -> str:
    raw_name = entry.get("name")
    if not raw_name:
        return ""
    return str(raw_name).strip().split(".")[-1]


def _radon_block_type(entry: dict[str, Any]) -> str:
    return str(entry.get("type", "")).strip().lower()


def _radon_block_complexity(entry: dict[str, Any]) -> int:
    try:
        return int(entry.get("complexity", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _is_reasonable_radon_complexity(cc: int) -> bool:
    return 0 < cc <= MAX_REASONABLE_RADON_CC


def _radon_module_line_count(project_dir: Path, normalized_path: str) -> int:
    candidate = Path(normalized_path)
    if not candidate.is_absolute():
        candidate = project_dir / candidate
    try:
        return len(candidate.read_text(encoding="utf-8", errors="ignore").splitlines())
    except OSError:
        return 0


def _alert_signature(alert: dict[str, Any]) -> tuple[str, str, int, int]:
    return (
        str(alert.get("type", "")),
        str(alert.get("name", "")),
        int(alert.get("value", 0) or 0),
        int(alert.get("limit", 0) or 0),
    )


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

    # Always exclude virtual-env and build directories to avoid scanning
    # third-party code that inflates CC values.
    # radon uses --ignore for directory names and --exclude for file globs.
    _default_ignore_dirs = [
        "venv", ".venv", ".tox", "node_modules",
        "build", "dist", ".git", "__pycache__",
    ]
    cmd.extend(["-i", ",".join(_default_ignore_dirs)])

    if excludes:
        for pattern in excludes:
            cmd.extend(["--exclude", pattern])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=RADON_TIMEOUT_SECONDS,
            check=False,
        )
        if result.returncode != 0 and not result.stdout:
            logger.warning("radon cc failed: %s", result.stderr[:200])
            return {}

        # radon zwraca JSON dict: {filepath: [{name, lineno, col_offset, complexity, rank}, ...]}
        return json.loads(result.stdout) if result.stdout else {}
    except subprocess.TimeoutExpired:
        logger.warning("radon cc timeout after %ss", RADON_TIMEOUT_SECONDS)
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
        for entry in _flatten_radon_blocks(entries):
            cc = _radon_block_complexity(entry)
            if not _is_reasonable_radon_complexity(cc):
                continue
            max_cc = max(max_cc, cc)

        if max_cc > 0:
            existing = max_cc_by_file.get(normalized_path, 0)
            max_cc_by_file[normalized_path] = max(existing, max_cc)

    return max_cc_by_file


def enhance_metrics_with_radon(
    metrics: list[Any] | AnalysisResult,
    project_dir: Path,
) -> None:
    """
    Uzupełnij metryki o dokładne CC z radon (jeśli dostępne).

    Args:
        metrics: Lista obiektów CodeMetrics albo AnalysisResult (modyfikowane w miejscu)
        project_dir: Ścieżka do projektu
    """
    result = metrics if isinstance(metrics, AnalysisResult) else None
    metric_list = result.metrics if result is not None else metrics

    radon_results = run_radon_cc(project_dir)
    if not radon_results:
        return

    max_cc_by_file = extract_max_cc_per_file(radon_results, project_dir)
    existing_function_metrics, existing_module_metrics = _collect_existing_metrics(metric_list)
    existing_alerts = _collect_existing_alerts(result)
    allowed_paths = _get_allowed_paths(existing_module_metrics, existing_function_metrics)

    updated, added, alert_count = _process_radon_results(
        radon_results, project_dir, metric_list, max_cc_by_file, existing_function_metrics, 
        existing_module_metrics, allowed_paths, result, existing_alerts
    )

    _update_result_stats(result, metric_list, updated, added, alert_count)


def _collect_existing_metrics(metric_list: list[Any]) -> tuple[dict[tuple[str, str], CodeMetrics], dict[str, CodeMetrics]]:
    existing_function_metrics: dict[tuple[str, str], CodeMetrics] = {}
    existing_module_metrics: dict[str, CodeMetrics] = {}

    for metric in metric_list:
        if not isinstance(metric, CodeMetrics):
            continue
        if metric.function_name:
            existing_function_metrics[(metric.file_path, metric.function_name)] = metric
        else:
            existing_module_metrics[metric.file_path] = metric

    return existing_function_metrics, existing_module_metrics

def _collect_existing_alerts(result: AnalysisResult | None) -> set[tuple[str, str, int, int]]:
    existing_alerts: set[tuple[str, str, int, int]] = set()
    if result is not None:
        for alert in result.alerts:
            existing_alerts.add(_alert_signature(alert))
    return existing_alerts

def _get_allowed_paths(existing_module_metrics: dict[str, CodeMetrics], existing_function_metrics: dict[tuple[str, str], CodeMetrics]) -> set[str]:
    allowed_paths = set(existing_module_metrics)
    allowed_paths.update(path for path, _ in existing_function_metrics)
    return allowed_paths

def _process_radon_results(
    radon_results: dict[str, Any], project_dir: Path, metric_list: list[Any], max_cc_by_file: dict[str, int],
    existing_function_metrics: dict[tuple[str, str], CodeMetrics], existing_module_metrics: dict[str, CodeMetrics],
    allowed_paths: set[str], result: AnalysisResult | None, existing_alerts: set[tuple[str, str, int, int]]
) -> tuple[int, int, int]:
    updated = 0
    added = 0
    alert_count = 0

    for path_key, entries in radon_results.items():
        if not isinstance(entries, list):
            continue

        normalized_path = _normalize_radon_path(path_key, project_dir)

        if allowed_paths and normalized_path not in allowed_paths:
            continue

        module_lines = _radon_module_line_count(project_dir, normalized_path)
        module_cc = max_cc_by_file.get(normalized_path, 0)
        direct_blocks = [entry for entry in entries if isinstance(entry, dict)]
        all_blocks = _flatten_radon_blocks(entries)
        function_count, class_count = _count_blocks(direct_blocks)
        is_init_file = normalized_path.endswith("__init__.py")

        updated, added, alert_count = _update_function_metrics(
            all_blocks, normalized_path, module_lines, module_cc, is_init_file, 
            existing_function_metrics, metric_list, result, existing_alerts, 
            updated, added, alert_count
        )

        updated = _update_module_metrics(normalized_path, module_lines, module_cc, function_count, class_count, existing_module_metrics, updated)

    return updated, added, alert_count

def _count_blocks(direct_blocks: list[dict[str, Any]]) -> tuple[int, int]:
    function_count = 0
    class_count = 0

    for entry in direct_blocks:
        if "class" in _radon_block_type(entry):
            class_count += 1
        else:
            function_count += 1

    return function_count, class_count

def _process_block_alert(
    name: str, cc: int, result: AnalysisResult | None,
    existing_alerts: set[tuple[str, str, int, int]], alert_count: int
) -> int:
    """Append a cc_exceeded alert if warranted and not already present; return updated alert_count."""
    if result is None or cc <= 10:
        return alert_count
    alert = {
        "type": "cc_exceeded",
        "name": name,
        "severity": 3 if cc > 20 else 2,
        "value": cc,
        "limit": 10,
    }
    signature = _alert_signature(alert)
    if signature not in existing_alerts:
        result.alerts.append(alert)
        existing_alerts.add(signature)
        alert_count += 1
    return alert_count


def _update_function_metrics(
    all_blocks: list[dict[str, Any]], normalized_path: str, module_lines: int, module_cc: int, is_init_file: bool,
    existing_function_metrics: dict[tuple[str, str], CodeMetrics], metric_list: list[Any], result: AnalysisResult | None, 
    existing_alerts: set[tuple[str, str, int, int]], updated: int, added: int, alert_count: int
) -> tuple[int, int, int]:
    for entry in all_blocks:
        name = _radon_block_name(entry)
        if not name:
            continue

        cc = _radon_block_complexity(entry)
        if not _is_reasonable_radon_complexity(cc):
            continue
        if cc > module_cc:
            module_cc = cc

        if "class" in _radon_block_type(entry):
            continue

        metric_key = (normalized_path, name)
        metric = existing_function_metrics.get(metric_key)
        if metric is None:
            if cc <= 10:
                continue
            metric = CodeMetrics(
                file_path=normalized_path,
                function_name=name,
                module_lines=module_lines,
                cyclomatic_complexity=cc,
                is_public_api=is_init_file or not name.startswith("_"),
            )
            metric_list.append(metric)
            existing_function_metrics[metric_key] = metric
            added += 1
        elif cc > metric.cyclomatic_complexity:
            metric.cyclomatic_complexity = cc
            updated += 1

        alert_count = _process_block_alert(name, cc, result, existing_alerts, alert_count)

    return updated, added, alert_count

def _update_module_metrics(
    normalized_path: str, module_lines: int, module_cc: int, function_count: int, class_count: int,
    existing_module_metrics: dict[str, CodeMetrics], updated: int
) -> int:
    module_metric = existing_module_metrics.get(normalized_path)
    if module_metric is None:
        return updated

    module_metric.module_lines = max(module_metric.module_lines, module_lines)
    module_metric.function_count = max(module_metric.function_count, function_count)
    module_metric.class_count = max(module_metric.class_count, class_count)
    if module_cc > module_metric.cyclomatic_complexity:
        module_metric.cyclomatic_complexity = module_cc
        updated += 1

    return updated

def _recompute_file_stats(result: AnalysisResult, metric_list: list[Any]) -> None:
    """Recompute total_files, total_lines, critical_count on *result*."""
    result.total_files = len({m.file_path for m in metric_list if not m.function_name})
    result.total_lines = sum(m.module_lines for m in metric_list if not m.function_name)
    result.critical_count = sum(1 for a in result.alerts if a.get("severity", 0) >= 2)


def _recompute_cc_avg(metric_list: list[Any]) -> float:
    """Return average CC across all metrics with CC > 0, or 0.0."""
    cc_vals = [m.cyclomatic_complexity for m in metric_list if m.cyclomatic_complexity > 0]
    return round(sum(cc_vals) / len(cc_vals), 2) if cc_vals else 0.0


def _update_result_stats(result: AnalysisResult | None, metric_list: list[Any], updated: int, added: int, alert_count: int) -> None:
    if result is not None:
        _recompute_file_stats(result, metric_list)
        result.avg_cc = _recompute_cc_avg(metric_list)

    if updated or added or alert_count:
        logger.info(
            "Enhanced %d metrics, added %d metrics and %d alerts with radon CC data",
            updated,
            added,
            alert_count,
        )
