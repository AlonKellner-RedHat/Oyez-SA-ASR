# Edited by Cursor: split from test_dictionary_loader (lintok; no new exclusions).
"""Tests for dictionary_loader: cascade Latin, derived, word_candidates stem."""

from pathlib import Path

import pytest

from scripts import _dictionary_impl_enchant
from scripts.dictionary_loader import (
    _CascadeChecker,
    _word_candidates,
    get_english_dictionary,
    set_allow_no_enchant,
    set_legal_dict_path_for_testing,
)
from tests.test_dictionary_loader_helpers import (
    _CASCADE_DERIVED_POSSESSIVE_WORDS,
    _CASCADE_NEW_AWARENESS_FORMS,
)


def test_cascade_accepts_latin_via_enchant_when_la_dict_installed() -> None:
    try:
        import enchant  # noqa: PLC0415

        enchant.Dict("la")
    except Exception:
        pytest.skip("enchant Latin dictionary (la) not installed")
    import scripts.dictionary_loader as dmod  # noqa: PLC0415

    saved_path = getattr(dmod, "_legal_dict_path_override", None)
    saved_cache = _dictionary_impl_enchant._CACHE
    try:
        set_legal_dict_path_for_testing(None)
        _dictionary_impl_enchant._CACHE = None
        set_allow_no_enchant(False)
        dic = get_english_dictionary()
        for word in ("habeas", "amici", "certiorari"):
            assert word in dic, f"cascade with Latin dict should accept {word!r}"
    finally:
        set_legal_dict_path_for_testing(saved_path)
        _dictionary_impl_enchant._CACHE = saved_cache


def test_cascade_accepts_derived_form_when_base_in_legal() -> None:
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
        assert "retrospectivity" in dic
    finally:
        set_legal_dict_path_for_testing(saved_path)
        _dictionary_impl_enchant._CACHE = saved_cache


def test_word_candidates_includes_stem_and_morphy() -> None:
    candidates_retro = _word_candidates("retrospectivity")
    assert "retrospective" in candidates_retro or "retrospect" in candidates_retro
    candidates_coerc = _word_candidates("coercively")
    assert (
        "coercive" in candidates_coerc
        or "coerc" in candidates_coerc
        or "coerciv" in candidates_coerc
    )


def test_cascade_still_rejects_typos() -> None:
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
        assert "ridicularity" not in dic
        assert "proecedural" not in dic
    finally:
        set_legal_dict_path_for_testing(saved_path)
        _dictionary_impl_enchant._CACHE = saved_cache


def test_cascade_accepts_derived_and_possessive_awareness_words() -> None:
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
        for word in _CASCADE_DERIVED_POSSESSIVE_WORDS:
            assert word in dic
        for word in _CASCADE_NEW_AWARENESS_FORMS:
            assert word in dic
    finally:
        set_legal_dict_path_for_testing(saved_path)
        _dictionary_impl_enchant._CACHE = saved_cache


def test_cascade_accepts_arbitrability_against_actual_dictionary() -> None:
    import scripts.dictionary_loader as dmod  # noqa: PLC0415

    saved_path = getattr(dmod, "_legal_dict_path_override", None)
    saved_cache = _dictionary_impl_enchant._CACHE
    try:
        set_legal_dict_path_for_testing(None)
        _dictionary_impl_enchant._CACHE = None
        set_allow_no_enchant(False)
        try:
            dic = get_english_dictionary()
        except RuntimeError:
            pytest.skip("enchant not available")
        if not isinstance(dic, _CascadeChecker):
            pytest.skip("cascade not used")
        if "arbitrability" not in dic:
            pytest.skip(
                "arbitrability not accepted (arbiter may be missing from system dictionary)"
            )
        assert "arbitrability" in dic
    finally:
        set_legal_dict_path_for_testing(saved_path)
        _dictionary_impl_enchant._CACHE = saved_cache
