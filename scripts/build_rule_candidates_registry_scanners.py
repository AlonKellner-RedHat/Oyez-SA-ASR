# Edited by Cursor: scanners registry for build_rule_candidates (lintok split).
"""Scanner registry and scan helpers."""

import bisect

from scripts.build_rule_candidates_registry_regex import (
    LATIN_EXTENDED_CHAR_RE,
    RULE_REGEX,
)
from scripts.rule_normalizations.all_caps_accept_scan import scan_turn_all_caps_accept
from scripts.rule_normalizations.bracket_acronym_scan import scan_turn_bracket_acronym
from scripts.rule_normalizations.bracket_sentence_scan import scan_turn_bracket_sentence
from scripts.rule_normalizations.common_acronym_scan import scan_turn_common_acronym
from scripts.rule_normalizations.concatenated_word_scan import (
    scan_turn_concatenated_word,
)
from scripts.rule_normalizations.dash_scan import scan_turn_dashes
from scripts.rule_normalizations.digit_letter_scan import scan_turn_digit_letter
from scripts.rule_normalizations.dual_notation_scan import scan_turn_dual_notation
from scripts.rule_normalizations.editorial_dollar_scan import scan_turn_editorial_dollar
from scripts.rule_normalizations.fraction_scan import scan_turn_fraction
from scripts.rule_normalizations.global_repeated_word_accept_scan import (
    scan_batch_global_repeated_word_accept,
)
from scripts.rule_normalizations.half_number_scan import scan_turn_half_number
from scripts.rule_normalizations.inline_typo_scan import scan_turn_inline_typo
from scripts.rule_normalizations.invalid_question_mark_scan import (
    scan_turn_invalid_question_mark,
)
from scripts.rule_normalizations.known_mixed_case_scan import scan_turn_known_mixed_case
from scripts.rule_normalizations.known_names_scan import scan_turn_known_names
from scripts.rule_normalizations.letter_dash_scan import scan_turn_letter_dash
from scripts.rule_normalizations.letter_roman_clause_scan import (
    scan_turn_letter_roman_clause,
)
from scripts.rule_normalizations.mixed_case_accept_6plus_scan import (
    scan_turn_mixed_case_accept_6plus,
)
from scripts.rule_normalizations.name_pattern_di_scan import scan_turn_name_pattern_di
from scripts.rule_normalizations.non_speech_brackets_scan import (
    scan_turn_non_speech_brackets,
)
from scripts.rule_normalizations.numbered_list_scan import scan_turn_numbered_list
from scripts.rule_normalizations.pascal_case_accept_scan import (
    scan_turn_pascal_case_accept,
)
from scripts.rule_normalizations.quote_scan import scan_turn_quotes
from scripts.rule_normalizations.repeated_word_accept_scan import (
    scan_batch_repeated_word_accept,
)
from scripts.rule_normalizations.replacement_char_fix_scan import (
    scan_turn_replacement_char_fix,
)
from scripts.rule_normalizations.roman_parens_scan import scan_turn_roman_parens
from scripts.rule_normalizations.section_header_scan import scan_turn_section_header
from scripts.rule_normalizations.short_mixed_acronym_scan import (
    scan_turn_short_mixed_acronym,
)
from scripts.rule_normalizations.single_digit_valid_word_scan import (
    scan_turn_single_digit_valid_word,
)
from scripts.rule_normalizations.special_currency_scan import scan_turn_special_currency
from scripts.rule_normalizations.split_word_merge_scan import scan_turn_split_word_merge
from scripts.rule_normalizations.symbol_scan import scan_turn_symbols
from scripts.rule_normalizations.title_abbreviation_scan import (
    scan_turn_title_abbreviation,
)
from scripts.rule_normalizations.trailing_dash_accept_scan import (
    scan_turn_trailing_dash_accept,
)
from scripts.rule_normalizations.typo_levenshtein_scan import scan_turn_typo_levenshtein
from scripts.rule_normalizations.website_dot_scan import scan_turn_website_dot


