# Edited by Cursor: extraction for build_awareness_candidates (lintok split).
"""Extract awareness spans from transcript text."""

import re
import time
from collections import defaultdict

from scripts.build_awareness_helpers import (
    _SINGLE_LETTER_ALLOWED,
    _SINGLE_LETTER_RE,
    BRACKET_CONTENT_MAX,
    DIGIT_LETTER_MIXED_RE,
    PUNCT,
    WORD_RE,
    _bracket_span,
    _bracket_spans,
    _in_brackets,
    _is_valid_word_for_non_dictionary,
)
from scripts.collect_asr_artifacts_regex import (
    ALL_CAPS_LONG_RE,
    AWARENESS_SYMBOLS,
    BRACKETS_ANGLE_RE,
    BRACKETS_CURLY_RE,
    BRACKETS_NUMBERED_RE,
    BRACKETS_PAREN_RE,
    BRACKETS_SQUARE_RE,
    LEADING_DECIMAL_RE,
    MIXED_CASE_RE,
    ORDINAL_RE,
    TIME_LIKE_RE,
    YEAR_RE,
)
from scripts.dictionary_loader import get_english_dictionary


def _extract_awareness(
    text: str,
    profile_times: defaultdict | None = None,
    dic: frozenset[str] | None = None,
) -> list[tuple[str, int, str]]:
    """Emit (category_id, start_index, span) for each match. Awareness does not suggest corrections."""
    out: list[tuple[str, int, str]] = []
    pt = profile_times
    word_dic = dic if dic is not None else get_english_dictionary()
    word_list = [(m.start(), m.group(0)) for m in WORD_RE.finditer(text)]
    bracket_spans = _bracket_spans(text)
    for _i, (start_index, word) in enumerate(word_list):
        if pt is not None:
            t0 = time.perf_counter()
        if any(ord(c) > 127 for c in word):
            out.append(("awareness_non_ascii", start_index, word))
        if pt is not None:
            pt["awareness_non_ascii"] += time.perf_counter() - t0

        if pt is not None:
            t0 = time.perf_counter()
        if MIXED_CASE_RE.fullmatch(word):
            out.append(("awareness_mixed_case", start_index, word))
        if pt is not None:
            pt["awareness_mixed_case"] += time.perf_counter() - t0

        if pt is not None:
            t0 = time.perf_counter()
        if ALL_CAPS_LONG_RE.fullmatch(word):
            out.append(("awareness_all_caps_long", start_index, word))
        if pt is not None:
            pt["awareness_all_caps_long"] += time.perf_counter() - t0

        if pt is not None:
            t0 = time.perf_counter()
        if (
            word == "..."
            or word in AWARENESS_SYMBOLS
            or any(sym in word for sym in AWARENESS_SYMBOLS)
        ):
            out.append(("awareness_symbols", start_index, word))
        if pt is not None:
            pt["awareness_symbols"] += time.perf_counter() - t0

        if pt is not None:
            t0 = time.perf_counter()
        if TIME_LIKE_RE.fullmatch(word):
            out.append(("awareness_time_like", start_index, word))
        if pt is not None:
            pt["awareness_time_like"] += time.perf_counter() - t0

        if pt is not None:
            t0 = time.perf_counter()
        if LEADING_DECIMAL_RE.fullmatch(word):
            out.append(("awareness_leading_decimal", start_index, word))
        if pt is not None:
            pt["awareness_leading_decimal"] += time.perf_counter() - t0

        if pt is not None:
            t0 = time.perf_counter()
        if DIGIT_LETTER_MIXED_RE.fullmatch(word):
            out.append(("awareness_digit_letter_mixed", start_index, word))
        if pt is not None:
            pt["awareness_digit_letter_mixed"] += time.perf_counter() - t0

        if pt is not None:
            t0 = time.perf_counter()
        if any(not c.isalnum() and c not in PUNCT for c in word):
            out.append(("awareness_other_char", start_index, word))
        if pt is not None:
            pt["awareness_other_char"] += time.perf_counter() - t0

        if pt is not None:
            t0 = time.perf_counter()
        if (
            not _is_valid_word_for_non_dictionary(word, word_dic)
            and not word.isdigit()
            and not ORDINAL_RE.fullmatch(word)
            and not YEAR_RE.fullmatch(word)
            and not (word and word[0].isupper())
        ):
            out.append(("awareness_non_dictionary", start_index, word))
        if pt is not None:
            pt["awareness_non_dictionary"] += time.perf_counter() - t0

        if pt is not None:
            t0 = time.perf_counter()
        if _SINGLE_LETTER_RE.fullmatch(word):
            letter = word[0].lower()
            if (
                word[0].islower()
                and letter not in _SINGLE_LETTER_ALLOWED
                and not word.endswith(".")
            ) and not _in_brackets(start_index, start_index + len(word), bracket_spans):
                prev_has_digit = _i > 0 and bool(re.search(r"\d", word_list[_i - 1][1]))
                next_has_digit = _i < len(word_list) - 1 and bool(
                    re.search(r"\d", word_list[_i + 1][1])
                )
                if not prev_has_digit and not next_has_digit:
                    out.append(("awareness_single_letter", start_index, word))
        if pt is not None:
            pt["awareness_single_letter"] += time.perf_counter() - t0

    if pt is not None:
        t0 = time.perf_counter()
    for m in BRACKETS_PAREN_RE.finditer(text):
        span = _bracket_span(m.group(1), "(", ")")
        out.append(("awareness_brackets_parens", m.start(), span))
    if pt is not None:
        pt["awareness_brackets_parens"] += time.perf_counter() - t0

    if pt is not None:
        t0 = time.perf_counter()
    for m in BRACKETS_SQUARE_RE.finditer(text):
        span = _bracket_span(m.group(1), "[", "]")
        out.append(("awareness_brackets_square", m.start(), span))
    if pt is not None:
        pt["awareness_brackets_square"] += time.perf_counter() - t0

    if pt is not None:
        t0 = time.perf_counter()
    for m in BRACKETS_CURLY_RE.finditer(text):
        span = _bracket_span(m.group(1), "{", "}")
        out.append(("awareness_brackets_curly", m.start(), span))
    if pt is not None:
        pt["awareness_brackets_curly"] += time.perf_counter() - t0

    if pt is not None:
        t0 = time.perf_counter()
    for m in BRACKETS_NUMBERED_RE.finditer(text):
        out.append(("awareness_brackets_numbered", m.start(), m.group(0)))
    if pt is not None:
        pt["awareness_brackets_numbered"] += time.perf_counter() - t0

    if pt is not None:
        t0 = time.perf_counter()
    for m in BRACKETS_ANGLE_RE.finditer(text):
        span = m.group(0)
        if len(span) > BRACKET_CONTENT_MAX + 2:
            span = span[: BRACKET_CONTENT_MAX + 1] + "...>"
        out.append(("awareness_brackets_angle", m.start(), span))
    if pt is not None:
        pt["awareness_brackets_angle"] += time.perf_counter() - t0

    return out
