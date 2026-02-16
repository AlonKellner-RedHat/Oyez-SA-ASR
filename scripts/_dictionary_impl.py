# Edited by Cursor: implementation for dictionary_loader (lintok split).
"""Implementation: WordNet/enchant/legal dict cascade for English word checking."""

from __future__ import annotations

import logging
from pathlib import Path

_logger = logging.getLogger(__name__)

_CACHE: frozenset[str] | _EnchantChecker | _CascadeChecker | None = None
_ALLOW_NO_ENCHANT = False
_WORDNET_MIN_LEN = 4
_wordnet_corpus: object | None = None
_stemmer: object | None = None
_LEGAL_DICT_PATH = Path("data/legal_words.txt")
_legal_dict_path_override: Path | None = None


def _get_wordnet() -> object:
    """Load WordNet once and return the corpus; reused in _wordnet_check."""
    global _wordnet_corpus  # noqa: PLW0603
    if _wordnet_corpus is None:
        import nltk  # noqa: PLC0415

        nltk.download("wordnet", quiet=True)
        from nltk.corpus import wordnet as wn  # noqa: PLC0415

        _wordnet_corpus = wn
    return _wordnet_corpus


def set_allow_no_enchant(allow: bool) -> None:
    """If True, allow fallback to word list when enchant is unavailable."""
    global _ALLOW_NO_ENCHANT  # noqa: PLW0603
    _ALLOW_NO_ENCHANT = allow


def set_legal_dict_path_for_testing(path: Path | None) -> None:
    """Override path to legal words file for tests. Pass None to reset."""
    global _legal_dict_path_override  # noqa: PLW0603
    _legal_dict_path_override = path


def _get_legal_dict_path() -> Path:
    """Path to legal words file (override for testing or default)."""
    if _legal_dict_path_override is not None:
        return _legal_dict_path_override
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


def _get_stemmer() -> object:
    """Return lazy-loaded SnowballStemmer for English."""
    global _stemmer  # noqa: PLW0603
    if _stemmer is None:
        from nltk.stem import SnowballStemmer  # noqa: PLC0415

        _stemmer = SnowballStemmer("english")
    return _stemmer


def _word_candidates(w: str) -> set[str]:
    """Return w plus morphy bases, stem, and suffix/prefix-derived forms."""
    out: set[str] = set()
    w_lower = w.lower()
    if w_lower:
        out.add(w_lower)
    if len(w_lower) < _WORDNET_MIN_LEN:
        return out
    if w_lower.endswith("atable") and len(w_lower) > 6:
        c = w_lower[:-6] + "ate"
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
    if w_lower.endswith("able") and len(w_lower) > 5:
        c = w_lower[:-4] + "e"
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
    if w_lower.startswith("un") and len(w_lower) > 4:
        c = w_lower[2:]
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
    if w_lower.startswith("pre") and len(w_lower) > 5:
        c = w_lower[3:]
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
    if w_lower.endswith("rability") and len(w_lower) > 8:
        c = w_lower[:-8] + "er"
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
    if w_lower.endswith("ability") and len(w_lower) > 9:
        c = w_lower[:-7] + "able"
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
        stem7 = w_lower[:-7]
        if len(stem7) >= _WORDNET_MIN_LEN and stem7.endswith("g"):
            c2 = stem7 + "eable"
            if len(c2) >= _WORDNET_MIN_LEN:
                out.add(c2)
    if w_lower.endswith("ity") and len(w_lower) > 6:
        c = w_lower[:-3]
        if len(c) >= 6:
            out.add(c)
    if w_lower.endswith("ily") and len(w_lower) > 5:
        c = w_lower[:-3] + "y"
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
    if w_lower.endswith("ly") and len(w_lower) > 4:
        c = w_lower[:-2]
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
    if w_lower.endswith("ment") and len(w_lower) > 6:
        c = w_lower[:-4]
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
    if w_lower.endswith("ency") and len(w_lower) > 6:
        c = w_lower[:-4] + "ent"
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
    if w_lower.endswith("ization") and len(w_lower) > 8:
        c = w_lower[:-7] + "ize"
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
    if w_lower.endswith("isation") and len(w_lower) > 8:
        c = w_lower[:-7] + "ise"
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
    if w_lower.startswith("non") and len(w_lower) > 6:
        c = w_lower[3:]
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
    if w_lower.startswith("mal") and len(w_lower) > 5:
        c = w_lower[3:]
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
    if w_lower.endswith("ance") and len(w_lower) > 6:
        c = w_lower[:-4] + "ant"
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
    if w_lower.endswith("ary") and len(w_lower) > 5:
        c = w_lower[:-3]
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
    if w_lower.endswith("ize") and len(w_lower) >= 6:
        c = w_lower[:-3] + "ise"
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
    if w_lower.endswith("ation") and len(w_lower) > 7:
        c = w_lower[:-5] + "e"
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
    if w_lower.endswith("ably") and len(w_lower) > 5:
        c = w_lower[:-1] + "e"
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
    if w_lower.endswith("atize") and len(w_lower) > 6:
        c = w_lower[:-5] + "ate"
        if len(c) >= _WORDNET_MIN_LEN:
            out.add(c)
    try:
        wn = _get_wordnet()
        for pos in ("n", "v", "a", "r"):
            base = wn.morphy(w_lower, pos)  # type: ignore[attr-defined]
            if base and len(base) >= _WORDNET_MIN_LEN:
                out.add(base)
        stemmer = _get_stemmer()
        stem = stemmer.stem(w_lower)  # type: ignore[attr-defined]
        if stem:
            out.add(stem)
    except Exception as e:
        _logger.debug("WordNet/stemmer lookup failed for %r: %s", w_lower, e)
    return out


