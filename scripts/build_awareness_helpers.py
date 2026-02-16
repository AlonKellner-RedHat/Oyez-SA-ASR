# Edited by Cursor: helpers for build_awareness_candidates (lintok split).
"""Helpers and constants for awareness candidate extraction."""

import re
import string

from scripts.collect_asr_artifacts import (
    BRACKETS_ANGLE_RE,
    BRACKETS_CURLY_RE,
    BRACKETS_NUMBERED_RE,
    BRACKETS_PAREN_RE,
    BRACKETS_SQUARE_RE,
)
from scripts.dictionary_loader import is_valid_word_for_rules

BRACKET_CONTENT_MAX = 80
WORD_RE = re.compile(r"\S+")
DIGIT_LETTER_MIXED_RE = re.compile(r"\b(?=\w*\d)(?=\w*[A-Za-z])\w+\b")
PUNCT = set(string.punctuation)

AWARENESS_LABELS: dict[str, str] = {
    "awareness_non_ascii": "Non-ASCII character",
    "awareness_mixed_case": "Mixed case (e.g. McCloud)",
    "awareness_all_caps_long": "Long all-caps (6+ letters)",
    "awareness_symbols": "Typographic/legal symbol",
    "awareness_brackets_parens": "Brackets (parentheses)",
    "awareness_brackets_square": "Brackets (square)",
    "awareness_brackets_curly": "Brackets (curly)",
    "awareness_brackets_numbered": "Numbered bracket (e.g. 1))",
    "awareness_brackets_angle": "Angle brackets (<foo>)",
    "awareness_time_like": "Time-like (12:34, 00:35:34, 9:38.5)",
    "awareness_leading_decimal": "Leading decimal (.66)",
    "awareness_digit_letter_mixed": "Word with digits and letters (e.g. H1N1, 2nd)",
    "awareness_other_char": "Character other than letter, digit, or punctuation",
    "awareness_non_dictionary": "Word not in dictionary (e.g. befair, supremecourt)",
    "awareness_single_letter": "Single letter (lowercase, not a/i/v/x, not followed by period) outside brackets and not adjacent to numbers",
}

FILTER_NOTE = "No normalization rule; awareness/review only."

_SINGLE_LETTER_RE = re.compile(r"^[a-zA-Z][.,;:!?'\"]*$")
_SINGLE_LETTER_ALLOWED = frozenset({"a", "v", "x", "i"})
LETTER_DIGIT_APOSTROPHE_SPAN_RE = re.compile(r"[a-zA-Z0-9']+")
MIN_SPAN_LEN = 4
_ORDINAL_SUBSTR_RE = re.compile(r"^\d+(?:st|nd|rd|th)$", re.IGNORECASE)
_YEAR_SUBSTR_RE = re.compile(r"^(?:19|20)\d{2}$")


def _is_valid_subspan(part: str, dic: frozenset[str] | object) -> bool:
    """Return True if part is valid (dict or stem in dict), or ordinal, or year, or all digits."""
    if not part:
        return False
    if is_valid_word_for_rules(part, dic):  # type: ignore[arg-type]
        return True
    if _ORDINAL_SUBSTR_RE.fullmatch(part):
        return True
    if _YEAR_SUBSTR_RE.fullmatch(part):
        return True
    return bool(part.isdigit())


def _is_valid_word_for_non_dictionary(word: str, dic: frozenset[str]) -> bool:
    """Return True if every letter/digit/apostrophe span of length >= 4 is valid."""
    for m in LETTER_DIGIT_APOSTROPHE_SPAN_RE.finditer(word):
        span = m.group(0)
        if len(span) >= MIN_SPAN_LEN and not _is_valid_subspan(span, dic):
            return False
    return True


def _bracket_span(content: str, prefix: str, suffix: str) -> str:
    """Build bracket key with truncation (match collect_asr_artifacts)."""
    content = content.strip()
    if len(content) > BRACKET_CONTENT_MAX:
        content = content[:BRACKET_CONTENT_MAX] + "..."
    return f"{prefix}{content}{suffix}"


def _bracket_spans(text: str) -> list[tuple[int, int]]:
    """Return (start, end) for every bracket match (parens, square, curly, angle, numbered)."""
    spans: list[tuple[int, int]] = []
    for pattern in (
        BRACKETS_PAREN_RE,
        BRACKETS_SQUARE_RE,
        BRACKETS_CURLY_RE,
        BRACKETS_ANGLE_RE,
        BRACKETS_NUMBERED_RE,
    ):
        for m in pattern.finditer(text):
            spans.append((m.start(), m.end()))
    return spans


def _in_brackets(start: int, end: int, bracket_spans: list[tuple[int, int]]) -> bool:
    """Return True if [start, end) overlaps any bracket span."""
    return any(not (end <= s or e <= start) for s, e in bracket_spans)
