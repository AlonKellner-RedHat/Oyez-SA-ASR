# Edited by Cursor: SCANNER_REGISTRY list (lintok; no new exclusions).
"""Scanner registry list."""

from scripts.build_rule_candidates_registry_scanners_helpers import (
    _scan_turn,
    _scan_turn_batch,
    _scan_turn_filter,
    _scan_turn_latin,
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
