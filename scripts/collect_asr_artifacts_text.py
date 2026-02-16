# Edited by Cursor: text/speaker extraction for collect_asr_artifacts (lintok split).
"""Extract artifact candidates from single-turn text and speaker lists."""

import re
from collections import Counter

from scripts.collect_asr_artifacts_regex import (
    _BRACKET_CONTENT_MAX,
    _NON_SPEECH_CONTENT_RE,
    ABBREV_RE,
    ACRONYM_RE,
    ACRONYM_STOPLIST,
    ALL_CAPS_LONG_RE,
    AWARENESS_SYMBOLS,
    BRACKETS_ANGLE_RE,
    BRACKETS_CURLY_RE,
    BRACKETS_NUMBERED_RE,
    BRACKETS_PAREN_RE,
    BRACKETS_SQUARE_RE,
    CASE_ID_RE,
    CURRENCY_RE,
    DASH_RANGE_RE,
    DECADE_RE,
    EDITORIAL_SQUARE_RE,
    ET_AL_RE,
    HISTORICAL_YEAR_RE,
    LEADING_DECIMAL_RE,
    MIXED_CASE_RE,
    MONTH_YEAR_RE,
    NO_DOT_CITATION_RE,
    NO_DOT_NEXT_RE,
    ORDINAL_RE,
    ORDINAL_WORD_RE,
    PERCENTAGE_RE,
    ROMAN_NUMERAL_RE,
    SECTION_RE,
    STANDALONE_CAP_RE,
    STATUTE_USC_RE,
    STRUCTURAL_PAREN_LETTER_RE,
    STRUCTURAL_PAREN_NUM_RE,
    TIME_LIKE_RE,
    TITLE_N_RE,
    UNSPOKEN_HEADER_PHRASES,
    VERSUS_RE,
    VOTE_TALLY_RE,
    YEAR_RE,
)


def _add(counter: Counter[str], key: str, normalize: bool = True) -> None:
    token = key.strip()
    if not token:
        return
    if normalize:
        token = token.replace("  ", " ").strip()
    counter[token] += 1


def _normalize_currency(s: str) -> str:
    """Canonical form for currency (strip commas) for counting."""
    return s.replace(",", "")


def _normalize_percentage(s: str) -> str:
    """Canonical form for percentage (digit + %) for counting."""
    s = s.strip().replace(" ", "")
    if s.endswith("percent"):
        return s.replace("percent", "%")
    return s


