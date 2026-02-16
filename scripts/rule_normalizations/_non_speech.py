# Edited by Cursor: extracted from __init__.py for lintok.
"""Non-speech content detection for bracket removal."""

from scripts.rule_normalizations._constants import (
    NON_SPEECH_AUDIO_CUT_RE,
    NON_SPEECH_BRACKET_CONTENT,
    NON_SPEECH_KEYWORDS,
)

_NON_SPEECH_LEV_MAX_LEN = 60
_NON_SPEECH_LEV_MAX = 2


def is_non_speech_content(content_norm: str) -> bool:
    """Return True if exact match, keyword, audio cut, or within 2 Lev of allowlist."""
    if content_norm in NON_SPEECH_BRACKET_CONTENT:
        return True
    if any(kw in content_norm for kw in NON_SPEECH_KEYWORDS):
        return True
    if NON_SPEECH_AUDIO_CUT_RE.search(content_norm):
        return True
    if len(content_norm) <= _NON_SPEECH_LEV_MAX_LEN:
        from scripts.typo_distances import levenshtein_distance  # noqa: PLC0415

        for phrase in NON_SPEECH_BRACKET_CONTENT:
            if levenshtein_distance(content_norm, phrase) <= _NON_SPEECH_LEV_MAX:
                return True
    return False
