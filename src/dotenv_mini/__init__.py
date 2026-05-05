"""dotenv-mini — strict, predictable .env reader/writer for Python.

Public API:

* :func:`loads`     — parse a string of `.env`-formatted text into a dict.
* :func:`dumps`     — serialize a dict back into `.env` text (round-trip safe).
* :func:`load`      — read a file path and return a dict.
* :func:`dump`      — write a dict to a file path.
* :func:`parse`     — parse and yield ``(key, value, raw_line)`` triples.
* :class:`DotenvError` — raised on any malformed input (ValueError subclass).

Non-goals (kept out on purpose):

* No ``$VAR`` / ``${VAR}`` interpolation — values are literal text.
* No ``export`` keyword stripping (allowed but not required).
* No multi-line values without explicit quoting.
"""

from __future__ import annotations

from ._core import DotenvError, dump, dumps, load, loads, parse

__all__ = [
    "DotenvError",
    "dump",
    "dumps",
    "load",
    "loads",
    "parse",
]

__version__ = "0.1.0"
