# Edited by Claude
"""Parser for cached Oyez case detail responses."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .case_models import (
    AudioReference,
    Decision,
    TimelineEvent,
    parse_opinion_title,
)

# Re-export for backwards compatibility
__all__ = [
    "AudioReference",
    "Decision",
    "ProcessedCase",
    "TimelineEvent",
    "extract_media_urls",
    "parse_opinion_title",
]


def extract_media_urls(cases_dir: Path) -> list[str]:
    """Extract all case_media hrefs from processed case files."""
    urls: set[str] = set()

    if not cases_dir.exists():
        return []

    for term_dir in cases_dir.iterdir():
        if not term_dir.is_dir():
            continue

        for case_file in term_dir.glob("*.json"):
            try:
                with case_file.open() as f:
                    case_data = json.load(f)

                for audio in case_data.get("oral_arguments", []) or []:
                    if audio.get("href") and not audio.get("unavailable"):
                        urls.add(audio["href"])

                for audio in case_data.get("opinion_announcements", []) or []:
                    if audio.get("href") and not audio.get("unavailable"):
                        urls.add(audio["href"])

            except (json.JSONDecodeError, KeyError, TypeError):
                continue

    return list(urls)


@dataclass
class ProcessedCase:
    """Processed case data ready for audio/transcript scraping."""

    id: int
    name: str
    docket_number: str
    term: str
    href: str
    timeline: list[TimelineEvent] = field(default_factory=list)
    decision: Decision | None = None
    oral_arguments: list[AudioReference] = field(default_factory=list)
    opinion_announcements: list[AudioReference] = field(default_factory=list)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "ProcessedCase":
        """Parse from raw API case detail response."""
        timeline_raw = raw.get("timeline", []) or []
        timeline = [TimelineEvent.from_raw(t) for t in timeline_raw if t is not None]

        decisions_raw = raw.get("decisions", []) or []
        decision = Decision.from_raw(decisions_raw[0]) if decisions_raw else None

        oral_raw = raw.get("oral_argument_audio", []) or []
        oral_arguments = [AudioReference.from_oral_argument(a) for a in oral_raw]

        opinion_raw = raw.get("opinion_announcement", []) or []
        opinion_announcements = [
            AudioReference.from_opinion_announcement(a) for a in opinion_raw
        ]

        return cls(
            id=raw.get("ID", 0),
            name=raw.get("name", ""),
            docket_number=raw.get("docket_number", ""),
            term=raw.get("term", ""),
            href=raw.get("href", ""),
            timeline=timeline,
            decision=decision,
            oral_arguments=oral_arguments,
            opinion_announcements=opinion_announcements,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "docket_number": self.docket_number,
            "term": self.term,
            "href": self.href,
            "timeline": [t.to_dict() for t in self.timeline],
            "decision": self.decision.to_dict() if self.decision else None,
            "oral_arguments": [a.to_dict() for a in self.oral_arguments],
            "opinion_announcements": [a.to_dict() for a in self.opinion_announcements],
        }

    def save(self, output_dir: Path, source_path: Path | None = None) -> Path:
        """Save case to JSON file with optional provenance."""
        case_dir = output_dir / self.term
        case_dir.mkdir(parents=True, exist_ok=True)
        file_path = case_dir / f"{self.docket_number}.json"
        data = self.to_dict()
        if source_path:
            data["_meta"] = {"source_path": str(source_path)}
        with file_path.open("w") as f:
            json.dump(data, f, indent=2)
        return file_path