def collect_from_text(text: str, artifacts: dict[str, Counter[str]]) -> None:
    """Extract artifact candidates from a single turn text."""
    if not text or not isinstance(text, str):
        return
    for m in CASE_ID_RE.finditer(text):
        tok = m.group(1)
        if VOTE_TALLY_RE.fullmatch(tok):
            _add(artifacts["vote_tally"], tok)
        else:
            _add(artifacts["case_ids"], tok)
    for m in YEAR_RE.finditer(text):
        _add(artifacts["years"], m.group(1))
    for m in ABBREV_RE.finditer(text):
        _add(artifacts["abbreviations"], m.group(0))
    for m in VERSUS_RE.finditer(text):
        _add(artifacts["versus"], m.group(1))
    for m in ORDINAL_RE.finditer(text):
        _add(artifacts["ordinals"], m.group(0))
    for m in SECTION_RE.finditer(text):
        _add(artifacts["section_refs"], m.group(1).strip())
    for m in MONTH_YEAR_RE.finditer(text):
        _add(artifacts["dates_month_year"], m.group(0))
    for m in STANDALONE_CAP_RE.finditer(text):
        _add(artifacts["likely_initials"], m.group(0))
    for m in ACRONYM_RE.finditer(text):
        tok = m.group(1)
        if len(tok) == 2 and tok in ACRONYM_STOPLIST:
            continue
        _add(artifacts["acronyms"], tok)
    for m in CURRENCY_RE.finditer(text):
        _add(artifacts["currency"], _normalize_currency(m.group(0)))
    for m in HISTORICAL_YEAR_RE.finditer(text):
        _add(artifacts["historical_years"], m.group(1))
    for phrase in UNSPOKEN_HEADER_PHRASES:
        if phrase in text:
            artifacts["unspoken_headers"][phrase] += 1
    for m in NO_DOT_NEXT_RE.finditer(text):
        _add(artifacts["no_dot_context"], m.group(1))
    for m in NO_DOT_CITATION_RE.finditer(text):
        _add(artifacts["no_dot_citation"], m.group(0))
    for m in ROMAN_NUMERAL_RE.finditer(text):
        _add(artifacts["roman_numerals"], m.group(1))
    for m in PERCENTAGE_RE.finditer(text):
        _add(artifacts["percentages"], _normalize_percentage(m.group(0)))
    for m in DECADE_RE.finditer(text):
        _add(artifacts["decades"], m.group(0))
    for _m in ET_AL_RE.finditer(text):
        _add(artifacts["abbreviations"], "et al.")
    for m in ORDINAL_WORD_RE.finditer(text):
        _add(artifacts["ordinals_word"], m.group(1))
    for m in STATUTE_USC_RE.finditer(text):
        _add(artifacts["statute_citation"], m.group(0).strip())
    for m in TITLE_N_RE.finditer(text):
        _add(artifacts["statute_citation"], m.group(0).strip())
    for c in text:
        if ord(c) > 127:
            artifacts["awareness_non_ascii"][f"U+{ord(c):04X}"] += 1
    for m in MIXED_CASE_RE.finditer(text):
        _add(artifacts["awareness_mixed_case"], m.group(0), normalize=False)
    for m in ALL_CAPS_LONG_RE.finditer(text):
        _add(artifacts["awareness_all_caps_long"], m.group(0), normalize=False)
    for sym in AWARENESS_SYMBOLS:
        if sym in text:
            artifacts["awareness_symbols"][f"U+{ord(sym):04X}"] += 1
    if "..." in text:
        artifacts["awareness_symbols"]["..."] += 1
    for m in BRACKETS_PAREN_RE.finditer(text):
        content = m.group(1).strip()
        if len(content) > _BRACKET_CONTENT_MAX:
            content = content[:_BRACKET_CONTENT_MAX] + "..."
        key = f"({content})" if content else "()"
        artifacts["awareness_brackets_parens"][key] += 1
        norm = content.strip().rstrip(".").strip()
        if norm and _NON_SPEECH_CONTENT_RE.search(norm):
            artifacts["non_speech_brackets"][key] += 1
    for m in BRACKETS_SQUARE_RE.finditer(text):
        content = m.group(1).strip()
        if len(content) > _BRACKET_CONTENT_MAX:
            content = content[:_BRACKET_CONTENT_MAX] + "..."
        key = f"[{content}]" if content else "[]"
        artifacts["awareness_brackets_square"][key] += 1
        norm = content.strip().rstrip(".").strip()
        if norm and _NON_SPEECH_CONTENT_RE.search(norm):
            artifacts["non_speech_brackets"][key] += 1
    for m in BRACKETS_CURLY_RE.finditer(text):
        content = m.group(1).strip()
        if len(content) > _BRACKET_CONTENT_MAX:
            content = content[:_BRACKET_CONTENT_MAX] + "..."
        key = f"{{{content}}}" if content else "{}"
        artifacts["awareness_brackets_curly"][key] += 1
    for m in BRACKETS_NUMBERED_RE.finditer(text):
        artifacts["awareness_brackets_numbered"][m.group(0)] += 1
        artifacts["numbered_list_marker"][m.group(0)] += 1
    for m in BRACKETS_ANGLE_RE.finditer(text):
        key = m.group(0)
        if len(key) > _BRACKET_CONTENT_MAX + 2:
            key = key[: _BRACKET_CONTENT_MAX + 1] + "...>"
        artifacts["awareness_brackets_angle"][key] += 1
    for m in EDITORIAL_SQUARE_RE.finditer(text):
        artifacts["editorial_square_bracket"][m.group(0)] += 1
    for m in DASH_RANGE_RE.finditer(text):
        artifacts["dash_range"][m.group(0)] += 1
    for _ in re.finditer(r"\.\.\.", text):
        artifacts["ellipsis"]["..."] += 1
    if "\u2026" in text:
        artifacts["ellipsis"]["U+2026"] += text.count("\u2026")
    for m in STRUCTURAL_PAREN_LETTER_RE.finditer(text):
        artifacts["structural_bracket"][m.group(0)] += 1
    for m in STRUCTURAL_PAREN_NUM_RE.finditer(text):
        artifacts["structural_bracket"][m.group(0)] += 1
    for m in TIME_LIKE_RE.finditer(text):
        artifacts["awareness_time_like"][m.group(0)] += 1
    for m in LEADING_DECIMAL_RE.finditer(text):
        frag = m.group(1)
        artifacts["awareness_leading_decimal"][frag] += 1
        if len(frag) != 5 or not (frag.startswith(".1") or frag.startswith(".2")):
            artifacts["leading_decimal"][frag] += 1


def collect_from_speakers(
    speakers: list[dict], artifacts: dict[str, Counter[str]]
) -> None:
    """Extract titles/initials from speaker names (e.g. Jr., Sr., middle initial)."""
    if not speakers:
        return
    for s in speakers:
        name = (s or {}).get("name") if isinstance(s, dict) else None
        if not name or not isinstance(name, str):
            continue
        if ", Jr." in name or " Jr." in name:
            artifacts["abbreviations"]["Jr."] += 1
        if ", Sr." in name or " Sr." in name:
            artifacts["abbreviations"]["Sr."] += 1
        for m in re.finditer(r"\b([A-Z])\.", name):
            _add(artifacts["likely_initials"], m.group(0))
