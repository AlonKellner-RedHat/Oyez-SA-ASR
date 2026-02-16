# Edited by Cursor: split from test_rule_normalizations (lintok; no new exclusions).
"""Tests for bracket/non-speech/accept normalizers and related scans."""

from scripts.rule_normalizations import (
    is_non_speech_content,
    normalize_all_caps_accept,
    normalize_digit_letter_mixed,
    normalize_known_mixed_case_entities,
    normalize_known_names,
    normalize_non_speech_brackets,
    normalize_numbered_list_marker,
    normalize_trailing_dash_accept,
)
from scripts.rule_normalizations.trailing_dash_accept_scan import (
    scan_turn_trailing_dash_accept,
)


def test_is_non_speech_content_overlap_and_2lev() -> None:
    """Plan: overlap exact; 2-Lev (inaudibel->inaudible); existing 1-Lev still True."""
    assert is_non_speech_content("overlap") is True
    assert is_non_speech_content("inaudibel") is True
    assert is_non_speech_content("lanch") is True


def test_normalize_non_speech_brackets() -> None:
    """Inaudible, Laughter, etc. -> empty string."""
    assert normalize_non_speech_brackets("(Inaudible)") == [""]
    assert normalize_non_speech_brackets("(Laughter)") == [""]
    assert normalize_non_speech_brackets("[Laughter]") == [""]
    assert normalize_non_speech_brackets("[Laughter Attempt]") == [""]
    assert normalize_non_speech_brackets("(audio abruptly cut 00:35:34-00:35:40)") == [
        ""
    ]
    assert normalize_non_speech_brackets("(Laughs)") == [""]
    assert normalize_non_speech_brackets("[Laughs]") == [""]
    assert normalize_non_speech_brackets("(Applause)") == [""]
    assert normalize_non_speech_brackets("[Inaudibles.]") == [""]
    assert normalize_non_speech_brackets("[Something inaudible.]") == [""]
    assert normalize_non_speech_brackets("(audio glitch)") == [""]
    assert normalize_non_speech_brackets("[break in recording]") == [""]
    assert normalize_non_speech_brackets("[Noon Recess]") == [""]
    assert normalize_non_speech_brackets("[Lanch]") == [""]
    assert normalize_non_speech_brackets("(Overlap)") == [""]
    assert normalize_non_speech_brackets("(Inaudibel)") == [""]
    assert normalize_non_speech_brackets("(sic)") == [""]
    assert normalize_non_speech_brackets("(ph)") == [""]
    assert normalize_non_speech_brackets("[ph]") == [""]
    assert normalize_non_speech_brackets("[Break]") == [""]


def test_normalize_non_speech_brackets_unknown_returns_span() -> None:
    """Unknown content returns list with original span."""
    assert normalize_non_speech_brackets("(Section 3)") == ["(Section 3)"]


def test_normalize_non_speech_brackets_unbracketed() -> None:
    """Unbracketed Generallaughter. / General laughter. -> empty."""
    assert normalize_non_speech_brackets("Generallaughter.") == [""]
    assert normalize_non_speech_brackets("General laughter.") == [""]
    assert normalize_non_speech_brackets("GENERAL LAUGHTER") == [""]


def test_normalize_digit_letter_mixed_multiple_forms() -> None:
    """77p0995e and 514b2b return multiple spoken forms."""
    result_77 = normalize_digit_letter_mixed("77p0995e")
    assert "seventy seven pee nine ninety five ee" in result_77
    assert "seven seven pee oh nine nine five ee" in result_77
    result_514 = normalize_digit_letter_mixed("514b2b")
    assert "five one four bee two bee" in result_514
    assert "five fourteen bee two bee" in result_514


