# Edited by Cursor: thin API re-export for lintok (impl in _dictionary_impl).
"""Load English word checker for concatenated-word split and non-dictionary awareness.

Cascade: (1) enchant en_US, (2) enchant la (Latin, if installed),
(3) NLTK WordNet, (4) legal dict (data/legal_words.txt when present).
"""

from scripts import _dictionary_impl
from scripts._dictionary_impl import (
    SINGLE_LETTER_RULE_ALLOWED,
    _CascadeChecker,
    _EnchantChecker,
    _word_candidates,
    get_english_dictionary,
    is_valid_word,
    is_valid_word_for_rules,
    set_allow_no_enchant,
    set_legal_dict_path_for_testing,
)

__all__ = [
    "SINGLE_LETTER_RULE_ALLOWED",
    "_CascadeChecker",
    "_EnchantChecker",
    "_dictionary_impl",
    "_word_candidates",
    "get_english_dictionary",
    "is_valid_word",
    "is_valid_word_for_rules",
    "set_allow_no_enchant",
    "set_legal_dict_path_for_testing",
]