def _scan_turn(text: str, path_str: str) -> list[tuple[str, int, str, str]]:
    """Emit (rule_id, start_index, span, path_str) for each match."""
    out: list[tuple[str, int, str, str]] = []
    for rule_id, (pattern, group_ix) in RULE_REGEX.items():
        for m in pattern.finditer(text):
            span = m.group(0) if group_ix == 0 else m.group(group_ix)
            out.append((rule_id, m.start(), span, path_str))
    return out


def _scan_turn_batch(
    full_text: str,
    _path_str: str,
    turn_boundaries: list[tuple[int, int, str, int]],
) -> list[tuple[str, int, int, str, str]]:
    """Emit (rule_id, turn_index, start_index, span, path_str) for each match."""
    if not turn_boundaries:
        return []
    turn_starts = [b[0] for b in turn_boundaries]
    out: list[tuple[str, int, int, str, str]] = []
    for rule_id, (pattern, group_ix) in RULE_REGEX.items():
        for m in pattern.finditer(full_text):
            pos = m.start()
            idx = bisect.bisect_right(turn_starts, pos) - 1
            if idx < 0 or pos >= turn_boundaries[idx][1]:
                continue
            start, _end, pstr, turn_index = turn_boundaries[idx]
            span = m.group(0) if group_ix == 0 else m.group(group_ix)
            out.append((rule_id, turn_index, pos - start, span, pstr))
    return out


def _scan_turn_filter(rule_id: str, span: str) -> bool:
    """Return False to skip adding this result (leading_decimal .YYYY, single_letter_parens (i))."""
    if (
        rule_id == "leading_decimal"
        and len(span) == 5
        and span.startswith(".")
        and span[1:].isdigit()
        and (span[1:].startswith("1") or span[1:].startswith("20"))
    ):
        return False
    if (
        rule_id == "single_letter_parens"
        and len(span) >= 3
        and span[0] == "("
        and span[-1] == ")"
    ):
        inner = span[1:-1].strip().lower()
        if inner == "i":
            return False
    return True


def _scan_turn_latin(text: str, path_str: str) -> list[tuple[str, int, str, str]]:
    """Emit (latin_extended, start_index, word, path_str) for words containing Latin extended chars."""
    out: list[tuple[str, int, str, str]] = []
    seen_start: set[int] = set()
    for m in LATIN_EXTENDED_CHAR_RE.finditer(text):
        start = m.start()
        end = m.end()
        while start > 0 and not text[start - 1].isspace():
            start -= 1
        while end < len(text) and not text[end].isspace():
            end += 1
        if start not in seen_start:
            seen_start.add(start)
            out.append(("latin_extended", start, text[start:end], path_str))
    return out


