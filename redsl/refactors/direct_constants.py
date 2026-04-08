"""Direct refactoring for magic number extraction."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any


class DirectConstantsRefactorer:
    """Handles magic number to constant extraction."""

    def __init__(self) -> None:
        self.applied_changes: list[dict[str, Any]] = []

    def _build_value_to_names_map(
        self,
        magic_numbers: list[tuple[int, int | float]],
        lines: list[str],
    ) -> dict[int | float, str]:
        """Build mapping from values to constant names."""
        value_to_names: dict[int | float, str] = {}
        for line_num, value in magic_numbers:
            if value not in value_to_names:
                if 0 <= line_num - 1 < len(lines):
                    const_name = self._generate_constant_name(value, lines[line_num - 1])
                else:
                    const_name = f"CONSTANT_{int(value) if isinstance(value, int) else 'FLOAT'}"
                value_to_names[value] = const_name
        return value_to_names

    @staticmethod
    def _find_import_end_line(tree: ast.Module) -> int:
        """Find the line number after the last import statement."""
        insert_line = 0
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                insert_line = node.end_lineno  # 1-indexed end of this import
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                pass  # docstring — keep scanning
            else:
                break  # first non-import real statement
        return insert_line

    def _replace_magic_numbers(
        self,
        lines: list[str],
        magic_numbers: list[tuple[int, int | float]],
        value_to_names: dict[int | float, str],
        insert_line: int,
    ) -> None:
        """Replace magic numbers with constant names in source lines."""
        line_offset = 1  # One element inserted into the lines list

        for line_num, value in magic_numbers:
            const_name = value_to_names[value]
            adjusted_line_num = line_num - 1
            if adjusted_line_num >= insert_line:
                adjusted_line_num += line_offset

            if 0 <= adjusted_line_num < len(lines):
                lines[adjusted_line_num] = re.sub(
                    r'\b' + re.escape(str(value)) + r'\b',
                    const_name,
                    lines[adjusted_line_num]
                )

    def extract_constants(self, file_path: Path, magic_numbers: list[tuple[int, int | float]]) -> bool:
        """Extract magic numbers into named constants."""
        if len(magic_numbers) < 3:  # Only worth it for multiple numbers
            return False

        try:
            source = file_path.read_text(encoding="utf-8")
            lines = source.splitlines(keepends=True)

            # Build value -> constant name mapping
            value_to_names = self._build_value_to_names_map(magic_numbers, lines)

            # Find insertion point after imports
            tree_for_pos = ast.parse(source)
            insert_line = self._find_import_end_line(tree_for_pos)

            # Insert constants
            constants_text = '\n' + '\n'.join(
                f"{name} = {value}" for value, name in sorted(value_to_names.items())
            ) + '\n\n'
            lines.insert(insert_line, constants_text)

            # Replace magic numbers with constant names
            self._replace_magic_numbers(lines, magic_numbers, value_to_names, insert_line)

            # Write back
            file_path.write_text(''.join(lines), encoding="utf-8")

            self.applied_changes.append({
                "file": str(file_path),
                "action": "extract_constants",
                "details": f"Extracted {len(value_to_names)} constants"
            })
            return True

        except Exception as e:
            print(f"Failed to extract constants from {file_path}: {e}")
            return False

    def _generate_constant_name(self, value: int | float, context: str) -> str:
        """Generate a meaningful constant name based on value and context."""
        context_lower = context.lower()

        if 'timeout' in context_lower or 'sleep' in context_lower:
            return f"TIMEOUT_{int(value)}"
        elif 'port' in context_lower:
            return f"PORT_{int(value)}"
        elif 'max' in context_lower:
            return f"MAX_{int(value)}"
        elif 'min' in context_lower:
            return f"MIN_{int(value)}"
        elif 'retry' in context_lower or 'attempt' in context_lower:
            return f"MAX_RETRIES"
        elif 'buffer' in context_lower:
            return f"BUFFER_SIZE"
        else:
            return f"CONSTANT_{int(value)}"

    def get_applied_changes(self) -> list[dict[str, Any]]:
        """Get list of all applied changes."""
        return self.applied_changes


__all__ = ["DirectConstantsRefactorer"]
