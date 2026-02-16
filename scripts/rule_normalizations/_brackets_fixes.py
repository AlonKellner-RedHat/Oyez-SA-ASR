# Edited by Cursor: split from _brackets_accept (lintok; no new exclusions).
"""Replacement char, concatenated split, single digit, typo, section, list, non-speech."""

import re

from scripts.rule_normalizations._constants import UNBRACKETED_NON_SPEECH_PHRASES
from scripts.rule_normalizations._non_speech import is_non_speech_content
from scripts.rule_normalizations._number_words import number_to_words


def normalize_replacement_char_fix(span: str) -> list[str]:
    """Known U+FFFD patterns (Condé Nast) -> fixed string."""
    from scripts.rule_normalizations.replacement_char_fix_scan import (  # noqa: PLC0415
        get_replacement_char_fix,
    )

    out = get_replacement_char_fix(span.strip())
    return [out] if out is not None else [span]


def normalize_concatenated_word_split(span: str) -> list[str]:
    """Token that splits into two valid words -> 'left right'."""
    from scripts.rule_normalizations.concatenated_word_scan import (  # noqa: PLC0415
        get_concatenated_word_split_form,
    )

    out = get_concatenated_word_split_form(span.strip())
    return [out] if out else [span]


def normalize_single_digit_valid_word(span: str) -> list[str]:
    """Token with one digit: if remainder is in word list, return [remainder]."""
    from scripts.rule_normalizations.single_digit_valid_word_scan import (  # noqa: PLC0415
        _single_digit_remainder,
        get_single_digit_valid_words,
    )

    remainder = _single_digit_remainder(span)
    if remainder is None:
        return [span]
    words = get_single_digit_valid_words()
    if remainder.lower() in words:
        return [remainder]
    return [span]


def normalize_typo_levenshtein(span: str) -> list[str]:
    """Return span unchanged; corrections come from typo_corrections in build_rule_candidates."""
    return [span]


def normalize_inline_typo(span: str) -> list[str]:
    """word[: correction] or word, [: correction] or , [: correction] -> [correction]."""
    m = re.search(r"\w+,\s*\[\s*:\s*([^\]]+)\]", span)
    if m:
        return [m.group(1).strip() + ","]
    m = re.search(r",\s*\[\s*:\s*([^\]]+)\]", span)
    if m:
        return [", " + m.group(1).strip()]
    m = re.search(r"\w+\s*\[\s*:\s*([^\]]+)\]", span)
    if m:
        return [m.group(1).strip()]
    return [span]


def normalize_section_header(span: str) -> list[str]:  # noqa: ARG001
    """Section header (all-caps at start/end of turn): remove."""
    return [""]


def normalize_numbered_list_marker(span: str) -> list[str]:
    """Numbered list marker 1) -> one, 5) -> five."""
    s = span.strip()
    if not s.endswith(")"):
        return [span]
    num_part = s[:-1].strip()
    if not num_part.isdigit():
        return [span]
    try:
        n = int(num_part)
        if 1 <= n <= 99:
            return [number_to_words(n)]
    except (ValueError, KeyError):
        pass
    return [span]


def normalize_non_speech_brackets(span: str) -> list[str]:
    """Return empty string for (Inaudible), [Laughter], etc.; else identity."""
    s = span.strip().rstrip(".").strip()
    phrase_norm = " ".join(s.lower().split())
    if phrase_norm in UNBRACKETED_NON_SPEECH_PHRASES:
        return [""]
    if len(s) < 3 or s[0] not in "([{" or s[-1] not in ")]}":
        return [span]
    content = s[1:-1].strip().rstrip(".").strip()
    content_norm = " ".join(content.lower().split())
    if is_non_speech_content(content_norm):
        return [""]
    return [span]
