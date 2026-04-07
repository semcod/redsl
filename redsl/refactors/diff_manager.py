"""
Diff manager — podgląd i wycofywanie zmian refaktoryzacji.

Odpowiada za:
- generate_diff     — unified diff dla dwóch wersji pliku
- preview_proposal  — sformatowany diff wszystkich zmian w propozycji
- create_checkpoint — git stash lub kopia plików → checkpoint_id
- rollback_to_checkpoint — cofnij do stanu sprzed
- rollback_single_file   — cofnij jeden plik
"""

from __future__ import annotations

import difflib
import logging
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import RefactorProposal

logger = logging.getLogger(__name__)


def generate_diff(original: str, refactored: str, file_path: str) -> str:
    """Wygeneruj unified diff dla dwóch wersji pliku.

    Args:
        original:   Oryginalny kod źródłowy
        refactored: Zrefaktoryzowany kod źródłowy
        file_path:  Ścieżka pliku (używana w nagłówku diffa)

    Returns:
        Unified diff jako string
    """
    original_lines = original.splitlines(keepends=True)
    refactored_lines = refactored.splitlines(keepends=True)

    diff = difflib.unified_diff(
        original_lines,
        refactored_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm="",
    )
    return "\n".join(diff)


def preview_proposal(proposal: "RefactorProposal", project_dir: Path | None = None) -> str:
    """Wygeneruj sformatowany diff wszystkich zmian w propozycji.

    Args:
        proposal:    Propozycja refaktoryzacji z listą zmian
        project_dir: Katalog projektu (potrzebny do odczytu oryginałów)

    Returns:
        Sformatowany string z diffami
    """
    lines = [
        f"## ReDSL Refactor Preview",
        f"Action: {proposal.action}",
        f"File:   {proposal.file_path}",
        f"Confidence: {proposal.confidence:.0%}",
        "",
    ]

    if not proposal.changes:
        lines.append("(no changes)")
        return "\n".join(lines)

    for change in proposal.changes:
        file_path = change.get("file_path", proposal.file_path)
        original = change.get("original", "")
        refactored = change.get("refactored", "")

        if not original and project_dir:
            full_path = project_dir / file_path
            if full_path.exists():
                original = full_path.read_text(encoding="utf-8", errors="ignore")

        if original and refactored:
            diff = generate_diff(original, refactored, file_path)
            if diff:
                lines.append(f"--- {file_path}")
                lines.append(diff)
            else:
                lines.append(f"(no diff for {file_path})")
        else:
            lines.append(f"(source not available for {file_path})")

    return "\n".join(lines)


