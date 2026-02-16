# Edited by Cursor: split from test_rule_normalizations (lintok; no new exclusions).
"""Tests for concatenated_word_split, single_digit_valid_word scan, is_token_invalid_for_merge."""

from unittest.mock import patch

from scripts.dictionary_loader import set_allow_no_enchant
from scripts.rule_normalizations import normalize_concatenated_word_split
from scripts.rule_normalizations.concatenated_word_scan import (
    scan_turn_concatenated_word,
)
from scripts.rule_normalizations.single_digit_valid_word_scan import (
    scan_turn_single_digit_valid_word,
)
from scripts.rule_normalizations.split_word_merge_scan import (
    is_token_invalid_for_merge,
)


def test_normalize_concatenated_word_split() -> None:
    """Token not in dictionary that splits into two valid words -> left right."""
    set_allow_no_enchant(True)
    assert normalize_concatenated_word_split("befair") == ["be fair"]
    assert normalize_concatenated_word_split("supremecourt") == ["supreme court"]
    assert normalize_concatenated_word_split("the18th") == ["the 18th"]
    assert normalize_concatenated_word_split("June22nd") == ["June 22nd"]
    assert normalize_concatenated_word_split("the") == ["the"]
    assert normalize_concatenated_word_split("xyzqq") == ["xyzqq"]


def test_scan_turn_concatenated_word_single_letter_q_in_dic_not_valid() -> None:
    """Single letter q in dictionary invalid for rules: no split for q or qxyz."""
    with patch(
        "scripts.rule_normalizations.concatenated_word_scan.get_english_dictionary",
        return_value=frozenset({"q"}),
    ):
        out = scan_turn_concatenated_word("q", "/p.json")
    assert len(out) == 0

    with patch(
        "scripts.rule_normalizations.concatenated_word_scan.get_english_dictionary",
        return_value=frozenset({"q", "xyz"}),
    ):
        out = scan_turn_concatenated_word("qxyz", "/p.json")
    assert len(out) == 0


def test_scan_turn_single_digit_valid_word_remainder_q_not_emitted() -> None:
    """Remainder q invalid for rules: 1q must not emit."""
    with patch(
        "scripts.rule_normalizations.single_digit_valid_word_scan.get_single_digit_valid_words",
        return_value=frozenset({"q"}),
    ):
        out = scan_turn_single_digit_valid_word("1q", "/p.json")
    assert len(out) == 0


def test_is_token_invalid_for_merge_single_letter_invalid() -> None:
    """Single letters t, s, n, w invalid for merge even when in dictionary."""
    dic = frozenset({"t", "s", "n", "w"})
    assert is_token_invalid_for_merge("t", dic) is True
    assert is_token_invalid_for_merge("s", dic) is True
    assert is_token_invalid_for_merge("n", dic) is True
    assert is_token_invalid_for_merge("w", dic) is True


def test_is_token_invalid_for_merge_single_letter_allowed() -> None:
    """Single letters a, i, v, x valid for merge when in dictionary."""
    dic = frozenset({"a", "i", "v", "x"})
    assert is_token_invalid_for_merge("a", dic) is False
    assert is_token_invalid_for_merge("i", dic) is False
    assert is_token_invalid_for_merge("v", dic) is False
    assert is_token_invalid_for_merge("x", dic) is False


def test_is_token_invalid_for_merge_non_single_letter() -> None:
    """Non-single-letter tokens: in dic -> valid, not in dic -> invalid."""
    dic = frozenset({"the", "word"})
    assert is_token_invalid_for_merge("the", dic) is False
    assert is_token_invalid_for_merge("word", dic) is False
    assert is_token_invalid_for_merge("xyz", dic) is True


def test_is_token_invalid_for_merge_single_letter_j_b_invalid_a_valid() -> None:
    """Regression: j and b invalid for merge; a valid when in dictionary."""
    dic = frozenset({"j", "b", "a"})
    assert is_token_invalid_for_merge("j", dic) is True
    assert is_token_invalid_for_merge("b", dic) is True
    assert is_token_invalid_for_merge("a", dic) is False
