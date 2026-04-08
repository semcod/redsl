"""Direct refactoring implementations — thin facade over specialized modules.

Backward compatibility: DirectRefactorEngine API remains unchanged.
Implementation now delegates to focused submodules:
- direct_imports: import cleanup
- direct_guard: main guard wrapping
- direct_constants: magic number extraction
- direct_types: return type annotations
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from redsl.refactors.ast_transformers import ReturnTypeAdder, UnusedImportRemover
from redsl.refactors.direct_constants import DirectConstantsRefactorer
from redsl.refactors.direct_guard import DirectGuardRefactorer
from redsl.refactors.direct_imports import DirectImportRefactorer
from redsl.refactors.direct_types import DirectTypesRefactorer


class DirectRefactorEngine:
    """Applies simple refactorings directly via AST manipulation.

    This is a thin facade that delegates to specialized refactorer classes.
    Maintains full backward compatibility with the original API.
    """

    def __init__(self) -> None:
        self._import_refactorer = DirectImportRefactorer()
        self._guard_refactorer = DirectGuardRefactorer()
        self._constants_refactorer = DirectConstantsRefactorer()
        self._types_refactorer = DirectTypesRefactorer()

    def remove_unused_imports(self, file_path: Path, unused_imports: list[str]) -> bool:
        """Remove unused imports from a Python file."""
        return self._import_refactorer.remove_unused_imports(file_path, unused_imports)


    def fix_module_execution_block(self, file_path: Path) -> bool:
        """Wrap module-level code in if __name__ == '__main__' guard."""
        return self._guard_refactorer.fix_module_execution_block(file_path)

    def extract_constants(self, file_path: Path, magic_numbers: list[tuple[int, int | float]]) -> bool:
        """Extract magic numbers into named constants."""
        return self._constants_refactorer.extract_constants(file_path, magic_numbers)

    def add_return_types(self, file_path: Path, functions_missing_return: list[tuple[str, int]]) -> bool:
        """Add return type annotations to functions."""
        return self._types_refactorer.add_return_types(file_path, functions_missing_return)

    def get_applied_changes(self) -> list[dict[str, Any]]:
        """Get list of all applied changes from all refactorers."""
        changes: list[dict[str, Any]] = []
        changes.extend(self._import_refactorer.get_applied_changes())
        changes.extend(self._guard_refactorer.get_applied_changes())
        changes.extend(self._constants_refactorer.get_applied_changes())
        changes.extend(self._types_refactorer.get_applied_changes())
        return changes


__all__ = ["DirectRefactorEngine", "ReturnTypeAdder", "UnusedImportRemover"]
