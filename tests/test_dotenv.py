"""End-to-end parse + serialize round-trip tests for dotenv-mini."""

import pytest

from dotenv_mini import DotenvError, dumps, loads, parse


class TestLoadsBasic:
    def test_empty(self):
        assert loads("") == {}

    def test_blank_lines_and_comments(self):
        text = "\n# comment\n\n# another\nFOO=bar\n"
        assert loads(text) == {"FOO": "bar"}

    def test_simple_assignment(self):
        assert loads("KEY=value") == {"KEY": "value"}

    def test_export_prefix(self):
        assert loads("export NAME=alice") == {"NAME": "alice"}

    def test_multiple_keys(self):
        assert loads("A=1\nB=2\nC=3\n") == {"A": "1", "B": "2", "C": "3"}

    def test_overwrite_repeated_key(self):
        assert loads("X=1\nX=2") == {"X": "2"}

    def test_whitespace_around_equals(self):
        # Whitespace before = is allowed and stripped from key.
        assert loads("KEY  =  value\n") == {"KEY": "value"}

    def test_empty_value(self):
        assert loads("KEY=\n") == {"KEY": ""}


class TestDoubleQuoted:
    def test_basic(self):
        assert loads('K="hello"') == {"K": "hello"}

    def test_with_spaces(self):
        assert loads('K="hello world"') == {"K": "hello world"}

    def test_escapes(self):
        assert loads(r'K="line1\nline2\ttab\"quote\\back"') == {
            "K": 'line1\nline2\ttab"quote\\back'
        }

    def test_unterminated(self):
        with pytest.raises(DotenvError):
            loads('K="not closed')

    def test_bad_escape(self):
        with pytest.raises(DotenvError):
            loads(r'K="\xFF"')


class TestSingleQuoted:
    def test_basic(self):
        assert loads("K='hello'") == {"K": "hello"}

    def test_no_escapes(self):
        # Single quotes are literal — \n stays as a backslash-n.
        assert loads(r"K='line1\nline2'") == {"K": r"line1\nline2"}

    def test_unterminated(self):
        with pytest.raises(DotenvError):
            loads("K='not closed")


class TestBare:
    def test_no_special(self):
        assert loads("K=value") == {"K": "value"}

    def test_strips_inline_comment(self):
        # A space-then-# starts a comment.
        assert loads("K=value # comment") == {"K": "value"}

    def test_keeps_internal_hash(self):
        # No space before # → still part of value.
        assert loads("K=value#nope") == {"K": "value#nope"}


class TestErrors:
    @pytest.mark.parametrize(
        "bad",
        [
            "no equals here",
            "1KEY=foo",       # invalid key (starts with digit)
            "KEY-WITH-DASH=x",  # invalid key (dash)
            "=missing-key",
        ],
    )
    def test_rejects_bad_lines(self, bad):
        with pytest.raises(DotenvError):
            loads(bad)


class TestDumps:
    def test_empty(self):
        assert dumps({}) == ""

    def test_basic(self):
        assert dumps({"K": "v"}) == "K=v\n"

    def test_quotes_when_needed(self):
        out = dumps({"K": "hello world"})
        assert out == 'K="hello world"\n'

    def test_escapes_newline(self):
        out = dumps({"K": "a\nb"})
        assert out == 'K="a\\nb"\n'

    def test_escapes_backslash_quote(self):
        out = dumps({"K": 'has "quote" and \\back'})
        assert out == 'K="has \\"quote\\" and \\\\back"\n'

    def test_quotes_dollar(self):
        # We don't interpolate $VAR, but we still quote to be safe — readers
        # that *do* interpolate would otherwise mangle this.
        assert dumps({"K": "$HOME"}) == 'K="$HOME"\n'

    def test_rejects_invalid_key(self):
        with pytest.raises(DotenvError):
            dumps({"1bad": "v"})

    def test_rejects_non_string_value(self):
        with pytest.raises(DotenvError):
            dumps({"K": 123})  # type: ignore[dict-item]


class TestRoundTrip:
    @pytest.mark.parametrize(
        "value",
        [
            "",
            "simple",
            "with spaces",
            "with\nnewline",
            "with\ttab",
            'with "quotes"',
            "with\\backslash",
            "$VAR  # not a comment",
            "  leading_and_trailing  ",
            "trailing#hash",
        ],
    )
    def test_round_trip(self, value):
        d = {"K": value}
        assert loads(dumps(d)) == d


class TestParseTriples:
    def test_yields_raw(self):
        triples = list(parse("FOO=bar\nBAZ=qux"))
        assert triples[0] == ("FOO", "bar", "FOO=bar")
        assert triples[1] == ("BAZ", "qux", "BAZ=qux")
