# Edited by Cursor: regex registry for build_rule_candidates (lintok split).
"""Rule regex patterns and Latin extended scan constants."""

import re

from scripts.collect_asr_artifacts import (
    DECADE_RE,
    LEADING_DECIMAL_RE,
    ORDINAL_RE,
    PERCENTAGE_RE,
    ROMAN_NUMERAL_RE,
    VOTE_TALLY_RE,
    YEAR_RE,
)

TIME_OF_DAY_RE = re.compile(r"\b\d{1,2}:\d{2}(?!:\d)\b")
SINGLE_LETTER_PARENS_RE = re.compile(r"\(\s*[a-zA-Z]\s*\)")
DOUBLE_LETTER_PARENS_RE = re.compile(r"\(\s*[a-zA-Z][a-zA-Z]\s*\)")
NUMBER_PARENS_RE = re.compile(r"\(\s*\d+\s*\)")

RULE_REGEX: dict[str, tuple[re.Pattern[str], int]] = {
    "vote_tally": (VOTE_TALLY_RE, 1),
    "years": (YEAR_RE, 1),
    "roman_numerals": (ROMAN_NUMERAL_RE, 1),
    "percentages": (PERCENTAGE_RE, 0),
    "decades": (DECADE_RE, 0),
    "single_letter_parens": (SINGLE_LETTER_PARENS_RE, 0),
    "double_letter_parens": (DOUBLE_LETTER_PARENS_RE, 0),
    "number_parens": (NUMBER_PARENS_RE, 0),
    "ordinals": (ORDINAL_RE, 0),
    "leading_decimal": (LEADING_DECIMAL_RE, 0),
    "time_of_day": (TIME_OF_DAY_RE, 0),
}

LATIN_EXTENDED_RANGE = range(0x00C0, 0x0250)
WORD_RE = re.compile(r"\S+")
LATIN_EXTENDED_CHAR_RE = re.compile(r"[\u00C0-\u024F]")
