# Edited by Cursor: split from test_rule_normalizations (lintok; no new exclusions).
"""Tests for split_word_merge scan and normalizer."""

from typing import Any
from unittest.mock import patch

from scripts.dictionary_loader import set_allow_no_enchant
from scripts.rule_normalizations import normalize_split_word_merge
from scripts.rule_normalizations.split_word_merge_scan import (
    scan_turn_split_word_merge,
)


def _patch_dictionary(dic: frozenset[str]) -> Any:
    """Context manager to patch get_english_dictionary for scanner tests. Edited by Cursor."""
    return patch(
        "scripts.rule_normalizations.split_word_merge_scan.get_english_dictionary",
        return_value=dic,
    )


def test_scan_turn_split_word_merge_single_letter_in_dictionary() -> None:
    """'t' in dictionary still triggers merge: 't he is' -> emit span containing 't he'."""
    set_allow_no_enchant(True)
    with _patch_dictionary(frozenset({"t", "the", "is"})):
        out = scan_turn_split_word_merge("t he is", "/path.json")
    spans = [r[2] for r in out]
    assert any("t he" in s for s in spans)


def test_normalize_split_word_merge_t_he_with_t_in_dictionary() -> None:
    """'t he' -> 'the' even when 't' is in dictionary (single letter invalid for merge)."""
    set_allow_no_enchant(True)
    with patch(
        "scripts.dictionary_loader.get_english_dictionary",
        return_value=frozenset({"t", "the"}),
    ):
        out = normalize_split_word_merge("t he")
    assert out == [{"text": "the"}]


def test_normalize_split_word_merge_don_t_apostrophe() -> None:
    """'don t' -> 'don't' when dictionary has 'don't' (apostrophe form)."""
    set_allow_no_enchant(True)
    with patch(
        "scripts.dictionary_loader.get_english_dictionary",
        return_value=frozenset({"don't", "i", "think"}),
    ):
        out = normalize_split_word_merge("don t")
    assert out == [{"text": "don't"}]


def test_normalize_split_word_merge_prefer_apostrophe_when_both_valid() -> None:
    """'don t' -> 'don't' (prefer apostrophe) when both 'dont' and 'don't' in dictionary."""
    set_allow_no_enchant(True)
    with patch(
        "scripts.dictionary_loader.get_english_dictionary",
        return_value=frozenset({"dont", "don't"}),
    ):
        out = normalize_split_word_merge("don t")
    assert out == [{"text": "don't"}]


def test_scan_turn_split_word_merge_don_t_apostrophe() -> None:
    """'I don t think' with 'don't' in dictionary -> scan emits span containing 'don t'."""
    set_allow_no_enchant(True)
    with _patch_dictionary(frozenset({"i", "don't", "think"})):
        out = scan_turn_split_word_merge("I don t think", "/path.json")
    spans = [r[2] for r in out]
    assert any("don t" in s for s in spans)


def test_normalize_split_word_merge() -> None:
    """Span 'r ight.' -> single correction merged word 'right'."""
    assert normalize_split_word_merge("r ight.") == [{"text": "right"}]
    assert normalize_split_word_merge("right t.") == [{"text": "right t."}]


def test_normalize_split_word_merge_thank_s_man() -> None:
    """Full span 'thank s man' -> correction 'thanks man' (only thank+s valid)."""
    set_allow_no_enchant(True)
    dic = frozenset({"thanks", "man"})
    with patch(
        "scripts.dictionary_loader.get_english_dictionary",
        return_value=dic,
    ):
        out = normalize_split_word_merge("thank s man")
    assert out == [{"text": "thanks man"}]


def test_scan_turn_split_word_merge() -> None:
    """Invalid token with valid merge -> at least one result with span 'r ight.' and start 8."""
    set_allow_no_enchant(True)
    with _patch_dictionary(frozenset({"right", "that", "is"})):
        out = scan_turn_split_word_merge("That is r ight.", "/path.json")
    r_ight_results = [r for r in out if r[2] == "r ight."]
    assert len(r_ight_results) >= 1
    rule_id, start_index, _span, path_str = r_ight_results[0]
    assert rule_id == "split_word_merge"
    assert start_index == 8
    assert path_str == "/path.json"


def test_scan_turn_split_word_merge_thank_s_man() -> None:
    """Invalid 's' with valid merge (thank s -> thanks): one result with full span 'thank s man'."""
    set_allow_no_enchant(True)
    with _patch_dictionary(frozenset({"thanks", "man"})):
        out = scan_turn_split_word_merge("thank s man", "/path.json")
    assert len(out) == 1
    rule_id, start_index, span, path_str = out[0]
    assert rule_id == "split_word_merge"
    assert span == "thank s man"
    assert start_index == 0
    assert path_str == "/path.json"


def test_scan_turn_split_word_merge_c_some() -> None:
    """Invalid 'c' with valid merge (c some -> come): full span 'c some'."""
    set_allow_no_enchant(True)
    with _patch_dictionary(frozenset({"that", "is", "come"})):
        out = scan_turn_split_word_merge("That is c ome", "/path.json")
    come_results = [r for r in out if r[2] == "c ome" or "c ome" in r[2]]
    assert len(come_results) >= 1
    _, start_index, span, _ = come_results[0]
    assert start_index == 5
    assert "c ome" in span


def test_scan_turn_split_word_merge_first_token_invalid() -> None:
    """First token invalid: full span is two tokens only (merge with next)."""
    set_allow_no_enchant(True)
    with _patch_dictionary(frozenset({"come", "here"})):
        out = scan_turn_split_word_merge("c ome here", "/path.json")
    assert len(out) >= 1
    spans = [r[2] for r in out]
    assert "c ome" in spans or any("c ome" in s for s in spans)


def test_scan_turn_split_word_merge_neither_merge_valid() -> None:
    """Invalid word with neither prev+curr nor curr+next valid -> no emit for that token."""
    set_allow_no_enchant(True)
    with _patch_dictionary(frozenset({"the", "quick", "brown"})):
        out = scan_turn_split_word_merge("the x y brown", "/path.json")
    assert len(out) == 0
