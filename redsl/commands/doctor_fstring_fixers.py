"""F-string fixers for project doctor."""

import ast
import re
from pathlib import Path


_MULTILINE_FSTRING_RE = re.compile(r"""(f)('''|\"\"\")""", re.DOTALL)
_SINGLE_CLOSE_RE = re.compile(r'(f["\'].*?)(\b\w+)(})')


def _read_source(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _write_if_parses(path: Path, src: str) -> bool:
    try:
        ast.parse(src)
    except SyntaxError:
        return False
    path.write_text(src, encoding="utf-8")
    return True


def _fix_single_line_fstring_line(line: str) -> tuple[str, bool]:
    if not ("f'" in line or 'f"' in line):
        return line, False

    match = _SINGLE_CLOSE_RE.search(line)
    if not match:
        return line, False

    prefix = match.group(1)
    before = prefix + match.group(2)
    opens = before.count("{") - before.count("{{")
    closes = before.count("}") - before.count("}}")
    if opens > closes:
        return line, False
    fixed_line = line[:match.start(2)] + "{" + line[match.start(2):]
    return fixed_line, True


def _apply_single_line_fstring_fixes(src: str) -> tuple[str, bool]:
    changed = False
    new_lines: list[str] = []
    for line in src.splitlines(keepends=True):
        fixed_line, line_changed = _fix_single_line_fstring_line(line)
        new_lines.append(fixed_line)
        changed = changed or line_changed
    return "".join(new_lines), changed


def _fix_multiline_fstring_chunk(src: str) -> tuple[str, bool]:
    result_parts: list[str] = []
    last_end = 0
    changed = False

    for match in _MULTILINE_FSTRING_RE.finditer(src):
        quote = match.group(2)
        body_start = match.end()
        close_idx = src.find(quote, body_start)
        if close_idx == -1:
            continue

        body = src[body_start:close_idx]
        fixed_body = _escape_fstring_body_braces(body)
        if fixed_body != body:
            result_parts.append(src[last_end:body_start])
            result_parts.append(fixed_body)
            last_end = close_idx
            changed = True

    if not changed:
        return src, False

    result_parts.append(src[last_end:])
    return "".join(result_parts), True


def _consume_open_fstring_brace(body: str, i: int, result: list[str]) -> int:
    if i + 1 < len(body) and body[i + 1] == "{":
        result.append("{{")
        return i + 2

    depth = 1
    j = i + 1
    while j < len(body) and depth > 0:
        if body[j] == "{":
            depth += 1
        elif body[j] == "}":
            depth -= 1
        j += 1

    if depth == 0:
        inner = body[i + 1 : j - 1]
        if inner.strip() and _is_fstring_expr(inner):
            result.append("{")
            result.append(inner)
            result.append("}")
        else:
            result.append("{{")
            result.append(inner)
            result.append("}}")
        return j

    result.append("{{")
    return i + 1


def _consume_close_fstring_brace(body: str, i: int, result: list[str]) -> int:
    if i + 1 < len(body) and body[i + 1] == "}":
        result.append("}}")
        return i + 2
    result.append("}}")
    return i + 1

def _fix_broken_fstring(path: Path) -> bool:
    """Fix common broken f-string patterns (single brace, multiline issues)."""
    src = _read_source(path)
    if src is None:
        return False

    new_src = _fix_multiline_fstring_braces(src)
    multiline_changed = new_src != src
    new_src, single_line_changed = _apply_single_line_fstring_fixes(new_src)
    if not (multiline_changed or single_line_changed):
        return False
    return _write_if_parses(path, new_src)

def _fix_multiline_fstring_braces(src: str) -> str:
    """Fix unbalanced braces in multiline f-string body."""
    return _fix_multiline_fstring_chunk(src)[0]

def _escape_fstring_body_braces(body: str) -> str:
    """Escape unbalanced braces in f-string body content."""
    result: list[str] = []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == '{':
            i = _consume_open_fstring_brace(body, i, result)
        elif ch == '}':
            i = _consume_close_fstring_brace(body, i, result)
        else:
            result.append(ch)
            i += 1
    return "".join(result)

def _is_fstring_expr(inner: str) -> bool:
    """Check if content inside f-string braces is a valid expression."""
    stripped = inner.strip()
    if not stripped:
        return False
    try:
        compile(stripped.split("!")[0].split(":")[0], "<fstring>", "eval")
        return True
    except SyntaxError:
        return False
