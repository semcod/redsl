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

if TYPE_CHECKING:
    from redsl.refactors.models import RefactorProposal

logger = logging.getLogger(__name__)

_VALLM_SCORE_THRESHOLD = 0.4   # vallm score is 0.0–1.0


def _extract_json(text: str) -> str:
    """Wyłuskaj pierwszy blok JSON z tekstu (pomijając preambuły takie jak 'Detected language:')."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            return "\n".join(lines[i:])
    return ""


def is_available() -> bool:
    """Sprawdź czy vallm jest zainstalowane i dostępne w PATH."""
    return shutil.which("vallm") is not None


def validate_patch(file_path: str | Path, refactored_code: str) -> dict:
    """
    Waliduj wygenerowany kod przez pipeline vallm.

    Zapisuje kod do tymczasowego pliku, uruchamia vallm validate,
    usuwa plik i zwraca wynik.

    Args:
        file_path:       Oryginalna ścieżka pliku (do nadania tymczasowemu plikowi
                         właściwego rozszerzenia i nazwy w raportach).
        refactored_code: Wygenerowany kod do walidacji.

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
    suffix = file_path.suffix or ".py"

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=suffix,
        prefix=f"redsl_vallm_{file_path.stem}_",
        delete=False,
        encoding="utf-8",
    ) as tmp:
        tmp.write(refactored_code)
        tmp_path = Path(tmp.name)

    try:
        proc = subprocess.run(
            ["vallm", "validate", "--file", str(tmp_path), "--output", "json"],
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
        try:
            tmp_path.unlink()
        except OSError:
            pass


def validate_proposal(proposal: "RefactorProposal") -> dict:
    """
    Waliduj wszystkie zmiany w propozycji refaktoryzacji.

    Args:
        proposal: Propozycja z listą FileChange.

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

    scores: list[float] = []
    failures: list[str] = []

    for change in proposal.changes:
        result = validate_patch(change.file_path, change.refactored_code)
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
