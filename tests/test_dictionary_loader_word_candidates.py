# Edited by Cursor: split from test_dictionary_loader (lintok; no new exclusions).
"""Tests for dictionary_loader: _word_candidates."""

from scripts.dictionary_loader import _word_candidates


def test_word_candidates_includes_new_awareness_bases() -> None:
    assert "indigent" in _word_candidates("indigency")
    assert "administrable" in _word_candidates("administrability")
    assert "discriminatory" in _word_candidates("discriminatorily")
    cand_arb = _word_candidates("arbitrability")
    assert "arbitrable" in cand_arb and "arbiter" in cand_arb
    assert "enplane" in _word_candidates("enplanement")
    assert "routinize" in _word_candidates("routinization")
    assert "dischargeable" in _word_candidates("dischargability")


def test_word_candidates_includes_derived_bases() -> None:
    assert "exclude" in _word_candidates("excludable")
    assert "rehabilitate" in _word_candidates("rehabilitatable")
    cand_unobj = _word_candidates("unobjected")
    assert "objected" in cand_unobj or "object" in cand_unobj
    cand_unpat = _word_candidates("unpatentable")
    assert "patent" in cand_unpat or "patentable" in cand_unpat
    assert "clear" in _word_candidates("preclear")


def test_word_candidates_includes_non_prefix() -> None:
    assert "dischargeability" in _word_candidates("nondischargeability")


def test_word_candidates_includes_mal_prefix() -> None:
    assert "distribute" in _word_candidates("maldistribute")


def test_word_candidates_includes_ance_suffix() -> None:
    assert "vibrant" in _word_candidates("vibrance")


def test_word_candidates_includes_ary_suffix() -> None:
    assert "preclusion" in _word_candidates("preclusionary")


def test_word_candidates_includes_ize_ise_variant() -> None:
    assert "merchandise" in _word_candidates("merchandize")


def test_word_candidates_includes_ation_suffix() -> None:
    assert "analyze" in _word_candidates("analyzation")


def test_word_candidates_includes_ably_suffix() -> None:
    assert "irrebuttable" in _word_candidates("irrebuttably")


def test_word_candidates_includes_atize_suffix() -> None:
    assert "illegitimate" in _word_candidates("illegitimatize")
