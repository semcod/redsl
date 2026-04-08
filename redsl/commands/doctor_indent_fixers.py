"""Indentation fixers for project doctor."""

import ast
import re
from pathlib import Path
from typing import List, Tuple

_GUARD_RE = re.compile(r"^if\s+__name__\s*==\s*[\"\']__main__[\"\']\s*:\s*$")
_DEF_RE = re.compile(r"^(class|def|async\s+def|try)\s*")

def _fix_guard_in_try_block(path: Path) -> bool:
    """Fix ``if __name__`` guard that was incorrectly placed inside a try/except.

    Pattern:
        try:
            from dotenv import load_dotenv
        if __name__ == "__main__":    ← breaks the try/except
            load_dotenv()
        except ImportError:
            pass

    Fix → restore the try body:
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
    """
    src = _read_source(path)
    if src is None:
        return False

    lines = src.splitlines(keepends=True)
    new_lines: list[str] = []
    i = 0
    changed = False

    while i < len(lines):
        stripped = lines[i].rstrip()

        if _GUARD_RE.match(stripped):
            guard_body, j = _collect_guard_body(lines, i)
            if _is_guard_followed_by_except(lines, j):
                new_lines.extend(guard_body)
                if guard_body and not guard_body[-1].endswith("\n"):
                    new_lines.append("\n")
                i = j
                changed = True
                continue

        new_lines.append(lines[i])
        i += 1

    if changed:
        path.write_text("".join(new_lines), encoding="utf-8")
    return changed

def _fix_guard_with_excess_indent(path: Path) -> bool:
    """Fix a bare ``if __name__`` guard whose body was a simple statement,
    followed by functions with excess-indented bodies.

    Pattern:
        if __name__ == "__main__":
            console = Console()

        def func():
            '''docs'''
            from x import y
                body_line = ...          ← excess indent

    Fix: remove guard, emit its body at module level, then un-indent
    function bodies that have 8-space indent after 4-space first line.
    """
    try:
        src = path.read_text(encoding="utf-8")
    except OSError:
        return False

    lines = src.splitlines(keepends=True)
    new_lines, changed = _process_guard_and_indent(lines)

    if changed:
        result = "".join(new_lines)
        path.write_text(result, encoding="utf-8")
        return _iterative_fix(path, src)
    return False

def _process_guard_and_indent(lines: list[str]) -> tuple[list[str], bool]:
    new_lines: list[str] = []
    i = 0
    changed = False

    while i < len(lines):
        stripped = lines[i].rstrip()

        if _GUARD_RE.match(stripped):
            new_lines, i, changed = _handle_guard(lines, i, new_lines)
            continue

        if _DEF_RE.match(stripped.lstrip()) and stripped.endswith(":"):
            new_lines, i, changed = _handle_function_indent(lines, i, new_lines, changed)
            continue

        new_lines.append(lines[i])
        i += 1

    return new_lines, changed

def _handle_guard(lines: list[str], i: int, new_lines: list[str]) -> tuple[list[str], int, bool]:
    guard_body: list[str] = []
    j = i + 1
    while j < len(lines):
        bl = lines[j]
        if bl.strip() == "" or bl.startswith("    ") or bl.startswith("\t"):
            guard_body.append(bl)
            j += 1
        else:
            break
    while guard_body and not guard_body[-1].strip():
        guard_body.pop()
    for bl in guard_body:
        if bl.startswith("    "):
            new_lines.append(bl[4:])
        elif bl.startswith("\t"):
            new_lines.append(bl[1:])
        else:
            new_lines.append(bl)
    if guard_body:
        new_lines.append("\n")
    return new_lines, j, True

def _handle_function_indent(lines: list[str], i: int, new_lines: list[str], changed: bool) -> tuple[list[str], int, bool]:
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

def _check_excess_indent(lines: list[str], i: int, new_lines: list[str], def_indent: int, expected: int, changed: bool) -> tuple[list[str], int, bool]:
    has_excess = False
    scan = i + 1
    while scan < min(i + 10, len(lines)):
        if not lines[scan].strip():
            scan += 1
            continue
        scan_indent = len(lines[scan]) - len(lines[scan].lstrip())
        if scan_indent == expected + 4:
            has_excess = True
            break
        elif scan_indent <= def_indent:
            break
        scan += 1

    if has_excess:
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

def _iterative_fix(path: Path, original_src: str) -> bool:
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


def _read_source(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _collect_guard_body(lines: list[str], start: int) -> tuple[list[str], int]:
    guard_body: list[str] = []
    j = start + 1
    while j < len(lines):
        bl = lines[j]
        if bl.strip() == "" or bl.startswith("    ") or bl.startswith("\t"):
            guard_body.append(bl)
            j += 1
        else:
            break
    while guard_body and not guard_body[-1].strip():
        guard_body.pop()
    return guard_body, j


def _next_non_blank_index(lines: list[str], start: int) -> int | None:
    idx = start
    while idx < len(lines):
        if lines[idx].strip():
            return idx
        idx += 1
    return None


def _is_guard_followed_by_except(lines: list[str], start: int) -> bool:
    next_idx = _next_non_blank_index(lines, start)
    return next_idx is not None and lines[next_idx].strip().startswith("except")

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
            def_indent = len(line) - len(line.lstrip())
            expected = def_indent + 4
            new_lines.append(line)
            i += 1

            peek = i
            while peek < len(lines) and not lines[peek].strip():
                peek += 1

            if peek < len(lines):
                next_line = lines[peek]
                actual = len(next_line) - len(next_line.lstrip())

                if actual == def_indent and next_line.strip():
                    new_lines, i, changed = _fix_body_indent(lines, i, new_lines, def_indent, expected, changed)
                elif actual > expected + 4 and next_line.strip():
                    new_lines, i, changed = _check_excess_indent(lines, i, new_lines, def_indent, expected, changed)
        else:
            new_lines.append(line)
            i += 1

    if changed:
        path.write_text("".join(new_lines), encoding="utf-8")
    return changed

