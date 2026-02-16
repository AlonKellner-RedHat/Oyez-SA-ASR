#!/usr/bin/env python3
# Edited by Cursor (lintok split: regex + normalizers + scanners + thin re-export)
"""Registry of rule regexes, normalizers, and scanners for build_rule_candidates."""

from scripts.build_rule_candidates_registry_normalizers import (
    ALL_RULE_IDS,
    RULE_LABELS,
    RULE_NORMALIZER,
)
from scripts.build_rule_candidates_registry_regex import (
    LATIN_EXTENDED_CHAR_RE,
    LATIN_EXTENDED_RANGE,
    NUMBER_PARENS_RE,
    RULE_REGEX,
    TIME_OF_DAY_RE,
    WORD_RE,
)
from scripts.build_rule_candidates_registry_scanners import (
    SCANNER_NAME_TO_RULE_IDS,
    SCANNER_REGISTRY,
)

__all__ = [
    "ALL_RULE_IDS",
    "LATIN_EXTENDED_CHAR_RE",
    "LATIN_EXTENDED_RANGE",
    "NUMBER_PARENS_RE",
    "RULE_LABELS",
    "RULE_NORMALIZER",
    "RULE_REGEX",
    "SCANNER_NAME_TO_RULE_IDS",
    "SCANNER_REGISTRY",
    "TIME_OF_DAY_RE",
    "WORD_RE",
]
