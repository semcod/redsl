"""
Mostek do redup — wykrywanie duplikatów kodu (Tier 2).

Rola w ReDSL:
- Zastępuje parsowanie duplication_toon.yaml (analiza duplikatów)
- Dostarcza cross-modułowe dane o duplikatach do DSL Engine
- Output w formacie JSON lub toon.yaml, który ReDSL już parsuje

Użycie:
    from redsl.analyzers import redup_bridge

    groups = redup_bridge.scan_duplicates(project_dir)
    for g in groups:
        print(g["similarity"], g["files"])
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from redsl.bridges.base import CliBridge
from redsl.utils.json_helpers import extract_json_block as _extract_json

if TYPE_CHECKING:
    from redsl.analyzers.metrics import AnalysisResult

logger = logging.getLogger(__name__)


class _RedupBridge(CliBridge):
    cli_name = "redup"
    check_args = ["--version"]


def is_available() -> bool:
    """Sprawdź czy redup jest zainstalowane i dostępne w PATH."""
    return _RedupBridge.is_available()


def scan_duplicates(
    project_dir: Path,
    min_lines: int = 3,
    min_similarity: float = 0.85,
) -> list[dict]:
    """
    Uruchom redup i zwróć listę grup duplikatów.

    Args:
        project_dir:    Katalog projektu do przeskanowania.
        min_lines:      Minimalna liczba linii bloku.
        min_similarity: Minimalny próg podobieństwa (0.0-1.0).

    Returns:
        Lista grup duplikatów w formacie:
        [{"similarity": 0.95, "files": [...], "saved_lines": 10, ...}]
        Zwraca [] jeśli redup nie jest dostępny lub nie znaleziono duplikatów.
    """
    if not is_available():
        logger.debug("redup not available — skipping duplicate scan")
        return []

    try:
        proc = subprocess.run(
            [
                "redup", "scan", str(project_dir),
                "--format", "json",
                "--min-lines", str(min_lines),
                "--min-sim", str(min_similarity),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if proc.returncode != 0:
            logger.warning("redup scan failed (exit %d): %s", proc.returncode, proc.stderr[:200])
            return []

        raw = _extract_json(proc.stdout)
        if not raw:
            logger.warning("redup returned no JSON output")
            return []

        data = json.loads(raw)
        groups = data.get("groups", [])

        logger.info(
            "redup: %d duplicate groups found in %s (%d files, %d lines recoverable)",
            len(groups),
            project_dir.name,
            data.get("stats", {}).get("files_scanned", 0),
            data.get("summary", {}).get("total_saved_lines", 0),
        )
        return groups

    except subprocess.TimeoutExpired:
        logger.warning("redup scan timed out for %s", project_dir)
        return []
    except Exception as exc:
        logger.warning("redup scan error: %s", exc)
        return []


def scan_as_toon(
    project_dir: Path,
    min_lines: int = 3,
    min_similarity: float = 0.85,
) -> str:
    """
    Uruchom redup w formacie toon i zwróć zawartość jako string.

    Zwrócony string można przekazać bezpośrednio do:
        ToonAnalyzer.analyze_from_toon_content(duplication_toon=...)

    Returns:
        Zawartość duplication_toon.yaml jako string, lub "" jeśli błąd.
    """
    if not is_available():
        logger.debug("redup not available — returning empty toon")
        return ""

    try:
        proc = subprocess.run(
            [
                "redup", "scan", str(project_dir),
                "--format", "toon",
                "--min-lines", str(min_lines),
                "--min-sim", str(min_similarity),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if proc.returncode != 0:
            logger.warning("redup scan (toon) failed (exit %d)", proc.returncode)
            return ""

        toon_content = _strip_progress_output(proc.stdout)
        logger.info("redup: toon output generated (%d bytes)", len(toon_content))
        return toon_content

    except subprocess.TimeoutExpired:
        logger.warning("redup toon scan timed out for %s", project_dir)
        return ""
    except Exception as exc:
        logger.warning("redup toon scan error: %s", exc)
        return ""


def _build_dup_index(groups: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build a filename → {similarity, lines} index from duplicate groups."""
    file_to_dup: dict[str, dict[str, Any]] = {}
    for group in groups:
        similarity = float(group.get("similarity_score") or group.get("similarity") or 0)
        lines = int(group.get("total_lines", 0))
        for fragment in group.get("fragments", []):
            raw_path = fragment.get("file", "")
            frag_lines = int(fragment.get("lines") or fragment.get("total_lines") or lines)
            key = Path(raw_path).name
            if key not in file_to_dup or file_to_dup[key]["similarity"] < similarity:
                file_to_dup[key] = {"similarity": similarity, "lines": frag_lines}
    return file_to_dup


def enrich_analysis(
    analysis: AnalysisResult,
    project_dir: Path,
) -> AnalysisResult:
    """
    Wzbogać istniejący AnalysisResult o dane z redup.

    Dodaje `duplicates` i aktualizuje `duplicate_lines` / `duplicate_similarity`
    w odpowiednich CodeMetrics.

    Args:
        analysis:    Istniejący wynik analizy (z CodeAnalyzer lub code2llm_bridge).
        project_dir: Katalog projektu.

    Returns:
        Zaktualizowany analysis (in-place + return).
    """
    groups = scan_duplicates(project_dir)
    if not groups:
        return analysis

    analysis.duplicates = groups
    file_to_dup = _build_dup_index(groups)

    for metric in analysis.metrics:
        key = Path(metric.file_path).name
        if key in file_to_dup:
            metric.duplicate_lines = file_to_dup[key]["lines"]
            metric.duplicate_similarity = file_to_dup[key]["similarity"]

    return analysis


def get_refactor_suggestions(project_dir: Path) -> list[dict]:
    """
    Pobierz sugestie refaktoryzacji duplikatów z redup.

    Returns:
        Lista sugestii z polami: action, files, priority, saved_lines.
    """
    if not is_available():
        return []

    try:
        proc = subprocess.run(
            ["redup", "scan", str(project_dir), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode != 0:
            return []

        raw = _extract_json(proc.stdout)
        if not raw:
            return []

        data = json.loads(raw)
        return data.get("refactor_suggestions", [])

    except Exception as exc:
        logger.warning("redup suggestions error: %s", exc)
        return []


# _extract_json is imported from redsl.utils.json_helpers


def _strip_progress_output(text: str) -> str:
    """Usuń linie postępu (emoji-prefixed) z outputu redup, zwróć czysty toon."""
    skip_prefixes = ("🔍", "📁", "📏", "🎯", "📊", "Found", "Duplicate")
    lines = text.splitlines(keepends=True)
    return "".join(
        line for line in lines
        if not any(line.lstrip().startswith(p) for p in skip_prefixes)
    )
