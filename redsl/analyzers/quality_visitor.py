"""AST visitor for detecting code quality issues."""

from __future__ import annotations

import ast
from typing import Any


class CodeQualityVisitor(ast.NodeVisitor):
    """Detects common code quality issues in Python AST."""

    def __init__(self) -> None:
        self.imports: dict[str, ast.Import | ast.ImportFrom] = {}
        self.imported_names: dict[str, str] = {}  # alias -> full name
        self.used_names: set[str] = set()
        self.magic_numbers: list[tuple[int, int | float]] = []  # (line, value)
        self.has_module_execution = False
        self.functions_missing_return: list[tuple[str, int]] = []  # (name, line)
        self.in_function = False
        self.in_main_guard = False
        self.module_level_statements: list[tuple[int, str]] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Track import statements."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = node
            self.imported_names[name] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Track from...import statements."""
        for alias in node.names:
            if alias.name == "*":
                continue  # Can't track star imports
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = node
            full_name = f"{node.module}.{alias.name}" if node.module else alias.name
            self.imported_names[name] = full_name
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Track name usage."""
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Track __all__ assignments to mark re-exported names as used."""
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            self.used_names.add(elt.value)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Track attribute access (e.g., module.function)."""
        # Track the base name for imported modules (handle nested attributes like urllib.request)
        root_name = self._get_root_name(node.value)
        if root_name:
            self.used_names.add(root_name)
        self.generic_visit(node)

    def _get_root_name(self, node: ast.AST) -> str | None:
        """Get the root name from a potentially nested attribute chain."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_root_name(node.value)
        return None

    def visit_Constant(self, node: ast.Constant) -> None:
        """Detect magic numbers."""
        if isinstance(node.value, (int, float)):
            # Common values that aren't considered magic numbers
            common_values = {0, 1, -1, 0.0, 1.0, -1.0, 2, 10, 100, 1000}
            if node.value not in common_values and abs(node.value) > 1:
                self.magic_numbers.append((node.lineno, node.value))
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check for missing return type annotations."""
        self.in_function = True
        if node.returns is None and node.name != "__init__":
            self.functions_missing_return.append((node.name, node.lineno))
        self.generic_visit(node)
        self.in_function = False

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Check for missing return type annotations in async functions."""
        self.in_function = True
        if node.returns is None and node.name != "__init__":
            self.functions_missing_return.append((node.name, node.lineno))
        self.generic_visit(node)
        self.in_function = False

    def visit_If(self, node: ast.If) -> None:
        """Detect __name__ == '__main__' guards."""
        # Check if this is a main guard
        if (self._is_main_guard(node)):
            self.in_main_guard = True
            # Visit the body - it's allowed execution
            for stmt in node.body:
                self.visit(stmt)
            self.in_main_guard = False
            # Don't visit the orelse - it's module level
            for stmt in node.orelse:
                self.visit(stmt)
        else:
            self.generic_visit(node)

    def _is_main_guard(self, node: ast.If) -> bool:
        """Check if node is `if __name__ == '__main__':`."""
        if not isinstance(node.test, ast.Compare):
            return False
        
        # Check left side is __name__
        if not (isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__"):
            return False
        
        # Check comparison with '__main__'
        if len(node.test.ops) != 1 or not isinstance(node.test.ops[0], ast.Eq):
            return False
        
        if len(node.test.comparators) != 1:
            return False
        
        comp = node.test.comparators[0]
        return isinstance(comp, ast.Constant) and comp.value == "__main__"

    def generic_visit(self, node: ast.AST) -> None:
        """Track module-level statements."""
        if not self.in_function and not self.in_main_guard:
            # Check if this is a module-level statement that might be execution
            if isinstance(node, (ast.Expr, ast.Assign, ast.AugAssign, ast.Call)):
                # Skip declarations and docstrings
                if not (isinstance(node, ast.Expr) and 
                       isinstance(node.value, ast.Constant) and 
                       isinstance(node.value.value, str)):
                    self.module_level_statements.append((node.lineno, type(node).__name__))
        
        super().generic_visit(node)

    def _is_import_used(self, name: str) -> bool:
        """Check if import name or any of its prefixes is in used_names.

        For `import urllib.request` used as `urllib.request.urlopen()`,
        the root `urllib` is marked used, so this should return True.
        """
        if name in self.used_names:
            return True
        # Check if any prefix is used (e.g., "urllib" for "urllib.request")
        parts = name.split(".")
        for i in range(1, len(parts)):
            prefix = ".".join(parts[:i])
            if prefix in self.used_names:
                return True
        return False

    def get_unused_imports(self) -> list[str]:
        """Get list of unused import names."""
        unused = []
        for name in self.imports:
            if not self._is_import_used(name):
                # Skip special cases
                if name in ("__future__", "typing"):
                    continue
                # Skip all __future__ imports (e.g. `from __future__ import annotations`)
                node = self.imports[name]
                if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                    continue
                unused.append(name)
        return unused

    def has_module_execution_block(self) -> bool:
        """Check if there's code executed at module level."""
        return len(self.module_level_statements) > 0

    def get_metrics(self) -> dict[str, Any]:
        """Return all detected quality metrics."""
        return {
            "unused_imports": len(self.get_unused_imports()),
            "magic_numbers": len(self.magic_numbers),
            "module_execution_block": 1 if self.has_module_execution_block() else 0,
            "missing_return_types": len(self.functions_missing_return),
            "unused_import_list": self.get_unused_imports(),
            "magic_number_list": self.magic_numbers,
            "functions_missing_return": self.functions_missing_return,
            "module_statements": self.module_level_statements,
        }
