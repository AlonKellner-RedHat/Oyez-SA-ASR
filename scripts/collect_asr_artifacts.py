#!/usr/bin/env python3
# Edited by Cursor
"""
Collect potential transcription artifacts for ASR normalization.

Scans processed transcripts and gathers numbers, abbreviations, case IDs,
dates, person titles, and similar tokens that typically need conversion
before training an ASR model (e.g. "Inc." -> "incorporated", "No." -> "number").
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Case/docket: 1-2 digits, hyphen, digits (e.g. 19-1392, 94-1039)
CASE_ID_RE = re.compile(r"\b(\d{1,2}-\d+)\b")
# Four-digit years
YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
# Common abbreviations that may need expansion for ASR
ABBREV_RE = re.compile(
    r"\b(Inc|No|Jr|Sr|Mr|Mrs|Ms|Dr|Gen|Gov|Hon|Sec|Rep|Sen|Prof|St|Vol|Ed|Rev|cf|e\.g|i\.e|etc|vs)\.(?=\s|$|[,\)])",
    re.IGNORECASE,
)
# "versus" or "vs." as standalone
VERSUS_RE = re.compile(r"\b(vs?\.?)\s+(?=[A-Z])", re.IGNORECASE)
# Ordinals: 1st, 2nd, 3rd, 4th, ...
ORDINAL_RE = re.compile(r"\b(\d+)(st|nd|rd|th)\b", re.IGNORECASE)
# Section/paragraph symbols and "Section N"
SECTION_RE = re.compile(r"(§|¶|\bSection\s+\d+[\w\(\)\-]*)", re.IGNORECASE)
# ALL-CAPS acronyms (2-5 letters); exclude common 2-letter words
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
# Currency: $N or $N.NN
CURRENCY_RE = re.compile(r"\$[\d,]+(?:\.[\d]+)?")
# Historical years 1000-1899 (19xx/20xx in years)
HISTORICAL_YEAR_RE = re.compile(r"\b(1[0-8]\d{2})\b")
# Unspoken header phrases (literal substrings)
UNSPOKEN_HEADER_PHRASES = (
    "ORAL ARGUMENT OF",
    "REBUTTAL OF",
    "RESUMED ORAL ARGUMENT OF",
)
# Simple numeric date patterns: Month DD, YYYY or DD/MM/YYYY style
MONTH_YEAR_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\b",
    re.IGNORECASE,
)
# Standalone single capital letter (possible initial)
STANDALONE_CAP_RE = re.compile(r"(?<=\s)([A-Z])\.(?=\s|$)")
# "No." followed by next token (for negation vs number disambiguation)
NO_DOT_NEXT_RE = re.compile(r"\bNo\.\s+(\S+)", re.IGNORECASE)
# "No." followed by citation (docket-style: digits-hyphen-digits) -> expand to "number"
NO_DOT_CITATION_RE = re.compile(r"\bNo\.\s+(\d+-\d+)", re.IGNORECASE)
# Vote tally: single digit - single digit (9-0, 7-2); separate from case IDs
VOTE_TALLY_RE = re.compile(r"\b(\d-\d)\b")
# Roman numerals (legal: Amendment VII, Title II); exclude single I
ROMAN_NUMERAL_RE = re.compile(r"\b(II|III|IV|V|VI|VII|VIII|IX|X|XI|XII)\b")
# Percentages: 50% or 25 percent
PERCENTAGE_RE = re.compile(r"\d+%|\d+\s*percent")
# Decades: 1980s, 1930s
DECADE_RE = re.compile(r"\b(19|20)\d{2}s\b")
# Et al. (legal abbreviation)
ET_AL_RE = re.compile(r"\bet\s+al\.?", re.IGNORECASE)
# Word ordinals: Fifth, Seventh, Eighth (Circuit, Amendment)
ORDINAL_WORD_RE = re.compile(
    r"\b(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|"
    r"Eleventh|Twelfth)\b",
    re.IGNORECASE,
)
# Statute citation: 21 U.S.C. or Title 18
STATUTE_USC_RE = re.compile(r"\d+\s*U\.?S\.?C\.?", re.IGNORECASE)
TITLE_N_RE = re.compile(r"Title\s+\d+", re.IGNORECASE)
# Awareness (unestablished rules): non-ASCII, mixed case, long all-caps, symbols
MIXED_CASE_RE = re.compile(r"\b[A-Z][a-z]+[A-Z]\w*\b")
ALL_CAPS_LONG_RE = re.compile(r"\b[A-Z]{6,}\b")
# Typographic/legal symbols beyond § ¶ $
AWARENESS_SYMBOLS = ("\u2026", "\u2013", "\u2014", "\u2020", "\u2021", "\u2022")
# Awareness: bracket usages — (aaa), [aaa], {aaa}, 1) etc. Edited by Cursor.
BRACKETS_PAREN_RE = re.compile(r"\(([^)]*)\)")
BRACKETS_SQUARE_RE = re.compile(r"\[([^\]]*)\]")
BRACKETS_CURLY_RE = re.compile(r"\{([^}]*)\}")
BRACKETS_NUMBERED_RE = re.compile(r"\b\d+\)")
# Awareness: leading decimals (.66, .5) — may be pronounced "point six six".
LEADING_DECIMAL_RE = re.compile(r"(?<!\d)(\.\d+)")
# Editorial [= X]: replace with normalized X then strip. Edited by Cursor.
EDITORIAL_SQUARE_RE = re.compile(r"\[=\s*([^\]]*)\]")
# Dash range N-M (en/em dash or hyphen) for "N to M" rule.
DASH_RANGE_RE = re.compile(r"\d+[\u2013\u2014-]\d+")
# Structural list markers (a), (b), (1), (2) for normalize-to-spoken rule.
STRUCTURAL_PAREN_LETTER_RE = re.compile(r"\(([a-zA-Z])\)")
STRUCTURAL_PAREN_NUM_RE = re.compile(r"\((\d{1,2})\)")
# Non-speech bracket content: strip list (case-fold match). Edited by Cursor.
_NON_SPEECH_CONTENT_RE = re.compile(
    r"(?i)^(inaudible|voice\s*overlap|laughter|coughing|audio\s*cut|"
    r"recess|dollars|noise|ph|indiscernible|mirth|sneezes|sighs|"
    r"applause|break|luncheon|lunch|interruption|banging|attempt\s*to\s*laughter)"
    r"\.?$"
)
# Max length for bracket content stored in report (avoid huge keys).
_BRACKET_CONTENT_MAX = 80


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
    """Extract artifact candidates from a single turn text.

    Edited by Cursor: Added acronyms, currency, historical_years,
    unspoken_headers, no_dot_context, vote_tally, roman_numerals,
    percentages, decades, ordinals_word, statute_citation, awareness_*,
    awareness_brackets_*, awareness_leading_decimal; leading_decimal,
    non_speech_brackets, editorial_square_bracket, dash_range, ellipsis,
    structural_bracket, numbered_list_marker.
    """
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
    # Acronyms (2-5 ALL-CAPS), skip common 2-letter words
    for m in ACRONYM_RE.finditer(text):
        tok = m.group(1)
        if len(tok) == 2 and tok in ACRONYM_STOPLIST:
            continue
        _add(artifacts["acronyms"], tok)
    # Currency: $N or $N.NN, normalize commas for counting
    for m in CURRENCY_RE.finditer(text):
        _add(artifacts["currency"], _normalize_currency(m.group(0)))
    # Historical years 1000-1899 (separate from 19xx/20xx)
    for m in HISTORICAL_YEAR_RE.finditer(text):
        _add(artifacts["historical_years"], m.group(1))
    # Unspoken header phrases (once per turn per phrase)
    for phrase in UNSPOKEN_HEADER_PHRASES:
        if phrase in text:
            artifacts["unspoken_headers"][phrase] += 1
    # "No." next token (negation vs number)
    for m in NO_DOT_NEXT_RE.finditer(text):
        _add(artifacts["no_dot_context"], m.group(1))
    # "No." as number (citation: No. 96-511)
    for m in NO_DOT_CITATION_RE.finditer(text):
        _add(artifacts["no_dot_citation"], m.group(0))
    # Roman numerals (VII, IV, etc.)
    for m in ROMAN_NUMERAL_RE.finditer(text):
        _add(artifacts["roman_numerals"], m.group(1))
    # Percentages
    for m in PERCENTAGE_RE.finditer(text):
        _add(artifacts["percentages"], _normalize_percentage(m.group(0)))
    # Decades
    for m in DECADE_RE.finditer(text):
        _add(artifacts["decades"], m.group(0))
    # Et al.
    for _m in ET_AL_RE.finditer(text):
        _add(artifacts["abbreviations"], "et al.")
    # Word ordinals (Fifth, Seventh, etc.)
    for m in ORDINAL_WORD_RE.finditer(text):
        _add(artifacts["ordinals_word"], m.group(1))
    # Statute citations
    for m in STATUTE_USC_RE.finditer(text):
        _add(artifacts["statute_citation"], m.group(0).strip())
    for m in TITLE_N_RE.finditer(text):
        _add(artifacts["statute_citation"], m.group(0).strip())
    # Awareness: non-ASCII characters (store as U+XXXX for report)
    for c in text:
        if ord(c) > 127:
            artifacts["awareness_non_ascii"][f"U+{ord(c):04X}"] += 1
    # Awareness: mixed-case words (McCloud, etc.)
    for m in MIXED_CASE_RE.finditer(text):
        _add(artifacts["awareness_mixed_case"], m.group(0), normalize=False)
    # Awareness: long all-caps (6+ letters)
    for m in ALL_CAPS_LONG_RE.finditer(text):
        _add(artifacts["awareness_all_caps_long"], m.group(0), normalize=False)
    # Awareness: typographic/legal symbols (ellipsis, en/em dash, etc.)
    for sym in AWARENESS_SYMBOLS:
        if sym in text:
            artifacts["awareness_symbols"][f"U+{ord(sym):04X}"] += 1
    if "..." in text:
        artifacts["awareness_symbols"]["..."] += 1
    # Awareness: bracket usages (e.g. [cough], (inaudible), 1)).
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
    # Editorial [= X] (replace with normalized X then strip).
    for m in EDITORIAL_SQUARE_RE.finditer(text):
        artifacts["editorial_square_bracket"][m.group(0)] += 1
    # Dash range N-M for "N to M" rule.
    for m in DASH_RANGE_RE.finditer(text):
        artifacts["dash_range"][m.group(0)] += 1
    # Ellipsis: literal "..." and U+2026 (omit or pause for ASR).
    for _ in re.finditer(r"\.\.\.", text):
        artifacts["ellipsis"]["..."] += 1
    if "\u2026" in text:
        artifacts["ellipsis"]["U+2026"] += text.count("\u2026")
    # Structural (a), (b), (1), (2) for normalize-to-spoken rule.
    for m in STRUCTURAL_PAREN_LETTER_RE.finditer(text):
        artifacts["structural_bracket"][m.group(0)] += 1
    for m in STRUCTURAL_PAREN_NUM_RE.finditer(text):
        artifacts["structural_bracket"][m.group(0)] += 1
    # Awareness: leading decimals (.66, .5) — "point six six".
    for m in LEADING_DECIMAL_RE.finditer(text):
        frag = m.group(1)
        artifacts["awareness_leading_decimal"][frag] += 1
        # First-class leading_decimal; skip .YYYY (year false positive).
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


# All category keys so path tracking and report stay consistent.
# Edited by Cursor: add awareness_brackets_*, awareness_leading_decimal.
_CATEGORIES = frozenset(
    {
        "case_ids",
        "years",
        "abbreviations",
        "versus",
        "ordinals",
        "section_refs",
        "dates_month_year",
        "likely_initials",
        "acronyms",
        "currency",
        "historical_years",
        "unspoken_headers",
        "no_dot_context",
        "no_dot_citation",
        "vote_tally",
        "roman_numerals",
        "percentages",
        "decades",
        "ordinals_word",
        "statute_citation",
        "awareness_non_ascii",
        "awareness_mixed_case",
        "awareness_all_caps_long",
        "awareness_symbols",
        "awareness_brackets_parens",
        "awareness_brackets_square",
        "awareness_brackets_curly",
        "awareness_brackets_numbered",
        "awareness_leading_decimal",
        "leading_decimal",
        "non_speech_brackets",
        "editorial_square_bracket",
        "dash_range",
        "ellipsis",
        "structural_bracket",
        "numbered_list_marker",
    }
)

# Map verification rule_id -> (script_category, ...). Used by --need-verification.
# Awareness categories are not listed (report-only).
_RULE_TO_CATEGORIES: dict[str, tuple[str, ...]] = {
    "case_ids": ("case_ids",),
    "versus": ("versus",),
    "title_mr": ("abbreviations",),
    "years": ("years",),
    "historical_years": ("historical_years",),
    "age": (),  # No script category; search transcripts for age-like numbers
    "currency": ("currency",),
    "section_refs": ("section_refs",),
    "acronyms": ("acronyms",),
    "no_negation": ("no_dot_context",),
    "no_number": ("no_dot_citation",),
    "unspoken_headers": ("unspoken_headers",),
    "vote_tally": ("vote_tally",),
    "roman_numerals": ("roman_numerals",),
    "percentages": ("percentages",),
    "decades": ("decades",),
    "ordinals_word": ("ordinals_word",),
    "statute_citation": ("statute_citation",),
}

_RULE_LABELS: dict[str, str] = {
    "no_number": '"No." (number/citation)',
    "no_negation": '"No." (negation)',
    "title_mr": "Title (Mr. / Ms.)",
    "historical_years": "Historical year (1xxx)",
    "age": "Age / small number",
    "section_refs": "Section number (legal)",
    "unspoken_headers": "Unspoken section headers",
    "vote_tally": "Vote tally (9-0, 7-2)",
    "roman_numerals": "Roman numeral (VII, IV)",
    "percentages": "Percentage (50%, 25 percent)",
    "decades": "Decade (1980s, 1930s)",
    "ordinals_word": "Ordinal (word): Fifth, Seventh",
    "statute_citation": "Statute citation (21 U.S.C., Title 18)",
}


def collect_artifacts(
    transcripts_dir: Path,
    *,
    track_paths: bool = False,
) -> dict[str, dict[str, int]] | tuple[dict[str, dict[str, int]], dict[str, set[str]]]:
    """Walk processed transcripts and collect all artifact candidates.

    If track_paths is True, return (report, category_to_paths) so callers can
    list example transcripts per category (e.g. for --need-verification).
    """
    artifacts: dict[str, Counter[str]] = defaultdict(Counter)
    category_to_paths: dict[str, set[str]] = {c: set() for c in _CATEGORIES}
    for path in sorted(transcripts_dir.rglob("*.json")):
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        try:
            rel = path.relative_to(transcripts_dir)
        except ValueError:
            rel = path
        rel_str = str(rel).replace("\\", "/")
        file_artifacts: dict[str, Counter[str]] = defaultdict(Counter)
        for turn in data.get("turns") or []:
            if isinstance(turn, dict):
                collect_from_text(turn.get("text") or "", file_artifacts)
        speakers = (data.get("metadata") or {}).get("speakers") or []
        collect_from_speakers(speakers, file_artifacts)
        for k, c in file_artifacts.items():
            if c:
                artifacts[k].update(c)
                if track_paths and k in category_to_paths:
                    category_to_paths[k].add(rel_str)
    report = {k: dict(v.most_common()) for k, v in sorted(artifacts.items())}
    if track_paths:
        return report, category_to_paths
    return report


def _run_need_verification(
    _transcripts_dir: Path,
    status_path: Path,
    min_instances: int,
    category_to_paths: dict[str, set[str]],
    max_example_paths: int = 15,
) -> None:
    """Print rules with fewer than min_instances verified and example transcripts."""
    try:
        status = json.loads(status_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        status = {}
    need: list[tuple[str, int, set[str]]] = []
    for rule_id, categories in _RULE_TO_CATEGORIES.items():
        current = status.get(rule_id, 0)
        if current >= min_instances:
            continue
        paths: set[str] = set()
        for cat in categories:
            paths |= category_to_paths.get(cat, set())
        label = _RULE_LABELS.get(rule_id, rule_id)
        need.append((label, current, paths))
    if not need:
        print(
            f"All rules have at least {min_instances} verified instances.",
            file=sys.stderr,
        )
        return
    print(
        f"Rules with fewer than {min_instances} verified instances:",
        file=sys.stderr,
    )
    for label, current, paths in sorted(need, key=lambda x: (x[1], x[0])):
        n_more = min_instances - current
        print(f"  {label}: {current} verified (need {n_more} more)", file=sys.stderr)
        sorted_paths = sorted(paths)[:max_example_paths]
        for p in sorted_paths:
            print(f"    {p}", file=sys.stderr)
        if len(paths) > max_example_paths:
            print(f"    ... and {len(paths) - max_example_paths} more", file=sys.stderr)


def main() -> None:
    """Parse args, collect artifacts from transcripts, and print or write report."""
    parser = argparse.ArgumentParser(
        description="Collect potential ASR transcription artifacts from processed transcripts."
    )
    parser.add_argument(
        "transcripts_dir",
        type=Path,
        nargs="?",
        default=Path("data/transcripts"),
        help="Root directory of processed transcript JSON files",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write JSON report here; default is stdout",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a short text summary to stderr",
    )
    parser.add_argument(
        "--need-verification",
        action="store_true",
        help="List rules with fewer than --min-instances verified and example transcripts",
    )
    parser.add_argument(
        "--min-instances",
        type=int,
        default=2,
        metavar="N",
        help="Minimum verified instances per rule (default: 2)",
    )
    parser.add_argument(
        "--status",
        type=Path,
        default=Path("data/asr_verification_status.json"),
        help="Path to JSON with current verified count per rule (default: data/asr_verification_status.json)",
    )
    args = parser.parse_args()
    if not args.transcripts_dir.is_dir():
        raise SystemExit(f"Not a directory: {args.transcripts_dir}")
    track_paths = args.need_verification
    result = collect_artifacts(args.transcripts_dir, track_paths=track_paths)
    if track_paths:
        report, category_to_paths = result
        _run_need_verification(
            args.transcripts_dir,
            args.status,
            args.min_instances,
            category_to_paths,
        )
    else:
        report = result
    out = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(out)
    else:
        print(out)
    if args.summary:
        total = sum(len(v) for v in report.values())
        for cat, counts in report.items():
            n = len(counts)
            top = list(counts.keys())[:5]
            print(f"  {cat}: {n} unique", file=sys.stderr)
            print(f"    sample: {top}", file=sys.stderr)
        print(f"  Total unique artifacts: {total}", file=sys.stderr)


if __name__ == "__main__":
    main()
