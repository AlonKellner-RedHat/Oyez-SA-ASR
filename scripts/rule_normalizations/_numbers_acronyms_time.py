# Edited by Cursor: split from _numbers (lintok; no new exclusions).
"""Acronym, time, letter-Roman, percentage, double-quote normalizers."""

import re

from scripts.rule_normalizations._constants import LETTER_PRONUNCIATION
from scripts.rule_normalizations._number_words import (
    digit_to_word,
    number_to_words,
    roman_to_int,
)


def normalize_common_acronym(span: str) -> list[str]:
    """Spell common acronym (PhD, Ph.D.) letter-by-letter (pee aych dee)."""
    s = span.strip()
    if not s:
        return [span]
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return [span]
    words = [LETTER_PRONUNCIATION.get(c.lower(), c) for c in letters]
    return [" ".join(words)]


def normalize_short_mixed_acronym(span: str) -> list[str]:
    """Spell short mixed-case acronym (2-5 letters, half+ caps) letter-by-letter."""
    s = span.strip()
    if len(s) < 2 or len(s) > 5 or not s.isalpha():
        return [span]
    caps = sum(1 for c in s if c.isupper())
    if caps < (len(s) + 1) // 2:
        return [span]
    words = [LETTER_PRONUNCIATION.get(c.lower(), c) for c in s]
    return [" ".join(words)]


def normalize_time_of_day(span: str) -> list[str]:
    """Time of day H:MM -> eight forty; 1:00 -> one / one oh oh."""
    s = span.strip()
    if ":" not in s or s.count(":") != 1:
        return [span]
    parts = s.split(":", 1)
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        return [span]
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        return [span]
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return [span]
    hour_word = number_to_words(hour)
    if minute == 0:
        return [hour_word, f"{hour_word} oh oh"]
    min_word = digit_to_word(minute) if minute <= 9 else number_to_words(minute)
    return [f"{hour_word} {min_word}"]


def normalize_bracket_acronym(span: str) -> list[str]:
    """Parenthesized acronym (MPSC), (NRDC) -> letter-by-letter."""
    s = span.strip()
    if len(s) < 4 or s[0] != "(" or s[-1] != ")":
        return [span]
    inner = s[1:-1].strip()
    if len(inner) < 2:
        return [span]
    words = [LETTER_PRONUNCIATION.get(c.lower(), c) for c in inner]
    return [" ".join(words)]


def normalize_letter_roman_clause(span: str) -> list[str]:
    """(C)(iii) -> 'cee three'; letter + Roman clause."""
    s = span.strip()
    m = re.match(
        r"\(\s*([A-Za-z])\s*\)\s*\(\s*(i|ii|iii|iv|v|vi|vii|viii|ix|x|xi|xii)\s*\)",
        s,
        re.IGNORECASE,
    )
    if not m:
        return [span]
    letter = m.group(1).lower()
    roman_part = m.group(2).strip().upper()
    val = roman_to_int(roman_part)
    if val is None:
        return [span]
    letter_word = LETTER_PRONUNCIATION.get(letter, letter)
    num_word = number_to_words(val)
    return [f"{letter_word} {num_word}"]


def normalize_letter_dash_sequence(span: str) -> list[str]:
    """(R-5) or R-5 -> 'ar five'."""
    s = span.strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1].strip()
    m = re.match(r"([A-Za-z])\s*-\s*(\d+)", s)
    if not m:
        return [span]
    letter = m.group(1).lower()
    num_str = m.group(2)
    try:
        n = int(num_str)
    except ValueError:
        return [span]
    letter_word = LETTER_PRONUNCIATION.get(letter, letter)
    num_word = number_to_words(n)
    return [f"{letter_word} {num_word}"]


def normalize_percentage(span: str) -> list[str]:
    """Normalize percentage (50% or 25 percent) -> spoken form."""
    s = span.strip().replace(" ", "")
    num_str = s.rstrip("%").replace("percent", "").strip()
    if not num_str.isdigit():
        return [span]
    try:
        n = int(num_str)
        return [f"{number_to_words(n)} percent"]
    except (ValueError, KeyError):
        return [span]


def normalize_double_quote(span: str) -> list[str]:  # noqa: ARG001
    """Double-quote (open/close): same 10 spoken options for both. Span ignored."""
    return [
        "",
        "quote",
        "start quote",
        "open quote",
        "open the quote",
        "I quote",
        "and I quote",
        "end quote",
        "close quote",
        "close the quote",
    ]
