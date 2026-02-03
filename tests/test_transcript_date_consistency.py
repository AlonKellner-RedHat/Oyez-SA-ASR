# Edited by Cursor
"""Test that transcript URL date and title date are always consistent."""

import json
from pathlib import Path

import pytest

from oyez_sa_asr.audio_source import (
    extract_transcript_date,
    parse_date_from_title,
)


def _transcripts_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "transcripts"


def _format_date_triple(t: tuple[int, int, int]) -> str:
    return f"{t[0]}-{t[1]:02d}-{t[2]:02d}"


def _collect_inconsistencies(transcripts_dir: Path) -> list[dict]:
    """Load all transcript JSONs and collect URL vs title date inconsistencies."""
    inconsistencies: list[dict] = []
    for path in sorted(transcripts_dir.rglob("*.json")):
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            inconsistencies.append(
                {
                    "path": str(path),
                    "error": "failed to load JSON",
                    "url_date": None,
                    "title_date": None,
                    "title": None,
                }
            )
            continue
        title = data.get("title")
        url_date = extract_transcript_date(data)
        title_date = parse_date_from_title(title) if title else None
        # Skip if no URL date (no audio_urls) - nothing to compare
        if url_date is None:
            continue
        if title_date is None:
            inconsistencies.append(
                {
                    "path": str(path),
                    "error": "title date unparseable",
                    "url_date": url_date,
                    "title_date": None,
                    "title": title,
                }
            )
            continue
        if url_date != title_date:
            inconsistencies.append(
                {
                    "path": str(path),
                    "error": "url date != title date",
                    "url_date": url_date,
                    "title_date": title_date,
                    "title": title,
                }
            )
    return inconsistencies


def _format_inconsistencies_report(items: list[dict]) -> str:
    lines = [
        "",
        "URL date vs title date inconsistencies:",
        "----------------------------------------",
    ]
    for item in items:
        lines.append(f"  path: {item['path']}")
        lines.append(f"  error: {item['error']}")
        if item.get("url_date"):
            lines.append(f"  url_date:   {_format_date_triple(item['url_date'])}")
        if item.get("title_date"):
            lines.append(f"  title_date: {_format_date_triple(item['title_date'])}")
        if item.get("title") is not None:
            lines.append(f"  title: {item['title']!r}")
        lines.append("")
    return "\n".join(lines)


@pytest.mark.slow
@pytest.mark.skipif(
    not _transcripts_dir().is_dir(),
    reason="data/transcripts not present",
)
def test_url_date_consistent_with_title() -> None:
    """URL-derived date must match date parsed from title; report inconsistencies."""
    transcripts_dir = _transcripts_dir()
    inconsistencies = _collect_inconsistencies(transcripts_dir)
    assert not inconsistencies, (
        f"Found {len(inconsistencies)} transcript(s) where URL date and title date "
        "differ or title is unparseable."
        + _format_inconsistencies_report(inconsistencies)
    )
