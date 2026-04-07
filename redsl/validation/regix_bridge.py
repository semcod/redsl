"""
regix bridge — wykrywanie regresji metryk po cyklu refaktoryzacji.

Zastępuje punkt 3.5 z planu ewolucji (regression detection) w całości:
- MetricsSnapshot
- compare_snapshots
- enforce_no_regression

Używa regix CLI (regix snapshot / regix compare / regix gates).
Opcjonalnie: Python API via `from regix import Regix` jeśli dostępne.

Typowy flow w orkiestratorze:
    before = regix_bridge.snapshot(project_dir)         # przed zmianami
    ... ReDSL aplikuje zmiany ...
    passed = regix_bridge.validate_after(project_dir, before, rollback=True)
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path

_DEFAULT_TIMEOUT = int(os.environ.get("REDSL_REGIX_TIMEOUT", "300"))

logger = logging.getLogger(__name__)


def is_available() -> bool:
    """
    Sprawdź czy regix jest zainstalowane i działa poprawnie.

    Używa `regix --version` zamiast tylko shutil.which() — narzędzie może
    istnieć w PATH ale crashować przy uruchomieniu (np. import error).
    """
    if shutil.which("regix") is None:
        return False
    try:
        proc = subprocess.run(
            ["regix", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return proc.returncode == 0
    except Exception:
        return False


def snapshot(project_dir: Path, ref: str | None = None, timeout: int | None = None) -> dict | None:
    """
    Zrób snapshot metryk projektu przez regix.

    Args:
        project_dir: Katalog projektu.
        ref:         Git ref (np. "HEAD", "HEAD~1"). None = working tree.
        timeout:     Limit czasu w sekundach (domyślnie $REDSL_REGIX_TIMEOUT lub 300).
                     Duże projekty z code2llm jako backendem wymagają 2-5 minut.

    Returns:
        Słownik z danymi snapshotu lub None jeśli regix niedostępne / błąd.
    """
    if not is_available():
        return None

    cmd = ["regix", "snapshot"]
    if ref:
        cmd.append(ref)
    cmd += ["--format", "json"]

    try:
        proc = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=timeout if timeout is not None else _DEFAULT_TIMEOUT,
        )
        if proc.returncode != 0:
            logger.warning("regix snapshot failed: %s", proc.stderr[:200])
            return None

        return json.loads(proc.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as exc:
        logger.warning("regix snapshot error: %s", exc)
        return None


def compare(
    project_dir: Path,
    before_ref: str = "HEAD~1",
    after_ref: str = "HEAD",
) -> dict | None:
    """
    Porównaj metryki między dwoma git refs przez regix.

    Args:
        project_dir: Katalog projektu.
        before_ref:  Ref "przed" (domyślnie HEAD~1).
        after_ref:   Ref "po" (domyślnie HEAD — aktualny commit).

    Returns:
        Słownik z raportem porównania lub None jeśli błąd.
    """
    if not is_available():
        return None

    cmd = ["regix", "compare", before_ref, after_ref, "--format", "json"]

    try:
        proc = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=_DEFAULT_TIMEOUT,
        )
        if proc.returncode != 0:
            logger.warning("regix compare failed: %s", proc.stderr[:200])
            return None

        return json.loads(proc.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as exc:
        logger.warning("regix compare error: %s", exc)
        return None


def compare_snapshots(
    project_dir: Path,
    before: dict,
    after: dict | None = None,
) -> dict | None:
    """
    Porównaj dwa snapshoty (obiekty z `snapshot()`).

    Jeśli after=None, porównuje before ze stanem working tree.

    Returns:
        Raport z polami: has_regressions, regressions, improvements, summary
        lub None jeśli regix niedostępne.
    """
    if not is_available():
        return None

    cmd = ["regix", "diff", "--format", "json"]
    input_data = json.dumps({"before": before, "after": after})

    try:
        proc = subprocess.run(
            cmd,
            cwd=project_dir,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=_DEFAULT_TIMEOUT,
        )
        if proc.returncode != 0:
            logger.warning("regix diff failed: %s", proc.stderr[:200])
            return None

        return json.loads(proc.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as exc:
        logger.warning("regix diff error: %s", exc)
        return None


def check_gates(project_dir: Path) -> dict | None:
    """
    Sprawdź quality gates z regix.yaml (lub domyślne progi).

    Returns:
        Słownik z polami: passed, failures, warnings
        lub None jeśli regix niedostępne / brak konfiguracji.
    """
    if not is_available():
        return None

    cmd = ["regix", "gates", "--format", "json"]

    try:
        proc = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        data = json.loads(proc.stdout) if proc.stdout.strip() else {}
        passed = proc.returncode == 0

        return {
            "passed": data.get("passed", passed),
            "failures": data.get("failures", []),
            "warnings": data.get("warnings", []),
            "raw": data,
        }
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as exc:
        logger.warning("regix gates error: %s", exc)
        return None


def rollback_working_tree(project_dir: Path) -> bool:
    """
    Cofnij niezatwierdzone zmiany w working tree przez `git checkout -- .`.

    Returns:
        True jeśli rollback się powiódł.
    """
    try:
        proc = subprocess.run(
            ["git", "checkout", "--", "."],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode == 0:
            logger.info("Rolled back working tree changes in %s", project_dir)
            return True
        logger.warning("git rollback failed: %s", proc.stderr[:200])
        return False
    except Exception as exc:
        logger.warning("Rollback error: %s", exc)
        return False


def validate_no_regression(
    project_dir: Path,
    rollback_on_failure: bool = False,
) -> tuple[bool, dict]:
    """
    Porównaj HEAD~1 → HEAD i sprawdź czy nie ma regresji metryk.

    Typowe użycie PO zacommitowaniu zmian przez ReDSL.
    Dla walidacji working tree (przed commitem) użyj validate_working_tree().

    Args:
        project_dir:        Katalog projektu (musi mieć git).
        rollback_on_failure: Jeśli True i wykryto regresję — cofnij commit (git reset HEAD~1).

    Returns:
        (passed: bool, report: dict)
    """
    if not is_available():
        logger.debug("regix not available — skipping regression check")
        return True, {}

    report = compare(project_dir, before_ref="HEAD~1", after_ref="HEAD") or {}
    regressions_list = report.get("regressions", [])
    errors_count = report.get("errors", 0)
    has_regressions = bool(regressions_list) or errors_count > 0

    if has_regressions:
        logger.warning(
            "Regression detected after refactoring: %s",
            report.get("regressions", []),
        )
        if rollback_on_failure:
            subprocess.run(
                ["git", "reset", "HEAD~1", "--mixed"],
                cwd=project_dir,
                check=False,
            )
            logger.info("Rolled back last commit due to regression")

    return not has_regressions, report


def validate_working_tree(
    project_dir: Path,
    before_snapshot: dict | None = None,
    rollback_on_failure: bool = False,
) -> tuple[bool, dict]:
    """
    Porównaj snapshot 'przed' ze stanem working tree (po zmianach, przed commitem).

    Używany w run_cycle() do walidacji przed aplikacją na dysk.

    Args:
        project_dir:        Katalog projektu.
        before_snapshot:    Snapshot z `snapshot(ref="HEAD")` zrobiony przed zmianami.
        rollback_on_failure: Jeśli True i regresja — cofnij zmiany working tree.

    Returns:
        (passed: bool, report: dict)
    """
    if not is_available():
        logger.debug("regix not available — skipping working tree validation")
        return True, {}

    if before_snapshot is None:
        before_snapshot = snapshot(project_dir, ref="HEAD") or {}

    after_snapshot = snapshot(project_dir) or {}
    report = compare_snapshots(project_dir, before_snapshot, after_snapshot) or {}
    regressions_list = report.get("regressions", [])
    errors_count = report.get("errors", 0)
    has_regressions = bool(regressions_list) or errors_count > 0

    if has_regressions:
        logger.warning(
            "Working tree regression detected: %s",
            report.get("regressions", []),
        )
        if rollback_on_failure:
            rollback_working_tree(project_dir)

    return not has_regressions, report
