# Edited by Cursor: split from test_dictionary_loader (lintok; no new exclusions).
"""Tests for dictionary_loader: is_valid_word and is_valid_word_for_rules."""

import pytest

from scripts import _dictionary_impl_enchant
from scripts.dictionary_loader import (
    _CascadeChecker,
    get_english_dictionary,
    is_valid_word,
    is_valid_word_for_rules,
    set_allow_no_enchant,
)


def test_is_valid_word_frozenset_stem() -> None:
    dic = frozenset({"accommod", "that", "is"})
    assert "accommodation" not in dic
    assert is_valid_word("accommodation", dic) is True
    assert is_valid_word("xyzqq", dic) is False


def test_is_valid_word_cascade_unchanged() -> None:
    saved_cache = _dictionary_impl_enchant._CACHE
    try:
        _dictionary_impl_enchant._CACHE = None
        set_allow_no_enchant(True)
        checker = get_english_dictionary()
        if not isinstance(checker, _CascadeChecker):
            pytest.skip("cascade not used (fallback frozenset)")
        for w in ("accommodation", "ridicularity"):
            assert is_valid_word(w, checker) == (w in checker), w
    finally:
        _dictionary_impl_enchant._CACHE = saved_cache


def test_is_valid_word_for_rules_single_letter_q_invalid() -> None:
    dic = frozenset({"q"})
    assert is_valid_word_for_rules("q", dic) is False
    assert is_valid_word("q", dic) is True


def test_is_valid_word_for_rules_single_letter_a_i_v_x_valid() -> None:
    dic = frozenset({"a", "i", "v", "x"})
    assert is_valid_word_for_rules("a", dic) is True
    assert is_valid_word_for_rules("i", dic) is True
    assert is_valid_word_for_rules("v", dic) is True
    assert is_valid_word_for_rules("x", dic) is True


def test_is_valid_word_for_rules_multi_letter_follows_dictionary() -> None:
    dic = frozenset({"the"})
    assert is_valid_word_for_rules("the", dic) is True
    assert is_valid_word_for_rules("The", dic) is True
    assert is_valid_word_for_rules("xyz", dic) is False
