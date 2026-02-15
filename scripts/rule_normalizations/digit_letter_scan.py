# Edited by Cursor (ASR normalization rules expansion)
"""Scan for digit-letter and letter-digit mixed tokens (2d, A2, 640L, 707{b}, 1392(d))."""

import re

# Digit(s) + letter(s) as single token; digit(s) + {letter}; digit(s) + (letter).
# Alternating (F2A, 5K1, R2D2, W2s); digit(s) + (two+ letters) e.g. 1395(ff). Edited by Cursor (TDD item 4).
# Trailing (?!\w) allows match when followed by . or ) so 1392(d). matches.
DIGIT_LETTER_RE = re.compile(
    r"\b(?:\d+[a-zA-Z]+|[a-zA-Z]+\d+|\d+\{[a-zA-Z]\}|\d+\(\s*[a-zA-Z]\s*\)|"
    r"([a-zA-Z]\d+)+[a-zA-Z]?|\d+([a-zA-Z]\d+)+|\d+\(\s*[a-zA-Z]{2,}\s*\))(?!\w)"
)


def scan_turn_digit_letter(
    text: str,
    path_str: str = "",
) -> list[tuple[str, int, str, str]]:
    """Emit (rule_id, start_index, span, path_str) for each digit/letter mixed token."""
    result: list[tuple[str, int, str, str]] = []
    for m in DIGIT_LETTER_RE.finditer(text):
        result.append(("digit_letter_mixed", m.start(), m.group(0), path_str))
    return result
