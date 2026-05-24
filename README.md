# dotenv-mini

A strict, predictable `.env` reader/writer for Python 3.10+. Zero dependencies.

* Round-trip safe: `loads(dumps(d)) == d` for every dict of strings.
* No `$VAR` / `${VAR}` interpolation — values are always literal.
* Strict grammar — malformed lines raise `DotenvError`, never silently swallowed.
* Single-quoted values are verbatim. Double-quoted values support
  `\n`, `\r`, `\t`, `\"`, `\\`.

## Install

```bash
python -m pip install -e .
```

Or from a clone:

```bash
pip install -e .
```

## Quick start

```python
from dotenv_mini import loads, dumps, load, dump

d = loads("""
# Database
DB_HOST=localhost
DB_PORT=5432
DB_PASS="se cr et"
""")
# {'DB_HOST': 'localhost', 'DB_PORT': '5432', 'DB_PASS': 'se cr et'}

print(dumps({"NAME": "alice", "GREETING": "hello\nworld"}))
# NAME=alice
# GREETING="hello\nworld"
```

## API reference

| Symbol | Purpose |
|---|---|
| `loads(text)` | Parse `.env` text → dict. |
| `dumps(d)` | Serialize dict → `.env` text. |
| `load(path)` | Read file at `path`, return dict. |
| `dump(d, path)` | Write dict to file at `path`. |
| `parse(text)` | Yield `(key, value, raw_line)` tuples. |
| `DotenvError` | `ValueError` subclass for any malformed input. |

## Grammar

```
line       := blank | comment | assignment
comment    := whitespace* '#' anything
assignment := whitespace* ['export' whitespace+] KEY whitespace* '=' value
KEY        := [A-Za-z_][A-Za-z0-9_]*
value      := '' | bare | single-quoted | double-quoted
```

A trailing inline comment after a *bare* value requires at least one space
before the `#`.

## Running tests

```bash
pip install -e ".[dev]"
pytest -q
```

## License

MIT.
