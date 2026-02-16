# Edited by Cursor: split from test_build_awareness_candidates (lintok; no new exclusions).
"""Tests: awareness_single_letter (lowercase, period, brackets, a/i/v/x)."""

import pytest

from scripts.dictionary_loader import set_allow_no_enchant

pytestmark = pytest.mark.slow


def test_awareness_single_letter_lowercase_only() -> None:
    from scripts.build_awareness_candidates import _extract_awareness  # noqa: PLC0415

    set_allow_no_enchant(True)
    out_upper = _extract_awareness("to B or a C")
    single_upper = [
        span for (cat, _si, span) in out_upper if cat == "awareness_single_letter"
    ]
    assert "B" not in single_upper
    out_lower = _extract_awareness("too much e xecutive")
    single_lower = [
        (cat, span)
        for (cat, _si, span) in out_lower
        if cat == "awareness_single_letter"
    ]
    assert ("awareness_single_letter", "e") in single_lower


def test_awareness_single_letter_emits_e_xecutive() -> None:
    from scripts.build_awareness_candidates import _extract_awareness  # noqa: PLC0415

    set_allow_no_enchant(True)
    out = _extract_awareness("too much e xecutive")
    single = [
        (cat, span) for (cat, _si, span) in out if cat == "awareness_single_letter"
    ]
    assert ("awareness_single_letter", "e") in single


def test_awareness_single_letter_not_followed_by_period() -> None:
    from scripts.build_awareness_candidates import _extract_awareness  # noqa: PLC0415

    set_allow_no_enchant(True)
    out = _extract_awareness("Thank you, counse l. I am very sympathetic.")
    single = [span for (cat, _si, span) in out if cat == "awareness_single_letter"]
    assert "l." not in single


def test_awareness_single_letter_emits_t_you() -> None:
    from scripts.build_awareness_candidates import _extract_awareness  # noqa: PLC0415

    set_allow_no_enchant(True)
    out = _extract_awareness("Yes, t you")
    single = [
        (cat, span) for (cat, _si, span) in out if cat == "awareness_single_letter"
    ]
    assert ("awareness_single_letter", "t") in single


def test_awareness_single_letter_not_in_brackets() -> None:
    from scripts.build_awareness_candidates import _extract_awareness  # noqa: PLC0415

    set_allow_no_enchant(True)
    out = _extract_awareness("See (e) or (x) here.")
    single = [span for (cat, _si, span) in out if cat == "awareness_single_letter"]
    assert "e" not in single and "x" not in single


def test_awareness_single_letter_not_adjacent_to_number() -> None:
    from scripts.build_awareness_candidates import _extract_awareness  # noqa: PLC0415

    set_allow_no_enchant(True)
    out1 = _extract_awareness("5 t here")
    out2 = _extract_awareness("t 5 here")
    single1 = [span for (cat, _si, span) in out1 if cat == "awareness_single_letter"]
    single2 = [span for (cat, _si, span) in out2 if cat == "awareness_single_letter"]
    assert "t" not in single1 and "t" not in single2


def test_awareness_single_letter_excludes_a_i_v_x() -> None:
    from scripts.build_awareness_candidates import _extract_awareness  # noqa: PLC0415

    set_allow_no_enchant(True)
    out = _extract_awareness("a i v x e letter")
    single = [span for (cat, _si, span) in out if cat == "awareness_single_letter"]
    assert (
        "a" not in single
        and "i" not in single
        and "v" not in single
        and "x" not in single
    )
    assert "e" in single
