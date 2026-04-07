"""
code2llm bridge — deleguje percepcję projektu do code2llm.

code2llm generuje pliki toon.yaml, które ToonAnalyzer już parsuje.
Zastępuje wewnętrzny PythonAnalyzer gdy code2llm jest dostępne.

Punkt 2.1 i 2.4 z planu ewolucji:
- Call graph / pipeline_detector (AST-aware context)
- Incremental analysis + evolutionary cache
- Multi-language support (Python, Go, Rust, Java, TS)
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redsl.analyzers.analyzer import CodeAnalyzer
    from redsl.analyzers.metrics import AnalysisResult

logger = logging.getLogger(__name__)

_TOON_CANDIDATES: list[tuple[str, str]] = [
    # code2llm -f toon generates these filenames
    ("analysis.toon.yaml", "project_toon"),   # primary output of code2llm
    ("project.toon.yaml", "project_toon"),
    ("project_toon.yaml", "project_toon"),
    ("analysis_toon.yaml", "project_toon"),
    ("duplication.toon.yaml", "duplication_toon"),
    ("duplication_toon.yaml", "duplication_toon"),
    ("validation.toon.yaml", "validation_toon"),
    ("validation_toon.yaml", "validation_toon"),
]


def is_available() -> bool:
    """Sprawdź czy code2llm jest zainstalowane i dostępne w PATH."""
    return shutil.which("code2llm") is not None


def generate_toon_files(
    project_dir: Path,
    output_dir: Path | None = None,
    timeout: int = 120,
) -> Path:
    """
    Uruchom code2llm na projekcie i zwróć katalog z wygenerowanymi plikami toon.

    Args:
        project_dir: Katalog projektu do analizy.
        output_dir:  Gdzie zapisać toon files (domyślnie project_dir / "project").
        timeout:     Timeout w sekundach (domyślnie 120s — OK dla 8k LOC).

    Returns:
        Ścieżka do katalogu z wygenerowanymi plikami toon.

    Raises:
        RuntimeError: jeśli code2llm nie jest dostępne lub zakończyło się błędem.
    """
    if not is_available():
        raise RuntimeError(
            "code2llm nie jest zainstalowane. "
            "Instalacja: pip install code2llm  lub  uv add code2llm"
        )

    if output_dir is None:
        output_dir = project_dir / "project"

    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = ["code2llm", str(project_dir), "-f", "toon", "-o", str(output_dir)]
    logger.info("Running: %s", " ".join(cmd))

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if proc.returncode != 0:
        logger.error("code2llm stderr: %s", proc.stderr[:500])
        raise RuntimeError(
            f"code2llm failed (exit {proc.returncode}): {proc.stderr[:200]}"
        )

    if proc.stdout:
        logger.debug("code2llm stdout: %s", proc.stdout[:300])

    return output_dir


def read_toon_contents(toon_dir: Path) -> dict[str, str]:
    """
    Wczytaj pliki toon z katalogu wyjściowego code2llm.

    Returns:
        Słownik {klucz: zawartość} dla znalezionych plików.
        Klucze: "project_toon", "duplication_toon", "validation_toon"
    """
    contents: dict[str, str] = {}

    for filename, key in _TOON_CANDIDATES:
        candidate = toon_dir / filename
        if candidate.exists() and key not in contents:
            contents[key] = candidate.read_text(encoding="utf-8")
            logger.debug("Loaded %s from %s", key, candidate.name)

    if not contents:
        logger.warning("No toon files found in %s", toon_dir)

    return contents


def analyze_with_code2llm(
    project_dir: Path,
    analyzer: "CodeAnalyzer",
    output_dir: Path | None = None,
    timeout: int = 120,
) -> "AnalysisResult":
    """
    Pełna ścieżka percepcji z code2llm:
    1. Uruchom code2llm → generuj toon files
    2. Wczytaj wygenerowane pliki
    3. Wywołaj analyzer.analyze_from_toon_content()

    Raises:
        RuntimeError: jeśli code2llm nie jest dostępne lub niepowodzenie.
    """
    toon_dir = generate_toon_files(project_dir, output_dir=output_dir, timeout=timeout)
    contents = read_toon_contents(toon_dir)

    if not contents:
        logger.warning(
            "code2llm generated no toon files in %s — falling back to PythonAnalyzer",
            toon_dir,
        )
        return analyzer.analyze_project(project_dir)

    result = analyzer.analyze_from_toon_content(
        project_toon=contents.get("project_toon", ""),
        duplication_toon=contents.get("duplication_toon", ""),
        validation_toon=contents.get("validation_toon", ""),
    )

    logger.info(
        "code2llm analysis: %d files, %d lines, avg CC=%.1f, %d critical",
        result.total_files,
        result.total_lines,
        result.avg_cc,
        result.critical_count,
    )
    return result


def maybe_analyze(
    project_dir: Path,
    analyzer: "CodeAnalyzer",
    output_dir: Path | None = None,
) -> "AnalysisResult | None":
    """
    Spróbuj analizy przez code2llm; zwróć None jeśli niezainstalowane.

    Używane przez orkiestrator jako opt-in — jeśli zwraca None, fallback do PythonAnalyzer.
    """
    if not is_available():
        logger.debug("code2llm not found — skipping bridge")
        return None

    try:
        return analyze_with_code2llm(project_dir, analyzer, output_dir)
    except Exception as exc:
        logger.warning("code2llm bridge failed: %s — falling back to PythonAnalyzer", exc)
        return None