def _wordnet_check(w: str) -> bool:
    """Return True if w is in WordNet (synsets or morphy base form)."""
    try:
        wn = _get_wordnet()
        if wn.synsets(w):  # type: ignore[attr-defined]
            return True
        for pos in ("n", "v", "a", "r"):
            base = wn.morphy(w, pos)  # type: ignore[attr-defined]
            if base and wn.synsets(base):  # type: ignore[attr-defined]
                return True
        return False
    except Exception:
        return False


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


def _enchant_providers_for_tag(tag: str) -> list[str]:
    """Read enchant.ordering and return provider names for tag in cascade order."""
    for path in (
        "/usr/share/enchant-2/enchant.ordering",
        "/usr/share/enchant/enchant.ordering",
    ):
        try:
            with open(path, encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    if ":" not in line:
                        continue
                    lang, order = line.split(":", 1)
                    if lang.strip() == tag:
                        return [p.strip() for p in order.split(",") if p.strip()]
        except OSError:
            continue
    return []


def _build_enchant_dicts_for_tag(tag: str) -> list:
    """Build list of enchant Dict for one language tag (one per provider), cascade order."""
    import enchant  # noqa: PLC0415

    dicts_list: list = []
    seen_providers: set[str] = set()
    providers = _enchant_providers_for_tag(tag)
    if providers:
        for prov_name in providers:
            try:
                broker = enchant.Broker()
                broker.set_ordering(tag, prov_name)
                d = broker.request_dict(tag)
                pname = d.provider.name  # type: ignore[attr-defined]
                if pname not in seen_providers:
                    dicts_list.append(d)
                    seen_providers.add(pname)
            except Exception:  # noqa: S110
                pass
    if not dicts_list:
        try:
            default = enchant.Dict(tag)
            dicts_list = [default]
            try:
                broker = enchant.Broker()
                seen = {default.provider.name}  # type: ignore[attr-defined]
                for list_tag, prov in broker.list_dicts():
                    if list_tag == tag and prov.name not in seen:
                        try:
                            b2 = enchant.Broker()
                            b2.set_ordering(tag, prov.name)
                            d2 = b2.request_dict(tag)
                            dicts_list.append(d2)
                            seen.add(prov.name)
                        except Exception:  # noqa: S110
                            pass
            except Exception:  # noqa: S110
                pass
        except Exception:  # noqa: S110
            pass
    return dicts_list


def _build_enchant_dicts() -> list:
    """Build list of enchant Dict: en_US first, then la (Latin) if available."""
    dicts_list: list = _build_enchant_dicts_for_tag("en_US")
    if not dicts_list:
        return dicts_list
    latin_dicts = _build_enchant_dicts_for_tag("la")
    dicts_list.extend(latin_dicts)
    return dicts_list


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