def test_normalize_digit_letter_mixed() -> None:
    """Digit-letter mixed (2d, A2, 640L, etc.) -> spoken form(s)."""
    assert normalize_digit_letter_mixed("2d") == ["two dee"]
    assert normalize_digit_letter_mixed("A2") == ["ay two"]
    assert "six forty ell" in normalize_digit_letter_mixed("640L")
    assert "em fifty" in normalize_digit_letter_mixed("M50")
    assert "seven oh seven bee" in normalize_digit_letter_mixed("707{b}")
    assert "thirteen ninety two dee" in normalize_digit_letter_mixed("1392(d)")
    assert "eff two ay" in normalize_digit_letter_mixed("F2A")
    assert "five kay one" in normalize_digit_letter_mixed("5K1")
    assert "ar two dee two" in normalize_digit_letter_mixed("R2D2")
    result_w2s = normalize_digit_letter_mixed("W2s")
    assert "double-u two ess" in result_w2s and "double-u twos" in result_w2s
    result_1395ff = normalize_digit_letter_mixed("1395(ff)")
    assert "thirteen ninety five eff eff" in result_1395ff


def test_normalize_known_names() -> None:
    """Known names (McLaughlin, FitzGerald, etc.) -> identity."""
    assert normalize_known_names("McLaughlin") == ["McLaughlin"]
    assert normalize_known_names("McCoy") == ["McCoy"]
    assert normalize_known_names("FitzGerald") == ["FitzGerald"]
    assert normalize_known_names("MacKinnon") == ["MacKinnon"]
    assert normalize_known_names("LeMaistre") == ["LeMaistre"]
    assert normalize_known_names("DeShaney") == ["DeShaney"]
    assert normalize_known_names("LaPenta") == ["LaPenta"]
    assert normalize_known_names("DuPoint") == ["DuPoint"]
    assert normalize_known_names("DuPage") == ["DuPage"]


def test_normalize_known_mixed_case_entities() -> None:
    """Known mixed-case entities (TikTok, YouTube) -> identity."""
    assert normalize_known_mixed_case_entities("TikTok") == ["TikTok"]
    assert normalize_known_mixed_case_entities("YouTube") == ["YouTube"]
    assert normalize_known_mixed_case_entities("LinkedIn") == ["LinkedIn"]


def test_normalize_all_caps_accept() -> None:
    """All-caps 6+ letters (CERCLA, ASARCO) -> identity."""
    assert normalize_all_caps_accept("CERCLA") == ["CERCLA"]
    assert normalize_all_caps_accept("ASARCO") == ["ASARCO"]
    assert normalize_all_caps_accept("PROMESA") == ["PROMESA"]


def test_scan_turn_trailing_dash_accept_emits_word_plus_dash() -> None:
    """Token word + trailing dash emits one result."""
    text = "turns out that the identific- the"
    out = scan_turn_trailing_dash_accept(text, "/p.json")
    assert len(out) == 1
    rule_id, _start, span, path_str = out[0]
    assert rule_id == "trailing_dash_accept"
    assert span == "identific-"
    assert path_str == "/p.json"
    out2 = scan_turn_trailing_dash_accept("identification", "/p.json")
    assert len(out2) == 0
    out3 = scan_turn_trailing_dash_accept("word\u2013", "/p.json")
    assert len(out3) == 1
    assert out3[0][2] == "word\u2013"
    out4 = scan_turn_trailing_dash_accept(
        "turns out that the identific - the", "/p.json"
    )
    assert len(out4) == 1
    assert out4[0][2] == "identific -"


def test_normalize_trailing_dash_accept_identity() -> None:
    """trailing_dash_accept normalizer returns identity."""
    assert normalize_trailing_dash_accept("identific-") == ["identific-"]


def test_normalize_numbered_list_marker() -> None:
    """Numbered list marker 1) -> one, 5) -> five, etc."""
    assert normalize_numbered_list_marker("1)") == ["one"]
    assert normalize_numbered_list_marker("5)") == ["five"]
    assert normalize_numbered_list_marker("12)") == ["twelve"]
    assert normalize_numbered_list_marker("42)") == ["forty two"]
    assert normalize_numbered_list_marker("67)") == ["sixty seven"]