def create_checkpoint(project_dir: Path) -> str:
    """Utwórz checkpoint aktualnego stanu projektu.

    Próbuje użyć git stash. Jeśli brak gita — kopiuje pliki do /tmp.

    Args:
        project_dir: Katalog projektu

    Returns:
        checkpoint_id — identyfikator checkpointa do późniejszego rollbacku
    """
    checkpoint_id = f"redsl_{int(time.time() * 1000)}"

    if _is_git_repo(project_dir):
        result = subprocess.run(
            ["git", "stash", "push", "-m", checkpoint_id],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logger.info("Git stash checkpoint created: %s", checkpoint_id)
            return f"git:{checkpoint_id}"

    # Fallback — kopia plików
    backup_dir = Path(tempfile.gettempdir()) / "redsl_checkpoints" / checkpoint_id
    backup_dir.mkdir(parents=True, exist_ok=True)

    for py_file in project_dir.rglob("*.py"):
        try:
            rel_path = py_file.relative_to(project_dir)
            dest = backup_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(py_file, dest)
        except OSError as e:
            logger.warning("Could not backup %s: %s", py_file, e)

    logger.info("File-copy checkpoint created: %s (%s)", checkpoint_id, backup_dir)
    return f"files:{checkpoint_id}"


def rollback_to_checkpoint(checkpoint_id: str, project_dir: Path) -> bool:
    """Cofnij projekt do stanu z checkpointa.

    Args:
        checkpoint_id: ID z create_checkpoint()
        project_dir:   Katalog projektu

    Returns:
        True jeśli rollback się powiódł
    """
    if checkpoint_id.startswith("git:"):
        stash_name = checkpoint_id[4:]
        return _rollback_git_stash(stash_name, project_dir)

    if checkpoint_id.startswith("files:"):
        cp_name = checkpoint_id[6:]
        return _rollback_files(cp_name, project_dir)

    logger.error("Unknown checkpoint format: %s", checkpoint_id)
    return False


def rollback_single_file(file_path: Path, checkpoint_id: str, project_dir: Path) -> bool:
    """Cofnij jeden plik do stanu z checkpointa.

    Args:
        file_path:     Ścieżka pliku do cofnięcia (względna lub bezwzględna)
        checkpoint_id: ID z create_checkpoint()
        project_dir:   Katalog projektu

    Returns:
        True jeśli rollback się powiódł
    """
    # Normalize to relative path
    try:
        rel_path = file_path.relative_to(project_dir)
    except ValueError:
        rel_path = file_path

    if checkpoint_id.startswith("git:"):
        return _git_checkout_file(rel_path, project_dir)

    if checkpoint_id.startswith("files:"):
        cp_name = checkpoint_id[6:]
        backup_dir = Path(tempfile.gettempdir()) / "redsl_checkpoints" / cp_name
        src = backup_dir / rel_path
        dst = project_dir / rel_path
        if src.exists():
            try:
                shutil.copy2(src, dst)
                logger.info("Rolled back file %s from checkpoint %s", rel_path, cp_name)
                return True
            except OSError as e:
                logger.error("Failed to rollback %s: %s", rel_path, e)
        else:
            logger.warning("File %s not found in checkpoint %s", rel_path, cp_name)

    return False


def _is_git_repo(project_dir: Path) -> bool:
    """Sprawdź czy katalog jest repozytorium git."""
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _rollback_git_stash(stash_name: str, project_dir: Path) -> bool:
    """Cofnij do git stash."""
    # Find the stash entry by name
    list_result = subprocess.run(
        ["git", "stash", "list"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    stash_ref = None
    for line in list_result.stdout.splitlines():
        if stash_name in line:
            stash_ref = line.split(":")[0].strip()
            break

    if not stash_ref:
        logger.warning("Stash '%s' not found, trying hard reset", stash_name)
        result = subprocess.run(
            ["git", "checkout", "--", "."],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    result = subprocess.run(
        ["git", "stash", "pop", stash_ref],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        logger.info("Git stash rollback to %s successful", stash_name)
        return True
    logger.error("Git stash pop failed: %s", result.stderr)
    return False


def _rollback_files(cp_name: str, project_dir: Path) -> bool:
    """Cofnij z kopii plików."""
    backup_dir = Path(tempfile.gettempdir()) / "redsl_checkpoints" / cp_name
    if not backup_dir.exists():
        logger.error("Checkpoint backup not found: %s", backup_dir)
        return False

    success = True
    for backup_file in backup_dir.rglob("*.py"):
        try:
            rel_path = backup_file.relative_to(backup_dir)
            dst = project_dir / rel_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_file, dst)
        except OSError as e:
            logger.error("Failed to restore %s: %s", backup_file, e)
            success = False

    if success:
        logger.info("File-copy rollback to %s successful", cp_name)
    return success


def _git_checkout_file(rel_path: Path, project_dir: Path) -> bool:
    """Cofnij jeden plik przez git checkout."""
    result = subprocess.run(
        ["git", "checkout", "--", str(rel_path)],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        logger.info("Git checkout of %s successful", rel_path)
        return True
    logger.error("Git checkout of %s failed: %s", rel_path, result.stderr)
    return False