SCANNER_REGISTRY: list[dict] = [
    {
        "name": "scan_turn",
        "scan": _scan_turn,
        "filter_result": _scan_turn_filter,
        "scan_batch": _scan_turn_batch,
    },
    {"name": "scan_turn_latin", "scan": _scan_turn_latin},
    {"name": "quotes", "scan": scan_turn_quotes},
    {"name": "dashes", "scan": scan_turn_dashes},
    {"name": "non_speech_brackets", "scan": scan_turn_non_speech_brackets},
    {"name": "digit_letter", "scan": scan_turn_digit_letter},
    {"name": "known_names", "scan": scan_turn_known_names},
    {"name": "known_mixed_case", "scan": scan_turn_known_mixed_case},
    {"name": "all_caps_accept", "scan": scan_turn_all_caps_accept},
    {"name": "numbered_list", "scan": scan_turn_numbered_list},
    {"name": "symbols", "scan": scan_turn_symbols},
    {"name": "title_abbreviation", "scan": scan_turn_title_abbreviation},
    {"name": "short_mixed_acronym", "scan": scan_turn_short_mixed_acronym},
    {"name": "pascal_case_accept", "scan": scan_turn_pascal_case_accept},
    {"name": "trailing_dash_accept", "scan": scan_turn_trailing_dash_accept},
    {"name": "mixed_case_accept_6plus", "scan": scan_turn_mixed_case_accept_6plus},
    {"name": "name_pattern_di", "scan": scan_turn_name_pattern_di},
    {"name": "bracket_sentence_unwrap", "scan": scan_turn_bracket_sentence},
    {"name": "website_dot", "scan": scan_turn_website_dot},
    {"name": "concatenated_word_split", "scan": scan_turn_concatenated_word},
    {"name": "split_word_merge", "scan": scan_turn_split_word_merge},
    {"name": "repeated_word_accept", "scan_batch": scan_batch_repeated_word_accept},
    {
        "name": "global_repeated_word_accept",
        "scan_batch_global": scan_batch_global_repeated_word_accept,
    },
    {"name": "replacement_char_fix", "scan": scan_turn_replacement_char_fix},
    {"name": "invalid_question_mark_fix", "scan": scan_turn_invalid_question_mark},
    {"name": "common_acronym", "scan": scan_turn_common_acronym},
    {"name": "special_currency", "scan": scan_turn_special_currency},
    {"name": "dual_notation", "scan": scan_turn_dual_notation},
    {"name": "fraction", "scan": scan_turn_fraction},
    {"name": "half_number", "scan": scan_turn_half_number},
    {"name": "section_header", "scan": scan_turn_section_header},
    {"name": "letter_dash", "scan": scan_turn_letter_dash},
    {"name": "letter_roman_clause", "scan": scan_turn_letter_roman_clause},
    {"name": "roman_parens", "scan": scan_turn_roman_parens},
    {"name": "bracket_acronym", "scan": scan_turn_bracket_acronym},
    {"name": "single_digit_valid_word", "scan": scan_turn_single_digit_valid_word},
    {"name": "editorial_dollar", "scan": scan_turn_editorial_dollar},
    {"name": "inline_typo", "scan": scan_turn_inline_typo},
    {
        "name": "typo_levenshtein",
        "scan": scan_turn_typo_levenshtein,
        "transcript_words": True,
    },
]

SCANNER_NAME_TO_RULE_IDS: dict[str, list[str]] = {
    "scan_turn": list(RULE_REGEX),
    "scan_turn_latin": ["latin_extended"],
    "quotes": ["open_double_quote", "close_double_quote"],
    "dashes": ["dash"],
    "non_speech_brackets": ["non_speech_brackets"],
    "digit_letter": ["digit_letter_mixed"],
    "known_names": ["known_names"],
    "known_mixed_case": ["known_mixed_case_entities"],
    "all_caps_accept": ["all_caps_accept"],
    "numbered_list": ["numbered_list_marker"],
    "symbols": [
        "currency",
        "symbol_section_ref",
        "symbol_section",
        "symbol_copyright",
        "symbol_pound",
    ],
    "title_abbreviation": ["title_abbreviation"],
    "short_mixed_acronym": ["short_mixed_acronym"],
    "pascal_case_accept": ["pascal_case_accept"],
    "trailing_dash_accept": ["trailing_dash_accept"],
    "mixed_case_accept_6plus": ["mixed_case_accept_6plus"],
    "name_pattern_di": ["name_pattern_di"],
    "bracket_sentence_unwrap": ["bracket_sentence_unwrap"],
    "website_dot": ["website_dot"],
    "concatenated_word_split": ["concatenated_word_split"],
    "split_word_merge": ["split_word_merge"],
    "repeated_word_accept": ["repeated_word_accept"],
    "global_repeated_word_accept": ["global_repeated_word_accept"],
    "replacement_char_fix": ["replacement_char_fix"],
    "invalid_question_mark_fix": ["invalid_question_mark_fix"],
    "common_acronym": ["common_acronym"],
    "special_currency": ["special_currency"],
    "dual_notation": ["dual_notation"],
    "fraction": ["fraction"],
    "half_number": ["half_number"],
    "section_header": ["section_header"],
    "letter_dash": ["letter_dash_sequence"],
    "letter_roman_clause": ["letter_roman_clause"],
    "roman_parens": ["roman_parens"],
    "bracket_acronym": ["bracket_acronym"],
    "single_digit_valid_word": ["single_digit_valid_word"],
    "editorial_dollar": ["editorial_dollar"],
    "inline_typo": ["inline_typo"],
    "typo_levenshtein": ["typo_levenshtein"],
}
