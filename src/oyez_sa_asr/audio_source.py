# Edited by Claude
"""Audio source discovery and era-aware format selection."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_DIGITAL_ERA_START = 2006  # First term recorded directly to MP3

# Modern format patterns (post-2005): {docket}_{date}-{type}
_MODERN_TYPE_PATTERNS = {
    "-opinion-dissent": "dissent",
    "-opinion-concurrence": "concurrence",
    "-opinion-concur": "concurrence",
    "-opinion": "opinion",
    "-argument": "oral_argument",
}

# Legacy format pattern: {date}{suffix}_{docket}
_LEGACY_SUFFIX_MAP = {
    "a": "oral_argument",  # argument
    "o": "opinion",  # opinion
    "r": "oral_argument",  # reargument (treat as oral argument)
}


def parse_transcript_type_from_recording_id(recording_id: str) -> str:
    """Parse transcript_type from recording_id.

    Edited by Claude.

    Handles two formats:
    - Modern: {docket}_{date}-{type} e.g., 21-86_20221107-argument
    - Legacy: {date}{suffix}_{docket} e.g., 20000418a_99-224

    Returns
    -------
        One of: oral_argument, opinion, dissent, concurrence, unknown
    """
    # Try modern format first (check longest patterns first)
    for pattern, transcript_type in _MODERN_TYPE_PATTERNS.items():
        if pattern in recording_id:
            return transcript_type

    # Try legacy format: {date}{suffix}_{docket}
    match = re.match(r"^\d{8}([a-z])_", recording_id)
    if match:
        suffix = match.group(1)
        return _LEGACY_SUFFIX_MAP.get(suffix, "unknown")

    return "unknown"


def get_recording_id(path: Path) -> str:
    """Extract common recording ID, stripping .delivery suffix from MP3."""
    stem = path.stem
    return stem[:-9] if stem.endswith(".delivery") else stem


# Regexes for deterministic date extraction from recording_id (see module doc below).
_LEGACY_DATE_RE = re.compile(r"^(\d{8})[a-z]_")
_MODERN_DATE_RE = re.compile(r"_(\d{8})-")


def parse_date_from_recording_id(recording_id: str) -> tuple[int, int, int] | None:
    """Parse (year, month, day) from recording_id.

    Date is encoded in every transcript's audio URL (metadata.audio_urls.mp3)
    in a deterministic way:

    - Legacy: {YYYYMMDD}{suffix}_{docket} e.g. 19951010a_94-1039 → 1995-10-10
    - Modern: {docket}_{YYYYMMDD}-{type} e.g. 19-1392_20211201-argument → 2021-12-01

    Returns (year, month, day) or None if not parseable. Month/day are validated
    (1-12, 1-31).
    """
    # Legacy: 8 digits at start, then single letter and underscore
    match = _LEGACY_DATE_RE.match(recording_id)
    if match:
        yyyymmdd = match.group(1)
    else:
        # Modern: 8 digits after underscore and before hyphen
        match = _MODERN_DATE_RE.search(recording_id)
        if not match:
            return None
        yyyymmdd = match.group(1)
    try:
        y, m, d = int(yyyymmdd[:4]), int(yyyymmdd[4:6]), int(yyyymmdd[6:8])
        if 1 <= m <= 12 and 1 <= d <= 31:
            return (y, m, d)
    except (ValueError, IndexError):
        pass
    return None


def get_recording_id_from_transcript(transcript: dict[str, Any]) -> str | None:
    """Get recording_id from transcript metadata (mp3 URL basename)."""
    urls = transcript.get("metadata", {}).get("audio_urls") or {}
    mp3 = urls.get("mp3")
    if not mp3 or not isinstance(mp3, str):
        return None
    name = mp3.rsplit("/", 1)[-1].strip()
    if not name:
        return None
    # recording_id is the basename before first dot (e.g. .../X.delivery.mp3 -> X)
    base = name.split(".")[0]
    return base if base else None


def extract_transcript_date(transcript: dict[str, Any]) -> tuple[int, int, int] | None:
    """Extract (year, month, day) from a transcript dict.

    Uses metadata.audio_urls.mp3 to get recording_id, then parses the
    deterministically encoded date (see parse_date_from_recording_id).
    """
    rec_id = get_recording_id_from_transcript(transcript)
    return parse_date_from_recording_id(rec_id) if rec_id else None


_MONTH_NAMES = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}
# Match " - Month DD, YYYY" or ", Month DD, YYYY" (e.g. "Oral Argument - December 01, 2021" or "Oral Argument, March 23, 2015")
_TITLE_DATE_RE = re.compile(
    r"[-,] ([A-Za-z]+) (\d{1,2}), (\d{4})(?:\s|$|[(\s])",
)


def parse_date_from_title(title: str) -> tuple[int, int, int] | None:
    """Parse (year, month, day) from transcript title.

    Expects format like "Oral Argument - December 01, 2021" or
    "Opinion Announcement - May 20, 1996". Returns None if unparseable.
    """
    if not title or not isinstance(title, str):
        return None
    match = _TITLE_DATE_RE.search(title)
    if not match:
        return None
    month_name, day_str, year_str = match.group(1), match.group(2), match.group(3)
    month = _MONTH_NAMES.get(month_name.lower())
    if month is None:
        return None
    try:
        day = int(day_str)
        year = int(year_str)
        if 1 <= day <= 31 and year >= 1900:
            return (year, month, day)
    except ValueError:
        pass
    return None


def get_preferred_format(term: str) -> tuple[str, str]:
    """Return (preferred, fallback) format based on term year.

    Pre-2006: OGG preserves more of the 96k/24bit WAV source.
    Post-2005: MP3 is the original recording format.
    """
    try:
        year = int(term)
        if year >= _DIGITAL_ERA_START:
            return ("mp3", "ogg")
        return ("ogg", "mp3")
    except ValueError:
        return ("mp3", "ogg")


def get_source_era(term: str) -> str:
    """Return source era label based on term year."""
    try:
        return "digital" if int(term) >= _DIGITAL_ERA_START else "analog"
    except ValueError:
        return "unknown"


def extract_term_docket(path: Path) -> tuple[str, str] | None:
    """Extract term and docket from audio path."""
    parts = path.parts
    try:
        idx = parts.index("case_data")
        return parts[idx + 1], parts[idx + 2]
    except (ValueError, IndexError):
        return None


@dataclass
class AudioSource:
    """Audio source with paths for each format."""

    recording_id: str
    term: str
    docket: str
    mp3_path: Path | None = None
    ogg_path: Path | None = None


def find_audio_sources(
    cache_dir: Path, terms: list[str] | None = None
) -> dict[tuple[str, str, str], AudioSource]:
    """Find and group audio files by (term, docket, recording_id).

    Args:
        cache_dir: Directory containing cached audio files.
        terms: Optional list of terms to filter by.
    """
    sources: dict[tuple[str, str, str], AudioSource] = {}
    term_set = set(terms) if terms else None

    for fmt in ("mp3", "ogg"):
        pattern = f"oyez.case-media.{fmt}/case_data/**/*.{fmt}"
        for path in cache_dir.glob(pattern):
            info = extract_term_docket(path)
            if info is None:
                continue
            term, docket = info

            # Apply term filter
            if term_set and term not in term_set:
                continue

            rec_id = get_recording_id(path)
            key = (term, docket, rec_id)

            if key not in sources:
                sources[key] = AudioSource(rec_id, term, docket)

            if fmt == "mp3":
                sources[key].mp3_path = path
            else:
                sources[key].ogg_path = path

    return sources
