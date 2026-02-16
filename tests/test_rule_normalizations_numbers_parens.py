# Edited by Cursor: split from test_rule_normalizations (lintok; no new exclusions).
"""Tests for parens and ordinal normalizers (double_letter, single_letter, number_parens, ordinal)."""

from scripts.rule_normalizations import (
    normalize_double_letter_parens,
    normalize_number_parens,
    normalize_ordinal,
    normalize_single_letter_parens,
)


def test_normalize_double_letter_parens() -> None:
    """(ph) -> pee aych, (ab) -> ay bee."""
    assert normalize_double_letter_parens("(ph)") == ["pee aych"]
    assert normalize_double_letter_parens("(ab)") == ["ay bee"]


def test_normalize_single_letter_parens() -> None:
    """Single letter in parentheses -> letter pronunciation (lowercase)."""
    assert normalize_single_letter_parens("(a)") == ["ay"]
    assert normalize_single_letter_parens("(b)") == ["bee"]
    assert normalize_single_letter_parens("(c)") == ["cee"]
    assert normalize_single_letter_parens("(A)") == ["ay"]
    assert normalize_single_letter_parens("(z)") == ["zee"]


def test_normalize_single_letter_parens_with_spaces() -> None:
    """Single letter in parens with optional spaces -> letter pronunciation."""
    assert normalize_single_letter_parens("(a )") == ["ay"]
    assert normalize_single_letter_parens("( b)") == ["bee"]
    assert normalize_single_letter_parens("( c )") == ["cee"]


def test_normalize_single_letter_parens_invalid_returns_span() -> None:
    """Invalid spans (ab), () return list with original span."""
    assert normalize_single_letter_parens("(ab)") == ["(ab)"]
    assert normalize_single_letter_parens("()") == ["()"]


def test_normalize_number_parens() -> None:
    """Number in parentheses -> spoken number."""
    assert normalize_number_parens("(1)") == ["one"]
    assert normalize_number_parens("(5)") == ["five"]
    assert normalize_number_parens("(32)") == ["thirty two"]
    assert normalize_number_parens("(0)") == ["zero"]


def test_normalize_number_parens_with_spaces() -> None:
    """Number in parens with optional spaces -> spoken number."""
    assert normalize_number_parens("( 12)") == ["twelve"]
    assert normalize_number_parens("(32 )") == ["thirty two"]
    assert normalize_number_parens("( 5 )") == ["five"]


def test_normalize_number_parens_invalid_returns_span() -> None:
    """Invalid (1a), () return list with original span."""
    assert normalize_number_parens("(1a)") == ["(1a)"]
    assert normalize_number_parens("()") == ["()"]


def test_normalize_ordinal() -> None:
    """Ordinal span -> spoken ordinal."""
    assert normalize_ordinal("37th") == ["thirty seventh"]
    assert normalize_ordinal("3rd") == ["third"]
    assert normalize_ordinal("1st") == ["first"]
    assert normalize_ordinal("21st") == ["twenty first"]


def test_normalize_ordinal_invalid_returns_span() -> None:
    """Invalid ordinal (no suffix) returns list with original span."""
    assert normalize_ordinal("12") == ["12"]
