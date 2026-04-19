"""Body indentation fixers for project doctor.

Fixes for function/class body lines that lost their proper indentation level
or have excess indentation. These fixers are used by ``_fix_guard_with_excess_indent``
and ``_fix_stolen_indent`` to correct indentation after guard block removal.

All fixers preserve AST validity and automatically revert changes if the resulting source
fails to parse. Used by ``redsl doctor`` command to auto-fix code quality issues.
"""

import ast
import re
from pathlib import Path

from ._fixer_utils import _read_source

_DEF_RE = re.compile(r"^(class|def|async\s+def|try)\s*")


def _scan_next_nonblank(lines: list[str], start: int) -> int:
    """Return index of next non-blank line from *start*, or len(lines)."""
    peek = start
    while peek < len(lines) and not lines[peek].strip():
        peek += 1
    return peek


def _process_def_block(lines: list[str], i: int, new_lines: list[str], changed: bool) -> tuple[list[str], int, bool]:
    """Handle a def/class/try block: fix body indent or strip excess indent."""
    def_indent = len(lines[i]) - len(lines[i].lstrip())
    expected = def_indent + 4
    new_lines.append(lines[i])
    i += 1

    peek = _scan_next_nonblank(lines, i)
    if peek < len(lines):
        next_line = lines[peek]
        actual = len(next_line) - len(next_line.lstrip())

        if actual == def_indent and next_line.strip():
            new_lines, i, changed = _fix_body_indent(lines, i, new_lines, def_indent, expected, changed)
        elif actual > expected + 4 and next_line.strip():
            new_lines, i, changed = _check_excess_indent(lines, i, new_lines, def_indent, expected, changed)
    return new_lines, i, changed


def _fix_stolen_indent(path: Path) -> bool:
    """Re-indent function/class body lines that lost their indentation.

    Handles two patterns:
      1. Body at same indent level as def/class (should be +4)
      2. Body with excess indent (extra +4 that shouldn't be there)
    """
    src = _read_source(path)
    if src is None:
        return False

    lines = src.splitlines(keepends=True)
    new_lines: list[str] = []
    i = 0
    changed = False

    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip()

        if _DEF_RE.match(stripped.lstrip()) and stripped.endswith(":"):
            new_lines, i, changed = _process_def_block(lines, i, new_lines, changed)
        else:
            new_lines.append(line)
            i += 1

    if changed:
        path.write_text("".join(new_lines), encoding="utf-8")
    return changed


def _handle_function_indent(lines: list[str], i: int, new_lines: list[str], changed: bool) -> tuple[list[str], int, bool]:
    """Detect and fix body indentation for a def/class/try block."""
    def_indent = len(lines[i]) - len(lines[i].lstrip())
    expected = def_indent + 4
    new_lines.append(lines[i])
    i += 1

    peek = i
    while peek < len(lines) and not lines[peek].strip():
        peek += 1

    if peek < len(lines):
        next_line = lines[peek]
        actual = len(next_line) - len(next_line.lstrip())

        if actual == def_indent and next_line.strip():
            new_lines, i, changed = _fix_body_indent(lines, i, new_lines, def_indent, expected, changed)
        elif actual == expected:
            new_lines, i, changed = _check_excess_indent(lines, i, new_lines, def_indent, expected, changed)
    return new_lines, i, changed


def _fix_body_indent(lines: list[str], i: int, new_lines: list[str], def_indent: int, expected: int, changed: bool) -> tuple[list[str], int, bool]:
    """Re-indent body lines that sit at def_indent instead of expected (def_indent+4)."""
    saw_blank = False
    while i < len(lines):
        bl = lines[i]
        bl_stripped = bl.rstrip()
        bl_indent = len(bl) - len(bl.lstrip()) if bl.strip() else -1

        if not bl.strip():
            saw_blank = True
            new_lines.append(bl)
            i += 1
            continue

        if bl_indent < def_indent:
            break

        if bl_indent == def_indent and saw_blank and _DEF_RE.match(bl_stripped.lstrip()):
            break

        saw_blank = False
        if bl_indent <= def_indent:
            new_lines.append(" " * expected + bl.lstrip())
            changed = True
        else:
            new_lines.append(bl)
        i += 1
    return new_lines, i, changed


def _detect_excess_indent(lines: list[str], i: int, expected: int, def_indent: int) -> bool:
    """Return True if body lines after position i are over-indented by 4."""
    scan = i + 1
    while scan < min(i + 10, len(lines)):
        if not lines[scan].strip():
            scan += 1
            continue
        scan_indent = len(lines[scan]) - len(lines[scan].lstrip())
        if scan_indent == expected + 4:
            return True
        elif scan_indent <= def_indent:
            break
        scan += 1
    return False


def _strip_excess_indent(lines: list[str], i: int, new_lines: list[str], def_indent: int, expected: int, scan: int, changed: bool) -> tuple[list[str], int, bool]:
    """Strip one extra indent level from over-indented body lines."""
    while i < len(lines):
        bl = lines[i]
        bl_indent = len(bl) - len(bl.lstrip()) if bl.strip() else -1
        if not bl.strip():
            new_lines.append(bl)
            i += 1
            continue
        if bl_indent <= def_indent and i > scan:
            break
        if bl_indent >= expected + 4:
            new_lines.append(bl[4:])
            changed = True
        else:
            new_lines.append(bl)
        i += 1
    return new_lines, i, changed


def _check_excess_indent(lines: list[str], i: int, new_lines: list[str], def_indent: int, expected: int, changed: bool) -> tuple[list[str], int, bool]:
    """Strip one extra indent level from body lines that are over-indented by 4."""
    if _detect_excess_indent(lines, i, expected, def_indent):
        scan = i + 1
        new_lines, i, changed = _strip_excess_indent(lines, i, new_lines, def_indent, expected, scan, changed)
    return new_lines, i, changed


def _iterative_fix(path: Path, original_src: str) -> bool:
    """Apply _fix_stolen_indent up to 5 times until AST parses; revert on failure."""
    for _ in range(5):
        try:
            ast.parse(path.read_text(encoding="utf-8"))
            return True
        except SyntaxError:
            if not _fix_stolen_indent(path):
                break
    try:
        ast.parse(path.read_text(encoding="utf-8"))
        return True
    except SyntaxError:
        path.write_text(original_src, encoding="utf-8")
        return False
