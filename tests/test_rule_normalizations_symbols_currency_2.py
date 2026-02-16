# Edited by Cursor: split from test_rule_normalizations (lintok; no new exclusions).
"""Tests for common_acronym, time_of_day, special_currency, dual_notation, half_number, dash, symbol_*, currency, editorial_dollar."""

from scripts.rule_normalizations import (
    normalize_common_acronym,
    normalize_currency,
    normalize_dash,
    normalize_dual_notation,
    normalize_editorial_dollar,
    normalize_half_number,
    normalize_special_currency,
    normalize_symbol_copyright,
    normalize_symbol_pound,
    normalize_symbol_section,
    normalize_symbol_section_ref,
    normalize_time_of_day,
)


def test_normalize_common_acronym() -> None:
    """PhD -> pee aych dee (letter-by-letter)."""
    assert normalize_common_acronym("PhD") == ["pee aych dee"]


def test_normalize_time_of_day() -> None:
    """8:40->eight forty; 1:00 and 6:00 have short and oh oh form."""
    assert normalize_time_of_day("8:40") == ["eight forty"]
    assert "one" in normalize_time_of_day(
        "1:00"
    ) and "one oh oh" in normalize_time_of_day("1:00")
    assert "six" in normalize_time_of_day(
        "6:00"
    ) and "six oh oh" in normalize_time_of_day("6:00")
    assert normalize_time_of_day("5:15") == ["five fifteen"]
    assert normalize_time_of_day("12:45") == ["twelve forty five"]


def test_normalize_special_currency() -> None:
    """[$] 3 billion / $ 21 hundred -> three billion dollars; etc."""
    result_billion = normalize_special_currency("$ 3 billion")
    assert (
        "three billion dollars" in result_billion
        and "three billion dollar" in result_billion
    )
    result_hundred = normalize_special_currency("$ 21 hundred")
    assert (
        "twenty one hundred dollars" in result_hundred
        and "twenty one hundred dollar" in result_hundred
    )
    result_raw = normalize_special_currency("[$] 43,000")
    assert "forty three thousand dollars" in result_raw
    result_86 = normalize_special_currency("[$] 86,000")
    assert "eighty six thousand dollars" in result_86
    result_dollars = normalize_special_currency("[dollars] 5,000")
    assert "five thousand dollars" in result_dollars
    assert "five thousand dollar" in result_dollars
    result_500 = normalize_special_currency("[dollars] 500")
    assert "five hundred dollars" in result_500


def test_normalize_dual_notation() -> None:
    """<thirty> [= 30] -> thirty; <fifty-nine e@l> [= 59(e)] contains fifty-nine ee."""
    assert normalize_dual_notation("<thirty> [= 30]") == ["thirty"]
    result_59 = normalize_dual_notation("<fifty-nine e@l> [= 59(e)]")
    assert any("fifty-nine ee" in r for r in result_59)
    result_v = normalize_dual_notation("<v@l> [= v.]")
    assert "versus" in result_v and "vee" in result_v


def test_normalize_dual_notation_variants() -> None:
    """Dual notation variants: <X> [81-523], [<X>] -> angle content only."""
    result = normalize_dual_notation("<Eighty one five twenty three> [81-523]")
    assert any("Eighty one five twenty three" in r for r in result)
    result2 = normalize_dual_notation("<eighteen thousand dollars > [ = $ 18,000]")
    assert any("eighteen thousand dollars" in r for r in result2)
    result3 = normalize_dual_notation("[<twenty-three oh five point one five>]")
    assert any("twenty-three oh five point one five" in r for r in result3)


def test_normalize_half_number() -> None:
    """12½% / 12 ½ % -> twelve and a half percent; etc."""
    assert "twelve and a half percent" in normalize_half_number("12½%")
    assert "twelve and a half percent" in normalize_half_number("12 ½ %")
    assert "nineteen and a half years" in normalize_half_number("19 ½ years")
    assert "eighteen and a half times" in normalize_half_number("18 ½ times")


def test_normalize_dash() -> None:
    """Non-standard dash or dash sequence -> single standard dash."""
    assert normalize_dash("\u2013") == ["-"]
    assert normalize_dash("\u2014") == ["-"]
    assert normalize_dash("--") == ["-"]
    assert normalize_dash("---") == ["-"]
    assert normalize_dash("\u2013\u2014") == ["-"]
    assert normalize_dash("\u22c5") == ["-"]
    assert normalize_dash("\u2026") == ["-"]
    assert normalize_dash("...") == ["-"]
    assert normalize_dash("(.)") == ["-"]


def test_normalize_symbol_section() -> None:
    """Standalone § -> section."""
    assert normalize_symbol_section("\u00a7") == ["section"]


def test_normalize_symbol_section_ref() -> None:
    """§1519 -> section fifteen nineteen."""
    result = normalize_symbol_section_ref("\u00a71519")
    assert "section fifteen nineteen" in result


def test_normalize_symbol_copyright() -> None:
    """© -> copyright."""
    assert normalize_symbol_copyright("\u00a9") == ["copyright"]


def test_normalize_symbol_pound() -> None:
    """Standalone £ -> pound."""
    assert normalize_symbol_pound("\u00a3") == ["pound"]


def test_normalize_currency() -> None:
    """Currency always returns both plural and singular."""
    assert normalize_currency("£40") == ["forty pounds", "forty pound"]
    assert normalize_currency("$50") == ["fifty dollars", "fifty dollar"]
    assert normalize_currency("$1") == ["one dollars", "one dollar"]


def test_normalize_editorial_dollar() -> None:
    """$<forty-two thousand> [= 42,000] -> forty-two thousand dollars/dollar."""
    span = "$<forty-two thousand> [= 42,000]"
    result = normalize_editorial_dollar(span)
    assert "forty-two thousand dollars" in result
    assert "forty-two thousand dollar" in result
