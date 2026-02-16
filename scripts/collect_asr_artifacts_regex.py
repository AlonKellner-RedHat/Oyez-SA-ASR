# Edited by Cursor: regex constants for collect_asr_artifacts (lintok split).
"""Regex and constants for ASR artifact collection."""

import re

# Case/docket: 1-2 digits, hyphen, digits (e.g. 19-1392, 94-1039)
CASE_ID_RE = re.compile(r"\b(\d{1,2}-\d+)\b")
YEAR_RE = re.compile(r"\b((?:19|20)\d{2})\b")
ABBREV_RE = re.compile(
    r"\b(Inc|No|Jr|Sr|Mr|Mrs|Ms|Dr|Gen|Gov|Hon|Sec|Rep|Sen|Prof|St|Vol|Ed|Rev|cf|e\.g|i\.e|etc|vs)\.(?=\s|$|[,\)])",
    re.IGNORECASE,
)
VERSUS_RE = re.compile(r"\b(vs?\.?)\s+(?=[A-Z])", re.IGNORECASE)
ORDINAL_RE = re.compile(r"\b\d+(?:st|nd|rd|th)\b", re.IGNORECASE)
SECTION_RE = re.compile(r"(§|¶|\bSection\s+\d+[\w\(\)\-]*)", re.IGNORECASE)
ACRONYM_RE = re.compile(r"\b([A-Z]{2,5})\b")
ACRONYM_STOPLIST = frozenset(
    {
        "IT",
        "DO",
        "US",
        "SO",
        "OR",
        "NO",
        "IF",
        "AS",
        "AT",
        "BE",
        "BY",
        "HE",
        "ME",
        "WE",
        "AN",
    }
)
CURRENCY_RE = re.compile(r"[$£][\d,]+(?:\.[\d]+)?")
HISTORICAL_YEAR_RE = re.compile(r"\b(1[0-8]\d{2})\b")
UNSPOKEN_HEADER_PHRASES = (
    "ORAL ARGUMENT OF",
    "REBUTTAL OF",
    "RESUMED ORAL ARGUMENT OF",
)
MONTH_YEAR_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\b",
    re.IGNORECASE,
)
STANDALONE_CAP_RE = re.compile(r"(?<=\s)([A-Z])\.(?=\s|$)")
NO_DOT_NEXT_RE = re.compile(r"\bNo\.\s+(\S+)", re.IGNORECASE)
NO_DOT_CITATION_RE = re.compile(r"\bNo\.\s+(\d+-\d+)", re.IGNORECASE)
VOTE_TALLY_RE = re.compile(r"\b(\d-\d)\b")
ROMAN_NUMERAL_RE = re.compile(r"\b(VIII|VII|XII|XI|III|IX|VI|IV|II|V|X)\b")
PERCENTAGE_RE = re.compile(r"\d+(?:%|\s*percent)")
DECADE_RE = re.compile(r"\b(?:(?:18|19|20)\d{2}s|\d{2}s)\b")
ET_AL_RE = re.compile(r"\bet\s+al\.?", re.IGNORECASE)
ORDINAL_WORD_RE = re.compile(
    r"\b(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|"
    r"Eleventh|Twelfth)\b",
    re.IGNORECASE,
)
STATUTE_USC_RE = re.compile(r"\d+\s*U\.?S\.?C\.?", re.IGNORECASE)
TITLE_N_RE = re.compile(r"Title\s+\d+", re.IGNORECASE)
MIXED_CASE_RE = re.compile(r"\b[A-Z][a-z]+[A-Z]\w*\b")
ALL_CAPS_LONG_RE = re.compile(r"\b[A-Z]{6,}\b")
AWARENESS_SYMBOLS = ("\u2026", "\u2013", "\u2014", "\u2020", "\u2021", "\u2022")
BRACKETS_PAREN_RE = re.compile(r"\(([^)]*)\)")
BRACKETS_SQUARE_RE = re.compile(r"\[([^\]]*)\]")
BRACKETS_CURLY_RE = re.compile(r"\{([^}]*)\}")
BRACKETS_ANGLE_RE = re.compile(r"<[^>]*>")
BRACKETS_NUMBERED_RE = re.compile(r"\b\d+\)")
LEADING_DECIMAL_RE = re.compile(r"(?<!\d)(\.\d+)")
TIME_LIKE_RE = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?\b")
EDITORIAL_SQUARE_RE = re.compile(r"\[=\s*([^\]]*)\]")
DASH_RANGE_RE = re.compile(r"\d+[\u2013\u2014-]\d+")
STRUCTURAL_PAREN_LETTER_RE = re.compile(r"\(([a-zA-Z])\)")
STRUCTURAL_PAREN_NUM_RE = re.compile(r"\((\d{1,2})\)")
_NON_SPEECH_CONTENT_RE = re.compile(
    r"(?i)^(inaudible|voice\s*overlap|laughter|coughing|audio\s*cut|"
    r"recess|dollars|noise|ph|indiscernible|mirth|sneezes|sighs|"
    r"applause|break|luncheon|lunch|interruption|banging|attempt\s*to\s*laughter|"
    r"laughter\s*attempt)"
    r"\.?$"
)
_BRACKET_CONTENT_MAX = 80
