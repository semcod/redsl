"""Direct refactoring for main guard handling."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


class DirectGuardRefactorer:
    """Handles main guard wrapping for module-level execution code."""

    def __init__(self) -> None:
        self.applied_changes: list[dict[str, Any]] = []

    @staticmethod
    def _is_main_guard_node(node: ast.If) -> bool:
        """Return True if *node* is `if __name__ == '__main__':`."""
        test = node.test
        return (
            isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name)
            and test.left.id == "__name__"
            and len(test.ops) == 1
            and isinstance(test.ops[0], ast.Eq)
            and len(test.comparators) == 1
            and isinstance(test.comparators[0], ast.Constant)
            and test.comparators[0].value == "__main__"
        )

    def _collect_guarded_lines(self, tree: ast.Module) -> set[int]:
        """Collect line numbers that are already inside __main__ guards."""
        guarded_lines: set[int] = set()
        for node in tree.body:
            if isinstance(node, ast.If) and self._is_main_guard_node(node):
                for child in ast.walk(node):
                    if hasattr(child, 'lineno'):
                        guarded_lines.add(child.lineno - 1)
        return guarded_lines

    def _collect_module_execution_lines(
        self,
        tree: ast.Module,
        guarded_lines: set[int],
    ) -> list[int]:
        """Collect module-level lines that need to be guarded (bare function calls)."""
        module_level_lines: list[int] = []
        for node in tree.body:
            # Only guard bare function/method calls at module level.
            # Assignments are intentional module-level state and must NOT be moved.
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                if (node.lineno - 1) not in guarded_lines:
                    module_level_lines.append(node.lineno - 1)
        return module_level_lines

    def _insert_main_guard(
        self,
        lines: list[str],
        module_level_lines: list[int],
    ) -> None:
        """Insert if __name__ == '__main__' guard and indent execution lines."""
        first_line = min(module_level_lines)
        indent = '    '

        # Insert the guard before the first execution line
        lines.insert(first_line, f'\nif __name__ == "__main__":\n')

        # Indent the execution lines (process in reverse to maintain indices)
        for line_num in sorted(module_level_lines, reverse=True):
            adjusted_line = line_num + 1  # Account for inserted guard
            if adjusted_line < len(lines):
                if not lines[adjusted_line].startswith(indent):
                    lines[adjusted_line] = indent + lines[adjusted_line]

    def fix_module_execution_block(self, file_path: Path) -> bool:
        """Wrap module-level code in if __name__ == '__main__' guard."""
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)

            # Collect lines already inside guards and lines needing guards
            guarded_lines = self._collect_guarded_lines(tree)
            module_level_lines = self._collect_module_execution_lines(tree, guarded_lines)

            if not module_level_lines:
                return False

            # Read lines and insert guard
            lines = source.splitlines(keepends=True)
            self._insert_main_guard(lines, module_level_lines)

            # Write back
            file_path.write_text(''.join(lines), encoding="utf-8")

            self.applied_changes.append({
                "file": str(file_path),
                "action": "fix_module_execution_block",
                "details": f"Wrapped {len(module_level_lines)} lines in main guard"
            })
            return True

        except Exception as e:
            print(f"Failed to fix module execution block in {file_path}: {e}")
            return False

    def get_applied_changes(self) -> list[dict[str, Any]]:
        """Get list of all applied changes."""
        return self.applied_changes


__all__ = ["DirectGuardRefactorer"]
