"""Guard block fixers for project doctor.

Fixes for ``if __name__ == "__main__"`` guard blocks that were incorrectly
placed inside try/except blocks or have excess indentation in function bodies.

All fixers preserve AST validity and automatically revert changes if the resulting source
fails to parse. Used by ``redsl doctor`` command to auto-fix code quality issues.
"""

import re
from pathlib import Path

_GUARD_RE = re.compile(r"^if\s+__name__\s*==\s*[\"\']__main__[\"\']\s*:\s*$")


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
    from redsl.commands._indent_fixers import _iterative_fix

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
    """Process lines to remove guard blocks and fix excess indentation."""
    from redsl.commands._indent_fixers import _DEF_RE

    new_lines: list[str] = []
    i = 0
    changed = False

    while i < len(lines):
        stripped = lines[i].rstrip()

        if _GUARD_RE.match(stripped):
            new_lines, i, changed = _handle_guard(lines, i, new_lines)
            continue

        if _DEF_RE.match(stripped.lstrip()) and stripped.endswith(":"):
            from redsl.commands._indent_fixers import _handle_function_indent
            new_lines, i, changed = _handle_function_indent(lines, i, new_lines, changed)
            continue

        new_lines.append(lines[i])
        i += 1

    return new_lines, changed


def _handle_guard(lines: list[str], i: int, new_lines: list[str]) -> tuple[list[str], int, bool]:
    """Consume a guard block and emit its body de-indented by one level."""
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


def _read_source(path: Path) -> str | None:
    """Read file source text, returning None on OS error."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _collect_guard_body(lines: list[str], start: int) -> tuple[list[str], int]:
    """Collect indented lines following a guard at `start`; strip trailing blanks."""
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
    """Return index of first non-blank line at or after `start`, or None."""
    idx = start
    while idx < len(lines):
        if lines[idx].strip():
            return idx
        idx += 1
    return None


def _is_guard_followed_by_except(lines: list[str], start: int) -> bool:
    """Return True if the first non-blank line at `start` begins an except clause."""
    next_idx = _next_non_blank_index(lines, start)
    return next_idx is not None and lines[next_idx].strip().startswith("except")
