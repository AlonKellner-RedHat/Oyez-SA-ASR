# Edited by Cursor: split from test_dictionary_loader (lintok; no new exclusions).
"""Tests for dictionary_loader: enchant and cascade (awareness, short, legal)."""

from pathlib import Path

import pytest

from scripts import _dictionary_impl_enchant
from scripts.dictionary_loader import (
    _CascadeChecker,
    _EnchantChecker,
    get_english_dictionary,
    set_allow_no_enchant,
    set_legal_dict_path_for_testing,
)
from tests.test_dictionary_loader_helpers import (
    _AWARENESS_REPORT_VALID_WORDS,
    _ENCHANT_INVALID_WORDS,
    _ENCHANT_VALID_WORDS,
)


def test_enchant_classifies_valid_words_and_rejects_typos() -> None:
    saved_allow = _dictionary_impl_enchant._ALLOW_NO_ENCHANT
    saved_cache = _dictionary_impl_enchant._CACHE
    try:
        _dictionary_impl_enchant._CACHE = None
        set_allow_no_enchant(False)
        try:
            dic = get_english_dictionary()
        except RuntimeError:
            pytest.skip(
                "enchant not available (install libenchant-2-2 enchant-2 aspell aspell-en)"
            )
        if not isinstance(dic, (_EnchantChecker, _CascadeChecker)):
            pytest.skip("enchant not available; using word-list fallback")
        for word in _ENCHANT_VALID_WORDS:
            assert word in dic, f"enchant should accept {word!r}"
        for word in _ENCHANT_INVALID_WORDS:
            assert word not in dic, f"enchant should reject {word!r}"
    finally:
        _dictionary_impl_enchant._ALLOW_NO_ENCHANT = saved_allow
        _dictionary_impl_enchant._CACHE = saved_cache


def test_enchant_classifies_awareness_report_words_as_valid() -> None:
    saved_allow = _dictionary_impl_enchant._ALLOW_NO_ENCHANT
    saved_cache = _dictionary_impl_enchant._CACHE
    try:
        _dictionary_impl_enchant._CACHE = None
        set_allow_no_enchant(False)
        try:
            dic = get_english_dictionary()
        except RuntimeError:
            pytest.skip("enchant not available")
        if not isinstance(dic, (_EnchantChecker, _CascadeChecker)):
            pytest.skip("enchant not available; using word-list fallback")
        missing = [w for w in _AWARENESS_REPORT_VALID_WORDS if w not in dic]
        if missing:
            pytest.skip(
                f"enchant (aspell-en) does not include: {missing[:3]!r}... "
                "Use a fuller dictionary for full coverage."
            )
        assert "ridicularity" not in dic
    finally:
        _dictionary_impl_enchant._ALLOW_NO_ENCHANT = saved_allow
        _dictionary_impl_enchant._CACHE = saved_cache


def test_cascade_accepts_awareness_report_words() -> None:
    saved_allow = _dictionary_impl_enchant._ALLOW_NO_ENCHANT
    saved_cache = _dictionary_impl_enchant._CACHE
    try:
        _dictionary_impl_enchant._CACHE = None
        set_allow_no_enchant(False)
        try:
            dic = get_english_dictionary()
        except RuntimeError:
            pytest.skip("enchant not available")
        for word in _AWARENESS_REPORT_VALID_WORDS:
            assert word in dic, f"cascade should accept {word!r}"
        assert "ridicularity" not in dic
    finally:
        _dictionary_impl_enchant._ALLOW_NO_ENCHANT = saved_allow
        _dictionary_impl_enchant._CACHE = saved_cache


def test_cascade_rejects_short_non_words() -> None:
    saved_allow = _dictionary_impl_enchant._ALLOW_NO_ENCHANT
    saved_cache = _dictionary_impl_enchant._CACHE
    try:
        _dictionary_impl_enchant._CACHE = None
        set_allow_no_enchant(False)
        try:
            dic = get_english_dictionary()
        except RuntimeError:
            pytest.skip("enchant not available")
        for word in ("xy", "zz", "qq"):
            assert word not in dic, f"cascade should reject short non-word {word!r}"
    finally:
        _dictionary_impl_enchant._ALLOW_NO_ENCHANT = saved_allow
        _dictionary_impl_enchant._CACHE = saved_cache


def test_cascade_accepts_legal_terms_when_legal_dict_present() -> None:
    import scripts.dictionary_loader as dmod  # noqa: PLC0415

    fixture_path = Path(__file__).resolve().parent / "fixtures" / "legal_words.txt"
    saved_path = getattr(dmod, "_legal_dict_path_override", None)
    saved_cache = _dictionary_impl_enchant._CACHE
    try:
        set_legal_dict_path_for_testing(fixture_path)
        _dictionary_impl_enchant._CACHE = None
        set_allow_no_enchant(False)
        try:
            dic = get_english_dictionary()
        except RuntimeError:
            pytest.skip("enchant not available")
        if not isinstance(dic, _CascadeChecker):
            pytest.skip("cascade not used")
        for word in (
            "affirmance",
            "vacatur",
            "habeas",
            "conclusory",
            "judicata",
            "amici",
        ):
            assert word in dic, f"cascade with legal dict should accept {word!r}"
    finally:
        set_legal_dict_path_for_testing(saved_path)
        _dictionary_impl_enchant._CACHE = saved_cache


def test_cascade_rejects_non_words_even_with_legal_dict() -> None:
    import scripts.dictionary_loader as dmod  # noqa: PLC0415

    fixture_path = Path(__file__).resolve().parent / "fixtures" / "legal_words.txt"
    saved_path = getattr(dmod, "_legal_dict_path_override", None)
    saved_cache = _dictionary_impl_enchant._CACHE
    try:
        set_legal_dict_path_for_testing(fixture_path)
        _dictionary_impl_enchant._CACHE = None
        set_allow_no_enchant(False)
        try:
            dic = get_english_dictionary()
        except RuntimeError:
            pytest.skip("enchant not available")
        for word in ("ridicularity", "xyzqq"):
            assert word not in dic, f"cascade should reject {word!r}"
    finally:
        set_legal_dict_path_for_testing(saved_path)
        _dictionary_impl_enchant._CACHE = saved_cache


def test_cascade_unchanged_when_legal_dict_missing() -> None:
    import scripts.dictionary_loader as dmod  # noqa: PLC0415

    saved_path = getattr(dmod, "_legal_dict_path_override", None)
    saved_cache = _dictionary_impl_enchant._CACHE
    try:
        set_legal_dict_path_for_testing(Path("/nonexistent/legal_words.txt"))
        _dictionary_impl_enchant._CACHE = None
        set_allow_no_enchant(False)
        try:
            dic = get_english_dictionary()
        except RuntimeError:
            pytest.skip("enchant not available")
        assert "ridicularity" not in dic
        for word in _AWARENESS_REPORT_VALID_WORDS:
            assert word in dic, (
                f"cascade should still accept {word!r} without legal file"
            )
    finally:
        set_legal_dict_path_for_testing(saved_path)
        _dictionary_impl_enchant._CACHE = saved_cache
