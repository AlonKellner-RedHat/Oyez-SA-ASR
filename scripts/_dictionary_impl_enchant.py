# Edited by Cursor: enchant/legal/cascade (lintok; no new exclusions).
"""Enchant dicts, legal set, cascade checker, and get_english_dictionary."""

from __future__ import annotations

import os
from pathlib import Path

from scripts._dictionary_impl_build import _build_enchant_dicts
from scripts._dictionary_impl_wordnet import (
    _WORDNET_MIN_LEN,
    _word_candidates,
    _wordnet_check,
)

_CACHE: frozenset[str] | _EnchantChecker | _CascadeChecker | None = None
_ALLOW_NO_ENCHANT = False
_LEGAL_DICT_PATH = Path("data/legal_words.txt")
_legal_dict_path_override: Path | None = None


def set_allow_no_enchant(allow: bool) -> None:
    """If True, allow fallback to word list when enchant is unavailable."""
    global _ALLOW_NO_ENCHANT  # noqa: PLW0603
    _ALLOW_NO_ENCHANT = allow


def set_legal_dict_path_for_testing(path: Path | None) -> None:
    """Override path to legal words file for tests. Pass None to reset."""
    global _legal_dict_path_override  # noqa: PLW0603
    _legal_dict_path_override = path


def _get_legal_dict_path() -> Path:
    """Path to legal words file (env override, testing override, or default)."""
    if _legal_dict_path_override is not None:
        return _legal_dict_path_override
    env_path = os.environ.get("LEGAL_WORDS_PATH")
    if env_path:
        return Path(env_path).resolve()
    return Path(__file__).resolve().parent.parent / _LEGAL_DICT_PATH


def _load_legal_set() -> frozenset[str]:
    """Load legal words from file; one word per line, lowercase, skip comments/empty."""
    path = _get_legal_dict_path()
    if not path.exists():
        return frozenset()
    words: set[str] = set()
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip().lower()
            if not line or line.startswith("#"):
                continue
            if line.isalpha() or (all(c.isalpha() or c == "'" for c in line)):
                words.add(line)
    return frozenset(words)


class _EnchantChecker:
    """Container that supports __contains__(word) via enchant spell check; caches results."""

    __slots__ = ("_cache", "_d")

    def __init__(self, d: object) -> None:
        self._d = d
        self._cache: dict[str, bool] = {}

    def __contains__(self, word: object) -> bool:
        if not isinstance(word, str):
            return False
        w = word.lower()
        if w not in self._cache:
            self._cache[w] = self._d.check(w)  # type: ignore[attr-defined]
        return self._cache[w]


class _CascadeChecker:
    """Check word via cascade: enchant dicts, WordNet, then legal dict."""

    __slots__ = ("_cache", "_dicts", "_legal_set", "_use_wordnet")

    def __init__(
        self,
        dicts: list,
        use_wordnet: bool = True,
        legal_set: frozenset[str] | None = None,
    ) -> None:
        self._dicts = dicts
        self._use_wordnet = use_wordnet
        self._legal_set = legal_set or frozenset()
        self._cache: dict[str, bool] = {}

    def __contains__(self, word: object) -> bool:
        if not isinstance(word, str):
            return False
        w = word.lower()
        if w not in self._cache:
            result = any(d.check(w) for d in self._dicts)  # type: ignore[attr-defined]
            if not result and self._use_wordnet and len(w) >= _WORDNET_MIN_LEN:
                result = _wordnet_check(w)
            if not result and self._legal_set and w in self._legal_set:
                result = True
            if not result and len(w) >= _WORDNET_MIN_LEN:
                for c in _word_candidates(w):
                    if c != w:
                        if any(d.check(c) for d in self._dicts):  # type: ignore[attr-defined]
                            result = True
                            break
                        if self._legal_set and c in self._legal_set:
                            result = True
                            break
                        if self._use_wordnet and _wordnet_check(c):
                            result = True
                            break
            if not result and (w.endswith("'") or w.endswith("'s")):
                stripped = w.rstrip("'")
                if stripped and stripped != w and stripped in self:
                    result = True
            self._cache[w] = result
        return self._cache[w]


def is_valid_word(
    word: str,
    checker: frozenset[str] | _CascadeChecker | _EnchantChecker,
) -> bool:
    """Return True if word is valid: in checker or (for frozenset) any stem/candidate in checker."""
    if isinstance(checker, frozenset):
        w = word.lower()
        if w in checker:
            return True
        if len(w) >= _WORDNET_MIN_LEN:
            for c in _word_candidates(w):
                if c in checker:
                    return True
        return False
    return word in checker  # type: ignore[operator]


SINGLE_LETTER_RULE_ALLOWED = frozenset({"a", "i", "v", "x"})


def is_valid_word_for_rules(
    word: str,
    checker: frozenset[str] | _CascadeChecker | _EnchantChecker,
) -> bool:
    """Return False if word is a single lowercase letter not in allowlist; else is_valid_word."""
    w = word.lower()
    if len(w) == 1 and w not in SINGLE_LETTER_RULE_ALLOWED:
        return False
    return is_valid_word(word, checker)


def get_english_dictionary() -> frozenset[str] | _EnchantChecker | _CascadeChecker:
    """Return a checker supporting 'word.lower() in result' for valid English; cached."""
    global _CACHE  # noqa: PLW0603
    if _CACHE is not None:
        return _CACHE
    try:
        dicts_list = _build_enchant_dicts()
        legal_set = _load_legal_set()
        _CACHE = _CascadeChecker(dicts_list, use_wordnet=True, legal_set=legal_set)
        return _CACHE
    except (ImportError, AttributeError, Exception) as e:
        if not _ALLOW_NO_ENCHANT:
            raise RuntimeError(
                "enchant (spell checker) is not available. Install system packages "
                "(e.g. apt install libenchant-2-2 enchant aspell-en) and ensure pyenchant "
                "can load Dict('en_US'). To allow fallback to a word list, pass --allow-no-enchant."
            ) from e
        from english_words import get_english_words_set  # noqa: PLC0415

        _CACHE = frozenset(get_english_words_set(["web2", "gcide"], lower=True))
        return _CACHE
