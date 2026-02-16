# Edited by Cursor: extracted from __init__.py for lintok.
"""Digit-letter mixed and digit-run normalizers."""

from scripts.rule_normalizations._constants import LETTER_PRONUNCIATION
from scripts.rule_normalizations._number_words import (
    digit_to_word,
    number_to_words,
)


def _digits_to_spoken(digit_str: str) -> list[str]:
    """Spoken form of digit string for codes: 640->six forty, 707->seven oh seven."""
    result: list[str] = []
    if not digit_str or not digit_str.isdigit():
        return result
    n = int(digit_str)
    if len(digit_str) == 1:
        result = [digit_to_word(n)]
    elif len(digit_str) == 2:
        result = [number_to_words(n)]
    elif len(digit_str) == 3:
        if 10 <= n % 100 <= 99 and n % 10 == 0:
            result = [number_to_words(n // 100), number_to_words(n % 100)]
        else:
            result = [digit_to_word(int(d)) if d != "0" else "oh" for d in digit_str]
    elif len(digit_str) == 4:
        result = [
            number_to_words(int(digit_str[:2])),
            number_to_words(int(digit_str[2:])),
        ]
    else:
        result = [digit_to_word(int(d)) if d != "0" else "oh" for d in digit_str]
    return result


def _digit_run_options(digit_str: str) -> list[list[str]]:
    """Return alternative token lists for a digit run (digit-by-digit and grouped)."""
    if not digit_str or not digit_str.isdigit():
        return []
    n = int(digit_str)
    digit_by_digit = [digit_to_word(int(d)) if d != "0" else "oh" for d in digit_str]
    options: list[list[str]] = [digit_by_digit]
    if len(digit_str) == 2:
        options.append([number_to_words(n)])
    elif len(digit_str) == 3:
        if 10 <= n % 100 <= 99:
            options.append([number_to_words(n // 100), number_to_words(n % 100)])
    elif len(digit_str) == 4:
        options.append(
            [
                number_to_words(int(digit_str[:2])),
                number_to_words(int(digit_str[2:])),
            ]
        )
    return options


def normalize_digit_letter_mixed(span: str) -> list[str]:
    """Digit-letter mixed (2d, 77p0995e) -> spoken form(s)."""
    s = span.strip()
    if not s:
        return [span]
    parts: list[tuple[str, str]] = []
    i = 0
    while i < len(s):
        if s[i].isdigit():
            j = i
            while j < len(s) and s[j].isdigit():
                j += 1
            parts.append(("digits", s[i:j]))
            i = j
        elif s[i] in "({" and i + 1 < len(s):
            close = ")" if s[i] == "(" else "}"
            k = s.find(close, i + 1)
            if k != -1:
                inner = s[i + 1 : k].strip()
                if inner.isalpha():
                    for c in inner:
                        parts.append(("letter", c))
                    i = k + 1
                    continue
            i += 1
        elif s[i].isalpha():
            j = i
            while j < len(s) and s[j].isalpha():
                j += 1
            parts.append(("letter", s[i:j]))
            i = j
        else:
            i += 1
    option_sequences: list[list[str]] = [[]]
    for kind, val in parts:
        if kind == "digits":
            opts = _digit_run_options(val)
            if not opts:
                for seq in option_sequences:
                    seq.extend(_digits_to_spoken(val))
            else:
                new_seqs: list[list[str]] = []
                for seq in option_sequences:
                    for opt in opts:
                        new_seqs.append(seq + opt)
                option_sequences = new_seqs
        elif kind == "letter":
            toks = [LETTER_PRONUNCIATION.get(c.lower(), c) for c in val]
            for seq in option_sequences:
                seq.extend(toks)
    if not option_sequences or not option_sequences[0]:
        return [span]
    result_set: set[str] = set()
    for seq in option_sequences:
        result_set.add(" ".join(seq))
    result_list = list(result_set)
    primary = result_list[0]
    if (s.endswith("2s") or s.endswith("2S")) and " two ess" in primary:
        result_set.add(primary.replace(" two ess", " twos"))
        result_list = list(result_set)
    return result_list
