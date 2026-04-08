"""AST-based transformer classes for deterministic code transformations."""

from __future__ import annotations

import ast


class ReturnTypeAdder(ast.NodeTransformer):
    """AST transformer to add return type annotations."""

    def __init__(self, functions_missing_return: list[tuple[str, int]]) -> None:
        self.functions_to_fix = {name for name, _ in functions_missing_return}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Add return type annotation to function."""
        self.generic_visit(node)

        if node.name in self.functions_to_fix and node.returns is None:
            return_type = self._infer_return_type(node)
            if return_type:
                node.returns = return_type

        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """Add return type annotation to async function."""
        self.generic_visit(node)

        if node.name in self.functions_to_fix and node.returns is None:
            return_type = self._infer_return_type(node)
            if return_type:
                node.returns = return_type

        return node

    # Type mapping for AST nodes to type names
    _AST_TYPE_MAP: dict[type, str] = {
        ast.List: 'list',
        ast.Dict: 'dict',
        ast.Tuple: 'tuple',
        ast.Set: 'set',
    }

    def _get_type_from_constant(self, node: ast.Constant) -> str | None:
        """Get type name from a Constant node."""
        value = node.value
        if isinstance(value, bool):
            return 'bool'
        if isinstance(value, int):
            return 'int'
        if isinstance(value, float):
            return 'float'
        if isinstance(value, str):
            return 'str'
        if value is None:
            return 'None'
        return None

    def _infer_return_type(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> ast.expr | None:
        """Infer return type from function body."""
        return_statements = [
            child.value for child in ast.walk(node)
            if isinstance(child, ast.Return) and child.value is not None
        ]

        if not return_statements:
            return ast.Name(id='None', ctx=ast.Load())

        types: set[str] = set()
        for ret in return_statements:
            type_name = self._extract_type_name(ret)
            if type_name is None:
                return None
            types.add(type_name)

        if len(types) != 1:
            return None

        type_name = types.pop()
        return ast.Name(id=type_name, ctx=ast.Load())

    def _extract_type_name(self, ret: ast.expr) -> str | None:
        """Extract type name from a return value AST node."""
        if isinstance(ret, ast.Constant):
            return self._get_type_from_constant(ret)
        if isinstance(ret, ast.Name):
            return ret.id
        # Use dispatch table for container types
        for node_type, type_name in self._AST_TYPE_MAP.items():
            if isinstance(ret, node_type):
                return type_name
        return None


class UnusedImportRemover(ast.NodeTransformer):
    """AST transformer to remove unused imports."""

    def __init__(self, unused_imports: list[str]) -> None:
        self.unused_imports = set(unused_imports)

    def visit_Import(self, node: ast.Import) -> ast.Import | None:
        """Remove unused imports from import statements."""
        new_aliases = []
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            if name not in self.unused_imports:
                new_aliases.append(alias)

        if new_aliases:
            node.names = new_aliases
            return node
        return None

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom | None:
        """Remove unused imports from from...import statements."""
        if node.names[0].name == "*":
            return node

        new_aliases = []
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            if name not in self.unused_imports:
                new_aliases.append(alias)

        if new_aliases:
            node.names = new_aliases
            return node
        return None


__all__ = ["ReturnTypeAdder", "UnusedImportRemover"]
