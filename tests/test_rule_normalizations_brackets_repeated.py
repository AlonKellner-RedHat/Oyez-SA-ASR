# Edited by Cursor: split from test_rule_normalizations (lintok; no new exclusions).
"""Tests for repeated_word_accept and global_repeated_word_accept scans/normalizers."""

from collections import Counter
from unittest.mock import patch

from scripts.rule_normalizations import (
    normalize_global_repeated_word_accept,
    normalize_repeated_word_accept,
)
from scripts.rule_normalizations.global_repeated_word_accept_scan import (
    scan_batch_global_repeated_word_accept,
)
from scripts.rule_normalizations.repeated_word_accept_scan import (
    scan_batch_repeated_word_accept,
)


def test_scan_batch_repeated_word_accept_two_occurrences_emitted() -> None:
    """Invalid foo twice -> 2 results for foo, 0 for bar."""
    full_text = "foo foo\nbar"
    path_str = "/path.json"
    turn_boundaries = [(0, 7, path_str, 0), (8, 11, path_str, 1)]
    with patch(
        "scripts.rule_normalizations.repeated_word_accept_scan.get_english_dictionary",
        return_value=frozenset(),
    ):
        out = scan_batch_repeated_word_accept(full_text, path_str, turn_boundaries)
    foo_results = [r for r in out if r[3] == "foo"]
    bar_results = [r for r in out if r[3] == "bar"]
    assert len(foo_results) == 2
    assert len(bar_results) == 0
    assert all(r[0] == "repeated_word_accept" for r in foo_results)


def test_scan_batch_repeated_word_accept_case_insensitive() -> None:
    """Foo and foo count as same word; both emitted when invalid."""
    full_text = "Foo foo"
    path_str = "/p.json"
    turn_boundaries = [(0, 7, path_str, 0)]
    with patch(
        "scripts.rule_normalizations.repeated_word_accept_scan.get_english_dictionary",
        return_value=frozenset(),
    ):
        out = scan_batch_repeated_word_accept(full_text, path_str, turn_boundaries)
    assert len(out) == 2
    assert {r[3] for r in out} == {"Foo", "foo"}


def test_scan_batch_repeated_word_accept_valid_words_not_emitted() -> None:
    """Valid words not emitted even when repeated."""
    full_text = "the the xyz xyz"
    path_str = "/p.json"
    turn_boundaries = [(0, 15, path_str, 0)]
    with patch(
        "scripts.rule_normalizations.repeated_word_accept_scan.get_english_dictionary",
        return_value=frozenset({"the"}),
    ):
        out = scan_batch_repeated_word_accept(full_text, path_str, turn_boundaries)
    the_results = [r for r in out if r[3] == "the"]
    xyz_results = [r for r in out if r[3] == "xyz"]
    assert len(the_results) == 0
    assert len(xyz_results) == 2


def test_scan_batch_repeated_word_accept_single_letter_q_emitted() -> None:
    """Single letter q in dictionary invalid for rules; q q emits two."""
    full_text = "q q"
    path_str = "/p.json"
    turn_boundaries = [(0, 3, path_str, 0)]
    with patch(
        "scripts.rule_normalizations.repeated_word_accept_scan.get_english_dictionary",
        return_value=frozenset({"q"}),
    ):
        out = scan_batch_repeated_word_accept(full_text, path_str, turn_boundaries)
    q_results = [r for r in out if r[3] == "q"]
    assert len(q_results) == 2
    assert all(r[0] == "repeated_word_accept" for r in q_results)


def test_normalize_repeated_word_accept() -> None:
    """repeated_word_accept normalizer returns identity."""
    assert normalize_repeated_word_accept("anything") == ["anything"]


def test_scan_batch_global_repeated_word_accept_three_letters_three_global() -> None:
    """Invalid xyz with global count 3 emitted; ab (2 letters) not emitted."""
    full_text = "xyz xyz ab"
    path_str = "/p.json"
    turn_boundaries = [(0, 11, path_str, 0)]
    global_counts: Counter[str] = Counter({"xyz": 3, "ab": 2})
    with patch(
        "scripts.rule_normalizations.global_repeated_word_accept_scan.get_english_dictionary",
        return_value=frozenset(),
    ):
        out = scan_batch_global_repeated_word_accept(
            full_text, path_str, turn_boundaries, global_counts
        )
    xyz_results = [r for r in out if r[3] == "xyz"]
    ab_results = [r for r in out if r[3] == "ab"]
    assert len(xyz_results) == 2
    assert len(ab_results) == 0


def test_scan_batch_global_repeated_word_accept_min_three_global() -> None:
    """Invalid 3+ letter word with global count < 3 not emitted."""
    full_text = "secuitcus"
    path_str = "/p.json"
    turn_boundaries = [(0, 9, path_str, 0)]
    global_counts: Counter[str] = Counter({"secuitcus": 2})
    with patch(
        "scripts.rule_normalizations.global_repeated_word_accept_scan.get_english_dictionary",
        return_value=frozenset(),
    ):
        out = scan_batch_global_repeated_word_accept(
            full_text, path_str, turn_boundaries, global_counts
        )
    assert len(out) == 0


def test_scan_batch_global_repeated_word_accept_single_letter_q_emitted() -> None:
    """Single letter q with global count 3 emits three."""
    full_text = "q q q"
    path_str = "/p.json"
    turn_boundaries = [(0, 5, path_str, 0)]
    global_counts: Counter[str] = Counter({"q": 3})
    with patch(
        "scripts.rule_normalizations.global_repeated_word_accept_scan.get_english_dictionary",
        return_value=frozenset({"q"}),
    ):
        out = scan_batch_global_repeated_word_accept(
            full_text, path_str, turn_boundaries, global_counts
        )
    q_results = [r for r in out if r[3] == "q"]
    assert len(q_results) == 3
    assert all(r[0] == "global_repeated_word_accept" for r in q_results)


def test_normalize_global_repeated_word_accept() -> None:
    """global_repeated_word_accept normalizer returns identity."""
    assert normalize_global_repeated_word_accept("anything") == ["anything"]
