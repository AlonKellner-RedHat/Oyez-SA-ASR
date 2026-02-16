# Edited by Cursor: split from test_rule_normalizations (lintok; no new exclusions).
"""Tests for vote_tally, year, roman, percentage, decade, latin, leading_decimal."""

import pytest

from scripts.rule_normalizations import (
    latin_simple_map,
    normalize_decade,
    normalize_latin,
    normalize_leading_decimal,
    normalize_letter_dash_sequence,
    normalize_letter_roman_clause,
    normalize_percentage,
    normalize_roman_numeral,
    normalize_roman_parens,
    normalize_single_digit_valid_word,
    normalize_vote_tally,
    normalize_year,
)


def test_normalize_vote_tally() -> None:
    """Vote tally 9-0 -> spoken nine to zero."""
    assert normalize_vote_tally("9-0") == ["nine to zero"]
    assert normalize_vote_tally("7-2") == ["seven to two"]
    assert normalize_vote_tally("5-4") == ["five to four"]


def test_normalize_year() -> None:
    """Four-digit year -> spoken form."""
    assert normalize_year("1999") == ["nineteen ninety nine"]
    assert normalize_year("2020") == ["twenty twenty"]
    assert normalize_year("1954") == ["nineteen fifty four"]


def test_normalize_roman_numeral() -> None:
    """Roman numeral (II-XII) -> spoken number."""
    assert normalize_roman_numeral("VII") == ["seven"]
    assert normalize_roman_numeral("IV") == ["four"]
    assert normalize_roman_numeral("II") == ["two"]
    assert normalize_roman_numeral("XII") == ["twelve"]


def test_normalize_roman_parens() -> None:
    """Roman (i)-(xii) -> number word + letter forms."""
    ii_result = normalize_roman_parens("(ii)")
    assert set(ii_result) >= {"two", "eye eye", "double eye"}, ii_result
    iii_result = normalize_roman_parens("(iii)")
    assert set(iii_result) >= {"three", "eye eye eye", "triple eye"}, iii_result
    assert set(normalize_roman_parens("(iv)")) >= {"four", "eye vee"}
    assert set(normalize_roman_parens("(v)")) >= {"five", "vee"}
    assert set(normalize_roman_parens("(vii)")) >= {
        "seven",
        "vee eye eye",
        "vee double eye",
    }
    assert set(normalize_roman_parens("(vi)")) >= {"six", "vee eye"}
    assert set(normalize_roman_parens("(xii)")) >= {
        "twelve",
        "ex eye eye",
        "ex double eye",
    }
    assert "one" in normalize_roman_parens("(i)")
    assert "eye" in normalize_roman_parens("(i)")
    assert normalize_roman_parens("(xiii)") == ["(xiii)"]
    assert normalize_roman_parens("(1)") == ["(1)"]
    assert normalize_roman_parens("(abc)") == ["(abc)"]


def test_normalize_letter_roman_clause() -> None:
    """(C)(iii) -> cee three."""
    assert normalize_letter_roman_clause("(C)(iii)") == ["cee three"]
    assert normalize_letter_roman_clause("(c)(iii)") == ["cee three"]
    assert normalize_letter_roman_clause("(A)(i)") == ["ay one"]
    assert normalize_letter_roman_clause("(R)(v)") == ["ar five"]


def test_normalize_letter_dash_sequence() -> None:
    """(R-5) and R-5 -> ar five."""
    assert normalize_letter_dash_sequence("(R-5)") == ["ar five"]
    assert normalize_letter_dash_sequence("R-5") == ["ar five"]


def test_normalize_single_digit_valid_word() -> None:
    """Token with one digit: remainder valid word -> correction; else identity."""
    assert normalize_single_digit_valid_word("n4or") == ["nor"]
    assert normalize_single_digit_valid_word("eviden3ce") == ["evidence"]
    assert normalize_single_digit_valid_word("9put") == ["put"]
    assert normalize_single_digit_valid_word("x7yz") == ["x7yz"]


def test_normalize_percentage() -> None:
    """Percentage span -> spoken form."""
    assert normalize_percentage("50%") == ["fifty percent"]
    assert normalize_percentage("25 percent") == ["twenty five percent"]
    assert normalize_percentage("100%") == ["one hundred percent"]


def test_normalize_decade() -> None:
    """Decade span (1980s, 20s) -> spoken form."""
    assert normalize_decade("1860s") == ["eighteen sixties"]
    assert normalize_decade("1980s") == ["nineteen eighties"]
    assert normalize_decade("1930s") == ["nineteen thirties"]
    assert normalize_decade("2010s") == ["twenty tens"]
    assert normalize_decade("2020s") == ["twenty twenties"]
    assert normalize_decade("20s") == ["twenties"]
    assert normalize_decade("50s") == ["fifties"]
    assert normalize_decade("10s") == ["tens"]


def test_normalize_vote_tally_invalid_returns_empty_or_unchanged() -> None:
    """Invalid vote tally format does not crash."""
    result = normalize_vote_tally("12-3")
    assert isinstance(result, list)
    assert len(result) >= 1


def test_latin_simple_map() -> None:
    """Latin accented chars map to ASCII (NFD strip)."""
    assert latin_simple_map("café") == "cafe"
    assert latin_simple_map("naïve") == "naive"
    assert latin_simple_map("Espańola") == "Espanola"
    assert latin_simple_map("vis-à-vis") == "vis-a-vis"


@pytest.mark.slow
def test_normalize_latin_returns_list_of_dicts_with_method() -> None:
    """normalize_latin returns list of {text, method}; first is simple_map."""
    result = normalize_latin("café")
    assert isinstance(result, list)
    assert len(result) >= 1
    first = result[0]
    assert "text" in first and "method" in first
    assert first["method"] == "simple_map"
    assert first["text"] == "cafe"
    for item in result:
        assert "text" in item and "method" in item


def test_normalize_leading_decimal() -> None:
    """.06 -> point oh six; .31 has point three one and point thirty one."""
    assert normalize_leading_decimal(".06") == ["point oh six"]
    result_31 = normalize_leading_decimal(".31")
    assert "point three one" in result_31 and "point thirty one" in result_31
    result_172 = normalize_leading_decimal(".172")
    assert "point one seven two" in result_172
    assert "point one seventy two" in result_172
