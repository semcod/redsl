"""Direct refactoring for return type annotations."""

from __future__ import annotations

import ast
import io
import tokenize
from pathlib import Path
from typing import Any

from redsl.refactors.ast_transformers import ReturnTypeAdder


class DirectTypesRefactorer:
    """Handles return type annotation addition."""

    def __init__(self) -> None:
        self.applied_changes: list[dict[str, Any]] = []

    def _collect_return_type_replacements(
        self,
        tree: ast.Module,
        lines: list[str],
        functions_missing_return: list[tuple[str, int]],
    ) -> dict[int, str]:
        replacements: dict[int, str] = {}
        to_fix = {(name, lineno) for name, lineno in functions_missing_return}
        inferrer = ReturnTypeAdder(functions_missing_return)

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if (node.name, node.lineno) not in to_fix or node.returns is not None:
                continue

            ret_type = inferrer._infer_return_type(node)
            if ret_type is None:
                continue

            signature = self._find_signature_colon(
                lines,
                node.lineno - 1,
                getattr(node, "end_lineno", node.lineno),
            )
            if signature is None:
                continue

            line_index, colon_idx = signature
            line = lines[line_index]
            before = line[:colon_idx].rstrip()
            after = line[colon_idx:]
            replacements[line_index] = f"{before} -> {ast.unparse(ret_type)}{after}"

        return replacements

    @staticmethod
    def _find_signature_colon(
        lines: list[str],
        start_line: int,
        end_line: int,
    ) -> tuple[int, int] | None:
        snippet = "".join(lines[start_line:end_line])
        depth = 0

        for token in tokenize.generate_tokens(io.StringIO(snippet).readline):
            if token.type != tokenize.OP:
                continue
            if token.string in "([{":
                depth += 1
            elif token.string in ")}]":
                depth = max(0, depth - 1)
            elif token.string == ":" and depth == 0:
                return start_line + token.start[0] - 1, token.start[1]

        return None

    def add_return_types(self, file_path: Path, functions_missing_return: list[tuple[str, int]]) -> bool:
        """Add return type annotations to functions.

        Uses line-based editing to preserve original formatting.
        """
        if not functions_missing_return:
            return False

        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            lines = source.splitlines(keepends=True)
            replacements = self._collect_return_type_replacements(
                tree,
                lines,
                functions_missing_return,
            )

            if not replacements:
                return False

            new_lines = [replacements.get(i, line) for i, line in enumerate(lines)]
            file_path.write_text("".join(new_lines), encoding="utf-8")

            self.applied_changes.append({
                "file": str(file_path),
                "action": "add_return_types",
                "details": f"Added return types to {len(functions_missing_return)} functions"
            })
            return True

        except Exception as e:
            print(f"Failed to add return types to {file_path}: {e}")
            return False

    @staticmethod
    def _find_def_colon(line: str, is_first_line: bool) -> int | None:
        """Find the index of the colon ending a def signature on this line.

        Skips colons inside strings and parentheses.
        Returns None if no signature-ending colon is found.
        """
        signature = DirectTypesRefactorer._find_signature_colon([line], 0, 1)
        return signature[1] if signature else None

    def get_applied_changes(self) -> list[dict[str, Any]]:
        """Get list of all applied applied changes."""
        return self.applied_changes


__all__ = ["DirectTypesRefactorer", "ReturnTypeAdder"]
