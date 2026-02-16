# Edited by Cursor: thin re-export (lintok; no new exclusions).
"""Implementation: WordNet/enchant/legal dict cascade for English word checking."""

from scripts._dictionary_impl_enchant import (
    _ALLOW_NO_ENCHANT,
    _CACHE,
    SINGLE_LETTER_RULE_ALLOWED,
    _CascadeChecker,
    _EnchantChecker,
    get_english_dictionary,
    is_valid_word,
    is_valid_word_for_rules,
    set_allow_no_enchant,
    set_legal_dict_path_for_testing,
)
from scripts._dictionary_impl_wordnet import _word_candidates

__all__ = [
    "SINGLE_LETTER_RULE_ALLOWED",
    "_ALLOW_NO_ENCHANT",
    "_CACHE",
    "_CascadeChecker",
    "_EnchantChecker",
    "_word_candidates",
    "get_english_dictionary",
    "is_valid_word",
    "is_valid_word_for_rules",
    "set_allow_no_enchant",
    "set_legal_dict_path_for_testing",
]
