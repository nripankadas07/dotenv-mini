"""Core dotenv-mini implementation — strict ``.env`` parse/serialize.

Grammar
=======

Each non-empty, non-comment line is::

    [export ] KEY = VALUE

* ``KEY`` matches ``[A-Za-z_][A-Za-z0-9_]*`` — POSIX shell variable rules.
* Whitespace around the ``=`` is allowed and stripped.
* ``VALUE`` is one of:

  - empty (the key has no value, parsed as ``""``).
  - bare (``foo`` / ``hello world`` — trailing inline comments after a
    space-then-``#`` are stripped, internal ``#`` is kept).
  - single-quoted (``'literal text'`` — no escapes, content is verbatim
    until the closing quote).
  - double-quoted (``"text with \\n \\t \\\" \\\\"`` — supports
    ``\\n``, ``\\r``, ``\\t``, ``\\"``, ``\\\\``).

Comments start with ``#`` either on a blank line or after at least one
whitespace character following a bare value.

Round-trip
==========

:func:`dumps` chooses the safest quoting for each value:

* No special characters → bare.
* Contains ``\\n``, ``\\r``, ``\\t``, ``"``, or ``\\`` → double-quoted with
  escapes.
* Contains ``$``, ``#``, leading/trailing whitespace, or single quotes →
  double-quoted.

This guarantees ``loads(dumps(x)) == x`` for any dict whose values are
strings.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, Iterator, Mapping, Tuple, Union


__all__ = [
    "DotenvError",
    "dump",
    "dumps",
    "load",
    "loads",
    "parse",
]


_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DOUBLE_ESCAPES = {
    "n": "\n",
    "r": "\r",
    "t": "\t",
    '"': '"',
    "\\": "\\",
}


class DotenvError(ValueError):
    """Raised for any malformed input to the dotenv-mini API.

    Subclasses :class:`ValueError`.
    """


def parse(text: str) -> Iterator[Tuple[str, str, str]]:
    """Yield ``(key, value, raw_line)`` triples for each assignment in ``text``.

    Comments and blank lines are skipped.

    Raises:
        DotenvError: if a line is not a comment, blank, or a valid
        ``KEY=VALUE`` assignment.
    """
    if not isinstance(text, str):
        raise DotenvError(f"expected str, got {type(text).__name__}")
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export ") or stripped.startswith("export\t"):
            stripped = stripped[len("export"):].lstrip()

        eq = stripped.find("=")
        if eq < 0:
            raise DotenvError(
                f"line {lineno}: missing '=' in {raw_line!r}"
            )
        key = stripped[:eq].rstrip()
        rest = stripped[eq + 1:]
        if not _KEY_RE.match(key):
            raise DotenvError(
                f"line {lineno}: invalid key {key!r} in {raw_line!r}"
            )
        value = _parse_value(rest, lineno=lineno, raw_line=raw_line)
        yield key, value, raw_line


def loads(text: str) -> Dict[str, str]:
    """Parse a `.env` string into a dict.

    Later assignments overwrite earlier ones with the same key.
    """
    out: Dict[str, str] = {}
    for k, v, _ in parse(text):
        out[k] = v
    return out


def load(path: Union[str, Path]) -> Dict[str, str]:
    """Read a `.env` file and return a dict."""
    return loads(Path(path).read_text(encoding="utf-8"))


def dumps(items: Mapping[str, str]) -> str:
    """Serialize a mapping to `.env` text. Round-trip-safe with :func:`loads`."""
    if not isinstance(items, Mapping):
        raise DotenvError(f"expected Mapping, got {type(items).__name__}")
    lines = []
    for k, v in items.items():
        if not isinstance(k, str) or not _KEY_RE.match(k):
            raise DotenvError(f"invalid key {k!r}")
        if not isinstance(v, str):
            raise DotenvError(f"value for {k!r} must be str, got {type(v).__name__}")
        lines.append(f"{k}={_serialize_value(v)}")
    return "\n".join(lines) + ("\n" if lines else "")


def dump(items: Mapping[str, str], path: Union[str, Path]) -> None:
    """Write a mapping to a `.env` file path."""
    Path(path).write_text(dumps(items), encoding="utf-8")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_value(rest: str, *, lineno: int, raw_line: str) -> str:
    rest = rest.lstrip()
    if not rest:
        return ""
    if rest[0] == "'":
        end = rest.find("'", 1)
        if end < 0:
            raise DotenvError(
                f"line {lineno}: unterminated single-quoted value in {raw_line!r}"
            )
        # Anything after the closing quote must be whitespace or a comment.
        tail = rest[end + 1 :]
        _ensure_clean_tail(tail, lineno=lineno, raw_line=raw_line)
        return rest[1:end]
    if rest[0] == '"':
        out, end = _scan_double_quoted(rest, lineno=lineno, raw_line=raw_line)
        tail = rest[end + 1 :]
        _ensure_clean_tail(tail, lineno=lineno, raw_line=raw_line)
        return out
    # Bare value: stop at first whitespace-then-# (inline comment).
    i = 0
    while i < len(rest):
        if rest[i] in (" ", "\t") and i + 1 < len(rest) and "#" in rest[i + 1 :].lstrip()[:1]:
            break
        i += 1
    bare = rest[:i].rstrip() if i < len(rest) else rest.rstrip()
    return bare


def _scan_double_quoted(rest: str, *, lineno: int, raw_line: str) -> tuple[str, int]:
    out = []
    i = 1
    while i < len(rest):
        c = rest[i]
        if c == "\\":
            if i + 1 >= len(rest):
                raise DotenvError(
                    f"line {lineno}: trailing backslash in {raw_line!r}"
                )
            nxt = rest[i + 1]
            if nxt not in _DOUBLE_ESCAPES:
                raise DotenvError(
                    f"line {lineno}: bad escape \\{nxt} in {raw_line!r}"
                )
            out.append(_DOUBLE_ESCAPES[nxt])
            i += 2
            continue
        if c == '"':
            return "".join(out), i
        out.append(c)
        i += 1
    raise DotenvError(
        f"line {lineno}: unterminated double-quoted value in {raw_line!r}"
    )


def _ensure_clean_tail(tail: str, *, lineno: int, raw_line: str) -> None:
    s = tail.lstrip()
    if not s:
        return
    if s.startswith("#"):
        return
    raise DotenvError(
        f"line {lineno}: junk after closing quote: {s!r} in {raw_line!r}"
    )


_NEEDS_DOUBLE_QUOTE_RE = re.compile(r"[\n\r\t\\\"]")


def _serialize_value(v: str) -> str:
    if v == "":
        return ""
    needs_double = bool(_NEEDS_DOUBLE_QUOTE_RE.search(v))
    needs_quote_for_safety = (
        v != v.strip()
        or "#" in v
        or "$" in v
        or "'" in v
        or " " in v
        or "\t" in v
    )
    if needs_double:
        body = (
            v.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )
        return f'"{body}"'
    if needs_quote_for_safety:
        return f'"{v}"'
    return v
