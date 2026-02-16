# Edited by Cursor: extracted from __init__.py for lintok.
"""Constants and regexes for rule normalizations."""

import re

# Literal pronunciation of single letter (a->ay, b->bee, ...). Used by single_letter_parens rule.
LETTER_PRONUNCIATION: dict[str, str] = {
    "a": "ay",
    "b": "bee",
    "c": "cee",
    "d": "dee",
    "e": "ee",
    "f": "eff",
    "g": "gee",
    "h": "aych",
    "i": "eye",
    "j": "jay",
    "k": "kay",
    "l": "ell",
    "m": "em",
    "n": "en",
    "o": "oh",
    "p": "pee",
    "q": "cue",
    "r": "ar",
    "s": "ess",
    "t": "tee",
    "u": "you",
    "v": "vee",
    "w": "double-u",
    "x": "ex",
    "y": "wy",
    "z": "zee",
}
STANDARD_DASH = "-"

# Non-speech bracket content (case-insensitive, after strip/rstrip dot).
NON_SPEECH_BRACKET_CONTENT = frozenset(
    {
        "inaudible",
        "voice overlap",
        "laughter",
        "laughs",
        "coughing",
        "audio cut",
        "recess",
        "indiscernible",
        "mirth",
        "sneezes",
        "sighs",
        "applause",
        "break",
        "luncheon",
        "lunch",
        "interruption",
        "banging",
        "attempt to laughter",
        "laughter attempt",
        "overlap",
        "sic",
        "ph",
    }
)
UNBRACKETED_NON_SPEECH_PHRASES = frozenset({"generallaughter", "general laughter"})
NON_SPEECH_KEYWORDS = ("inaudible", "laugh", "audio", "break", "recess", "lunch")

NON_SPEECH_AUDIO_CUT_RE = re.compile(
    r"(?i)audio\s+(abruptly\s+)?cut\s+\d{2}:\d{2}:\d{2}-\d{2}:\d{2}:\d{2}"
)
ORDINAL_SUFFIX_RE = re.compile(r"^(\d+)(st|nd|rd|th)$", re.IGNORECASE)

# Max content length to run Levenshtein vs NON_SPEECH_BRACKET_CONTENT.
_NON_SPEECH_LEV_MAX_LEN = 60
_NON_SPEECH_LEV_MAX = 2

# Title abbreviations (Mr.->Mister, Dr.->Doctor, etc.)
TITLE_ABBREVIATION_MAP: dict[str, str] = {
    "mr": "Mister",
    "dr": "Doctor",
    "mrs": "Misses",
    "ms": "Miss",
    "jr": "Junior",
    "sr": "Senior",
    "gen": "General",
    "gov": "Governor",
    "hon": "Honorable",
    "prof": "Professor",
    "rev": "Reverend",
    "sec": "Secretary",
    "rep": "Representative",
    "sen": "Senator",
}

# Abbreviated decade 00s-90s -> spoken.
ABBREV_DECADE_WORDS = (
    "hundreds",
    "tens",
    "twenties",
    "thirties",
    "forties",
    "fifties",
    "sixties",
    "seventies",
    "eighties",
    "nineties",
)

# Latin extended: uroman lang codes.
LATIN_UROMAN_LANGS = ("tur",)
