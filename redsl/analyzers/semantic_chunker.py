"""
Semantic chunker — przygotowanie kontekstu funkcji dla LLM.

Zamiast wysyłać cały plik (może być 1000L), wytnij:
1. Docstring modułu + importy (filtrowane do tych używanych w funkcji)
2. Definicję klasy jeśli to metoda (sygnatura + docstring)
3. Funkcję docelową (pełny kod)
4. Opcjonalnie: sąsiednie funkcje z tej samej klasy/modułu

Punkt 2.2 z planu ewolucji.
Redukuje tokeny LLM i poprawia jakość propozycji przez skupienie kontekstu.
"""

from __future__ import annotations

import ast
import logging
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

_MAX_CONTEXT_LINES = 150
_MAX_NEIGHBOR_LINES = 30


@dataclass
class SemanticChunk:
    """Wycięty semantyczny fragment kodu gotowy do wysłania do LLM."""

    target_function: str
    file_path: str
    source: str
    imports: str = ""
    class_context: str = ""
    neighbor_functions: list[str] = field(default_factory=list)
    total_lines: int = 0
    truncated: bool = False

    def to_llm_prompt(self) -> str:
        """Złóż chunk w sformatowany prompt dla LLM."""
        parts: list[str] = []

        if self.imports:
            parts.append(f"# Imports used in this function:\n{self.imports}")

        if self.class_context:
            parts.append(f"# Class context:\n{self.class_context}")

        if self.neighbor_functions:
            for nb in self.neighbor_functions[:2]:
                parts.append(f"# Neighboring function:\n{nb}")

        parts.append(f"# Function to refactor:\n{self.source}")

        if self.truncated:
            parts.append("# [context truncated for length]")

        return "\n\n".join(parts)


class SemanticChunker:
    """Buduje semantyczne chunki kodu dla LLM."""

    def chunk_function(
        self,
        file_path: Path,
        func_name: str,
        include_neighbors: bool = True,
        max_lines: int = _MAX_CONTEXT_LINES,
    ) -> SemanticChunk | None:
        """Wytnij semantyczny chunk dla jednej funkcji.

        Args:
            file_path:         Ścieżka do pliku .py
            func_name:         Nazwa funkcji (lub Class.method)
            include_neighbors: Czy dodawać sąsiednie funkcje
            max_lines:         Maksymalna liczba linii kontekstu

        Returns:
            SemanticChunk lub None jeśli funkcja nie znaleziona
        """
        parsed = self._parse_source(file_path)
        if parsed is None:
            return None
        source, tree, lines = parsed

        short_name = func_name.split(".")[-1]
        class_name = func_name.split(".")[0] if "." in func_name else None

        func_node, class_node = self._find_nodes(tree, short_name, class_name)
        if func_node is None:
            logger.debug("Function %r not found in %s", func_name, file_path)
            return None

        func_src = textwrap.dedent("".join(lines[func_node.lineno - 1:func_node.end_lineno]))
        imports_src = self._extract_relevant_imports(tree, lines, func_src)
        class_ctx = self._extract_class_context(class_node, lines) if class_node else ""
        neighbors = self._extract_neighbors(tree, func_node, class_node, lines, max_lines) if include_neighbors else []

        return self._build_chunk(func_name, file_path, func_src, imports_src, class_ctx, neighbors, max_lines)

    @staticmethod
    def _parse_source(file_path: Path) -> tuple[str, ast.AST, list[str]] | None:
        """Read and parse source file. Returns (source, tree, lines) or None."""
        try:
            source = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source, filename=str(file_path))
        except (OSError, SyntaxError) as e:
            logger.warning("Could not parse %s: %s", file_path, e)
            return None
        return source, tree, source.splitlines(keepends=True)

    @staticmethod
    def _build_chunk(func_name: str, file_path: Path, func_src: str,
                     imports_src: str, class_ctx: str, neighbors: list[str],
                     max_lines: int) -> SemanticChunk:
        """Build SemanticChunk with truncation if needed."""
        total = (
            len(func_src.splitlines())
            + len(imports_src.splitlines())
            + len(class_ctx.splitlines())
            + sum(len(n.splitlines()) for n in neighbors)
        )
        truncated = total > max_lines
        if truncated:
            neighbors = neighbors[:1] if neighbors else []
            logger.debug("Chunk for %r truncated (%d lines > %d)", func_name, total, max_lines)

        return SemanticChunk(
            target_function=func_name,
            file_path=str(file_path),
            source=func_src,
            imports=imports_src,
            class_context=class_ctx,
            neighbor_functions=neighbors,
            total_lines=min(total, max_lines),
            truncated=truncated,
        )

    def chunk_file(
        self,
        file_path: Path,
        max_lines: int = _MAX_CONTEXT_LINES,
    ) -> list[SemanticChunk]:
        """Wygeneruj chunki dla wszystkich funkcji w pliku."""
        try:
            source = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source, filename=str(file_path))
        except (OSError, SyntaxError):
            return []

        chunks = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                chunk = self.chunk_function(file_path, node.name, include_neighbors=False,
                                            max_lines=max_lines)
                if chunk:
                    chunks.append(chunk)
        return chunks

    @staticmethod
    def _find_nodes(
        tree: ast.AST, func_name: str, class_name: str | None
    ) -> tuple[ast.FunctionDef | ast.AsyncFunctionDef | None, ast.ClassDef | None]:
        """Znajdź węzeł funkcji i klasy w drzewie AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if class_name and node.name != class_name:
                    continue
                for item in ast.iter_child_nodes(node):
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if item.name == func_name:
                            return item, node
            elif class_name is None and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == func_name:
                    return node, None
        return None, None

    @staticmethod
    def _extract_relevant_imports(
        tree: ast.AST, lines: list[str], func_src: str
    ) -> str:
        """Wytnij tylko importy których nazwy pojawiają się w funkcji."""
        import_lines: list[str] = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    if name in func_src:
                        import_lines.append("".join(lines[node.lineno - 1:node.end_lineno]))
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    if name in func_src:
                        import_lines.append("".join(lines[node.lineno - 1:node.end_lineno]))
                        break
        return "".join(import_lines).strip()

    @staticmethod
    def _extract_class_context(class_node: ast.ClassDef, lines: list[str]) -> str:
        """Wytnij sygnaturę klasy i docstring (bez ciał metod)."""
        class_line = lines[class_node.lineno - 1]
        docstring = ast.get_docstring(class_node)
        if docstring:
            return f"{class_line.rstrip()}\n    \"\"\"{docstring[:200]}...\"\"\""
        return class_line.rstrip()

    @staticmethod
    def _extract_neighbors(
        tree: ast.AST,
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
        class_node: ast.ClassDef | None,
        lines: list[str],
        max_lines: int,
    ) -> list[str]:
        """Wytnij sąsiednie funkcje (z tej samej klasy lub modułu)."""
        parent = class_node if class_node else tree
        siblings: list[ast.FunctionDef | ast.AsyncFunctionDef] = []

        for child in ast.iter_child_nodes(parent):
            if (
                isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                and child.name != func_node.name
            ):
                siblings.append(child)

        result = []
        for sibling in siblings[:3]:
            src_lines = lines[sibling.lineno - 1:sibling.end_lineno]
            if len(src_lines) <= _MAX_NEIGHBOR_LINES:
                result.append("".join(src_lines))

        return result
