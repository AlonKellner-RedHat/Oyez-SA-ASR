# Edited by Cursor: split from _brackets_accept (lintok; no new exclusions).
"""Parens, dash, accept-identity, bracket unwrap, website dot normalizers."""

import re

from scripts.rule_normalizations._constants import (
    LETTER_PRONUNCIATION,
    STANDARD_DASH,
)
from scripts.rule_normalizations._number_words import number_to_words


def normalize_double_letter_parens(span: str) -> list[str]:
    """Two letters in parentheses (ph), (ab) -> pee aych, ay bee."""
    s = span.strip()
    if len(s) < 4 or s[0] != "(" or s[-1] != ")":
        return [span]
    inner = s[1:-1].strip()
    if len(inner) != 2 or not inner.isalpha():
        return [span]
    a, b = inner[0].lower(), inner[1].lower()
    if a in LETTER_PRONUNCIATION and b in LETTER_PRONUNCIATION:
        return [f"{LETTER_PRONUNCIATION[a]} {LETTER_PRONUNCIATION[b]}"]
    return [span]


def normalize_single_letter_parens(span: str) -> list[str]:
    """Single letter in parentheses (with optional spaces) -> letter pronunciation."""
    s = span.strip()
    if len(s) < 3 or s[0] != "(" or s[-1] != ")":
        return [span]
    inner = s[1:-1].strip()
    if len(inner) != 1 or not inner.isalpha():
        return [span]
    letter = inner.lower()
    if letter in LETTER_PRONUNCIATION:
        return [LETTER_PRONUNCIATION[letter]]
    return [span]


def normalize_number_parens(span: str) -> list[str]:
    """Return spoken number for number in parentheses (e.g. (32)->thirty two)."""
    s = span.strip()
    if len(s) < 3 or s[0] != "(" or s[-1] != ")":
        return [span]
    inner = s[1:-1].strip()
    if not inner.isdigit():
        return [span]
    try:
        n = int(inner)
        if 0 <= n <= 999:
            return [number_to_words(n)]
    except (ValueError, KeyError):
        pass
    return [span]


def normalize_dash(span: str) -> list[str]:  # noqa: ARG001
    """Return single standard dash for non-standard dash or dash sequence."""
    return [STANDARD_DASH]


def normalize_known_names(span: str) -> list[str]:
    """Known name patterns (McLaughlin, FitzGerald): no correction, mark as handled."""
    return [span]


def normalize_all_caps_accept(span: str) -> list[str]:
    """All-caps 6+ letters (CERCLA, ASARCO, PROMESA): no correction, mark as handled."""
    return [span]


def normalize_known_mixed_case_entities(span: str) -> list[str]:
    """Known mixed-case entities (TikTok, YouTube, LinkedIn): no correction."""
    return [span]


def normalize_pascal_case_accept(span: str) -> list[str]:
    """PascalCase 6+ letters, each segment 3+: accept (identity)."""
    return [span]


def normalize_trailing_dash_accept(span: str) -> list[str]:
    """Word + trailing dash (interruption): accept (identity)."""
    return [span]


def normalize_mixed_case_accept_6plus(span: str) -> list[str]:
    """Mixed case 6+ letters (PowerEx, RadLAX): accept (identity)."""
    return [span]


def normalize_name_pattern_di(span: str) -> list[str]:
    """Di + capitalized word (DiBona, DiMaria): accept (identity)."""
    return [span]


def normalize_bracket_sentence_unwrap(span: str) -> list[str]:
    """Bracket with 4+ words -> inner text only (unwrap)."""
    s = span.strip()
    if len(s) < 3 or s[0] not in "([" or s[-1] not in ")]":
        return [span]
    inner = s[1:-1].strip()
    return [inner]


def normalize_website_dot(span: str) -> list[str]:
    """[xxxDOTyyy] -> xxx dot yyy."""
    m = re.search(r"\[([^\]]*?)DOT([^\]]*)\]", span, re.IGNORECASE)
    if not m:
        return [span]
    left = m.group(1).strip()
    right = m.group(2).strip()
    return [f"{left} dot {right}"]


def normalize_invalid_question_mark_fix(span: str) -> list[str]:
    """\ufffd? -> ?."""
    if "\ufffd" in span and "?" in span:
        return ["?"]
    return [span]


def normalize_repeated_word_accept(span: str) -> list[str]:
    """Word that appears 2+ times in same transcript: accept (no correction)."""
    return [span]


def normalize_global_repeated_word_accept(span: str) -> list[str]:
    """Invalid 3+ letter word appearing globally 3+ times: accept (no correction)."""
    return [span]
