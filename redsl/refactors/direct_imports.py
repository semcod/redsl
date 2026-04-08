"""Direct refactoring for import cleanup."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from redsl.refactors.ast_transformers import UnusedImportRemover


class DirectImportRefactorer:
    """Handles import-related direct refactoring."""

    def __init__(self) -> None:
        self.applied_changes: list[dict[str, Any]] = []

    def remove_unused_imports(self, file_path: Path, unused_imports: list[str]) -> bool:
        """Remove unused imports from a Python file.

        Uses line-based editing to preserve original formatting.
        """
        if not unused_imports:
            return False

        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            lines = source.splitlines(keepends=True)
            unused_set = set(unused_imports)

            lines_to_remove, line_replacements = self._collect_unused_import_edits(
                tree, lines, unused_set
            )

            if not lines_to_remove and not line_replacements:
                return False

            new_source = self._apply_line_edits(lines, lines_to_remove, line_replacements)
            file_path.write_text(new_source, encoding="utf-8")

            self.applied_changes.append({
                "file": str(file_path),
                "action": "remove_unused_imports",
                "details": f"Removed: {', '.join(unused_imports)}"
            })
            return True

        except Exception as e:
            print(f"Failed to remove unused imports from {file_path}: {e}")
            return False

    def _collect_unused_import_edits(
        self,
        tree: ast.Module,
        lines: list[str],
        unused_set: set[str],
    ) -> tuple[set[int], dict[int, str]]:
        """Collect line removals and replacements for unused import cleanup."""
        lines_to_remove: set[int] = set()  # 0-indexed
        line_replacements: dict[int, str] = {}  # 0-indexed -> new content

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                self._collect_import_edits(node, lines, unused_set, lines_to_remove, line_replacements)
            elif isinstance(node, ast.ImportFrom):
                self._collect_import_from_edits(node, lines, unused_set, lines_to_remove, line_replacements)

        return lines_to_remove, line_replacements

    def _collect_import_edits(
        self,
        node: ast.Import,
        lines: list[str],
        unused_set: set[str],
        lines_to_remove: set[int],
        line_replacements: dict[int, str],
    ) -> None:
        kept = [alias for alias in node.names if self._alias_name(alias) not in unused_set]
        if len(kept) == len(node.names):
            return

        if not kept:
            self._remove_statement_lines(node, lines_to_remove)
            return

        names_str = ", ".join(self._format_alias(alias) for alias in kept)
        indent = self._get_indent(lines[node.lineno - 1])
        line_replacements[node.lineno - 1] = f"{indent}import {names_str}\n"
        self._remove_replaced_statement_lines(node, lines_to_remove)

    def _collect_import_from_edits(
        self,
        node: ast.ImportFrom,
        lines: list[str],
        unused_set: set[str],
        lines_to_remove: set[int],
        line_replacements: dict[int, str],
    ) -> None:
        if self._is_star_import(node):
            return

        kept = [alias for alias in node.names if self._alias_name(alias) not in unused_set]
        if len(kept) == len(node.names):
            return

        if not kept:
            self._remove_statement_lines(node, lines_to_remove)
            return

        replacement = self._build_import_from_replacement(node, lines, kept)
        if replacement is None:
            self._remove_statement_lines(node, lines_to_remove)
            return

        line_index, text = replacement
        line_replacements[line_index] = text
        self._remove_replaced_statement_lines(node, lines_to_remove)

    @staticmethod
    def _is_star_import(node: ast.ImportFrom) -> bool:
        return node.names[0].name == "*"

    def _build_import_from_replacement(
        self,
        node: ast.ImportFrom,
        lines: list[str],
        kept: list[ast.alias],
    ) -> tuple[int, str] | None:
        indent = self._get_indent(lines[node.lineno - 1])
        module = node.module or ""
        dots = "." * (node.level or 0)
        end_lineno = getattr(node, "end_lineno", node.lineno)

        if end_lineno > node.lineno:
            names_lines = [
                f"{indent}    {self._format_alias(alias)},"
                for alias in kept
            ]
            replacement = (
                f"{indent}from {dots}{module} import (\n"
                + "\n".join(names_lines)
                + f"\n{indent})\n"
            )
        else:
            names_str = ", ".join(self._format_alias(alias) for alias in kept)
            replacement = f"{indent}from {dots}{module} import {names_str}\n"

        return node.lineno - 1, replacement

    @staticmethod
    def _alias_name(alias: ast.alias) -> str:
        return alias.asname or alias.name

    @staticmethod
    def _format_alias(alias: ast.alias) -> str:
        return f"{alias.name} as {alias.asname}" if alias.asname else alias.name

    @staticmethod
    def _remove_statement_lines(node: ast.AST, lines_to_remove: set[int]) -> None:
        end_lineno = getattr(node, "end_lineno", node.lineno)
        for ln in range(node.lineno - 1, end_lineno):
            lines_to_remove.add(ln)

    @staticmethod
    def _remove_replaced_statement_lines(node: ast.AST, lines_to_remove: set[int]) -> None:
        end_lineno = getattr(node, "end_lineno", node.lineno)
        for ln in range(node.lineno, end_lineno):
            lines_to_remove.add(ln)

    def _apply_line_edits(
        self,
        lines: list[str],
        lines_to_remove: set[int],
        line_replacements: dict[int, str],
    ) -> str:
        new_lines = []
        for i, line in enumerate(lines):
            if i in lines_to_remove:
                continue
            if i in line_replacements:
                new_lines.append(line_replacements[i])
            else:
                new_lines.append(line)

        return self._clean_blank_lines("".join(new_lines))

    @staticmethod
    def _get_indent(line: str) -> str:
        """Return the leading whitespace of a line."""
        return line[: len(line) - len(line.lstrip())]

    @staticmethod
    def _clean_blank_lines(source: str) -> str:
        """Remove runs of 3+ consecutive blank lines, keeping max 2."""
        result: list[str] = []
        blank_count = 0
        for line in source.splitlines(keepends=True):
            if line.strip() == "":
                blank_count += 1
                if blank_count <= 2:
                    result.append(line)
            else:
                blank_count = 0
                result.append(line)
        return "".join(result)

    def get_applied_changes(self) -> list[dict[str, Any]]:
        """Get list of all applied changes."""
        return self.applied_changes


__all__ = ["DirectImportRefactorer", "UnusedImportRemover"]
