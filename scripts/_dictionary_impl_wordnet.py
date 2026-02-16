# Edited by Cursor: WordNet/stemmer/candidates (lintok; no new exclusions).
"""WordNet corpus, stemmer, and word candidates for dictionary cascade."""

from __future__ import annotations

import logging

_logger = logging.getLogger(__name__)

_WORDNET_MIN_LEN = 4
_wordnet_corpus: object | None = None
_stemmer: object | None = None


def _get_wordnet() -> object:
    """Load WordNet once and return the corpus; reused in _wordnet_check."""
    global _wordnet_corpus  # noqa: PLW0603
    if _wordnet_corpus is None:
        import nltk  # noqa: PLC0415

        nltk.download("wordnet", quiet=True)
        from nltk.corpus import wordnet as wn  # noqa: PLC0415

        _wordnet_corpus = wn
    return _wordnet_corpus


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
