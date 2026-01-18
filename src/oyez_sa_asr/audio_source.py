# Edited by Claude
"""Audio source discovery and era-aware format selection."""

from dataclasses import dataclass
from pathlib import Path

_DIGITAL_ERA_START = 2006  # First term recorded directly to MP3


def get_recording_id(path: Path) -> str:
    """Extract common recording ID, stripping .delivery suffix from MP3."""
    stem = path.stem
    return stem[:-9] if stem.endswith(".delivery") else stem


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
