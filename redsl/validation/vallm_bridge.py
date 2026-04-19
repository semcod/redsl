"""
vallm bridge — wielowarstwowa walidacja wygenerowanych patchy.

Zastępuje/wzmacnia punkt 1.4 (test runner validation) i 2.3 (confidence tuning):
- Walidacja składni, importów, złożoności, bezpieczeństwa (bandit), semantyki (CodeBERT)
- Scoring 0-100 → verdict: pass / warn / fail
- Score jako wejście do confidence trackera

Używa vallm CLI: vallm validate <plik> --format json

Typowy flow:
    result = validate_patch(Path("foo.py"), refactored_code)
    if not result["valid"]:
        reject_proposal()
    proposal.confidence = blend_with_vallm_score(proposal.confidence, result["score"])
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from redsl.bridges.base import CliBridge
from redsl.utils.json_helpers import extract_json_block as _extract_json

if TYPE_CHECKING:
    from redsl.refactors.models import RefactorProposal

logger = logging.getLogger(__name__)

_VALLM_SCORE_THRESHOLD = 0.4   # vallm score is 0.0–1.0


# _extract_json is imported from redsl.utils.json_helpers


def _validation_target_path(
    validation_root: Path,
    file_path: Path,
    project_dir: Path | None = None,
) -> Path:
    """Map a target file into the temporary validation workspace."""
    if file_path.is_absolute() and project_dir is not None:
        try:
            relative_path = file_path.relative_to(project_dir)
        except ValueError:
            relative_path = Path(file_path.name)
    else:
        relative_path = file_path if not file_path.is_absolute() else Path(file_path.name)
    return validation_root / relative_path


def _stage_validation_context(
    validation_root: Path,
    file_path: Path,
    refactored_code: str,
    project_dir: Path | None = None,
    copied_dirs: set[Path] | None = None,
) -> Path:
    """Stage a file into the validation workspace, optionally copying sibling modules."""
    staged_path = _validation_target_path(validation_root, file_path, project_dir=project_dir)
    staged_path.parent.mkdir(parents=True, exist_ok=True)

    if project_dir is not None:
        source_path = file_path if file_path.is_absolute() else project_dir / file_path
        source_dir = source_path.parent
        if file_path.is_absolute():
            try:
                rel_parent = file_path.relative_to(project_dir).parent
            except ValueError:
                rel_parent = Path(".")
        else:
            rel_parent = file_path.parent

        if source_dir.exists() and rel_parent != Path("."):
            if copied_dirs is None or rel_parent not in copied_dirs:
                shutil.copytree(source_dir, staged_path.parent, dirs_exist_ok=True)
                if copied_dirs is not None:
                    copied_dirs.add(rel_parent)

    staged_path.write_text(refactored_code, encoding="utf-8")
    return staged_path


def _run_vallm_validation(file_path: Path) -> dict:
    """Run vallm on a staged file and normalize its JSON output."""
    proc = subprocess.run(
        ["vallm", "validate", "--file", str(file_path), "--output", "json"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    # vallm may print non-JSON preamble lines (e.g. "Detected language: python")
    raw = _extract_json(proc.stdout)
    if not raw:
        logger.warning("vallm returned no JSON for %s", file_path.name)
        return {
            "valid": proc.returncode == 0,
            "score": 0.0,
            "verdict": "unknown",
            "issues": [],
            "available": True,
        }

    data = json.loads(raw)
    verdict = data.get("verdict", "unknown")
    # vallm score is 0.0–1.0
    score = float(data.get("score", 0.0))
    issues = data.get("issues", [])

    valid = verdict != "fail" and score >= _VALLM_SCORE_THRESHOLD
    if not valid:
        logger.warning(
            "vallm validation failed for %s: verdict=%s score=%.0f issues=%d",
            file_path.name, verdict, score, len(issues),
        )

    return {
        "valid": valid,
        "score": score,
        "verdict": verdict,
        "issues": issues,
        "available": True,
    }


class _VallmBridge(CliBridge):
    cli_name = "vallm"
    check_args = ["--help"]


def is_available() -> bool:
    """Sprawdź czy vallm jest zainstalowane i w pełni działa (nie tylko czy jest w PATH)."""
    return _VallmBridge.is_available()


def validate_patch(
    file_path: str | Path,
    refactored_code: str,
    project_dir: Path | None = None,
) -> dict:
    """
    Waliduj wygenerowany kod przez pipeline vallm.

    Zapisuje kod do tymczasowego workspace, uruchamia vallm validate,
    usuwa pliki i zwraca wynik.

    Args:
        file_path:       Oryginalna ścieżka pliku (do nadania tymczasowemu plikowi
                         właściwego rozszerzenia i nazwy w raportach).
        refactored_code: Wygenerowany kod do walidacji.
        project_dir:     Opcjonalny katalog projektu do skopiowania kontekstu
                         plików sąsiednich i modułów pakietowych.

    Returns:
        Słownik z polami:
            valid (bool)   — czy vallm nie zwrócił verdict "fail"
            score (float)  — wynik 0-100 (0 jeśli vallm niedostępne)
            verdict (str)  — "pass" | "warn" | "fail" | "unknown"
            issues (list)  — lista wykrytych problemów
            available (bool) — czy vallm był dostępny
    """
    if not is_available():
        return {
            "valid": True,
            "score": 0.0,
            "verdict": "unknown",
            "issues": [],
            "available": False,
        }

    file_path = Path(file_path)

    validation_root = Path(tempfile.mkdtemp(prefix="redsl_vallm_"))
    try:
        tmp_path = _stage_validation_context(
            validation_root,
            file_path,
            refactored_code,
            project_dir=project_dir,
        )

        return _run_vallm_validation(tmp_path)

    except subprocess.TimeoutExpired:
        logger.warning("vallm timed out for %s", file_path.name)
        return {"valid": True, "score": 0.0, "verdict": "timeout", "issues": [], "available": True}
    except json.JSONDecodeError as exc:
        logger.warning("vallm returned invalid JSON: %s", exc)
        return {"valid": True, "score": 0.0, "verdict": "parse_error", "issues": [], "available": True}
    except Exception as exc:
        logger.warning("vallm error: %s", exc)
        return {"valid": True, "score": 0.0, "verdict": "error", "issues": [], "available": True}
    finally:
        shutil.rmtree(validation_root, ignore_errors=True)


def validate_proposal(proposal: "RefactorProposal", project_dir: Path | None = None) -> dict:
    """
    Waliduj wszystkie zmiany w propozycji refaktoryzacji.

    Args:
        proposal: Propozycja z listą FileChange.
        project_dir: Opcjonalny katalog projektu do stagingu całego proposal
            w jednym temp workspace, tak aby `vallm` widział nowe siblingi
            i importy względne.

    Returns:
        Słownik z polami:
            all_valid (bool)    — czy wszystkie pliki przeszły walidację
            scores (list[float]) — wyniki per plik
            avg_score (float)   — średni wynik vallm
            failures (list)     — pliki z verdict "fail"
            available (bool)    — czy vallm był dostępny
    """
    if not is_available():
        return {
            "all_valid": True,
            "scores": [],
            "avg_score": 0.0,
            "failures": [],
            "available": False,
        }

    if project_dir is not None:
        validation_root = Path(tempfile.mkdtemp(prefix="redsl_vallm_proposal_"))
        copied_dirs: set[Path] = set()
        staged_paths: list[tuple[str, Path]] = []
        try:
            for change in proposal.changes:
                file_path = Path(change.file_path)
                staged_path = _stage_validation_context(
                    validation_root,
                    file_path,
                    change.refactored_code,
                    project_dir=project_dir,
                    copied_dirs=copied_dirs,
                )
                staged_paths.append((change.file_path, staged_path))

            scores: list[float] = []
            failures: list[str] = []

            for original_path, staged_path in staged_paths:
                result = _run_vallm_validation(staged_path)
                scores.append(result["score"])
                if not result["valid"]:
                    failures.append(original_path)

            avg_score = sum(scores) / len(scores) if scores else 0.0

            return {
                "all_valid": len(failures) == 0,
                "scores": scores,
                "avg_score": avg_score,
                "failures": failures,
                "available": True,
            }
        finally:
            shutil.rmtree(validation_root, ignore_errors=True)

    scores: list[float] = []
    failures: list[str] = []

    for change in proposal.changes:
        result = validate_patch(change.file_path, change.refactored_code, project_dir=project_dir)
        scores.append(result["score"])
        if not result["valid"]:
            failures.append(change.file_path)

    avg_score = sum(scores) / len(scores) if scores else 0.0

    return {
        "all_valid": len(failures) == 0,
        "scores": scores,
        "avg_score": avg_score,
        "failures": failures,
        "available": True,
    }


def blend_confidence(base_confidence: float, vallm_score: float) -> float:
    """
    Połącz confidence z metryk ReDSL z wynikiem vallm (punkt 2.3).

    vallm score jest w skali 0.0–1.0 → weighted blend z base_confidence.

    Args:
        base_confidence: Confidence z RefactorEngine.estimate_confidence() [0-1].
        vallm_score:     Wynik vallm [0.0-1.0].

    Returns:
        Nowy confidence [0-1].
    """
    if vallm_score <= 0:
        return base_confidence

    vallm_normalized = min(1.0, max(0.0, vallm_score))
    blended = 0.6 * base_confidence + 0.4 * vallm_normalized
    return round(blended, 3)
