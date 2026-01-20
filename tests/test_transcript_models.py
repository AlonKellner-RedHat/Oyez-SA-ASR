# Edited by Claude
"""Tests for ProcessedTranscript and case mapping."""

import json
import tempfile
from pathlib import Path
from typing import Any

from oyez_sa_asr.scraper.parser_transcripts import (
    ProcessedTranscript,
    build_transcript_to_case_map,
)


def _turn(
    start: float, stop: float, text: str = "x", name: str = "A"
) -> dict[str, Any]:
    """Create a turn dict with minimal fields."""
    return {
        "start": start,
        "stop": stop,
        "speaker": {"ID": 1, "name": name},
        "text_blocks": [{"text": text}],
    }


def _raw(turns: list[dict[str, Any]], dur: float = 30.0) -> dict[str, Any]:
    """Create a raw transcript dict with minimal fields."""
    return {
        "id": 1,
        "title": "Oral Argument - Test",
        "media_file": [],
        "transcript": {"duration": dur, "sections": [{"turns": turns}]},
    }


class TestBuildCaseMap:
    """Tests for build_transcript_to_case_map function."""

    def test_builds_map_from_cases(self) -> None:
        """Map transcript IDs to case info."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cases_dir = Path(tmpdir)
            term_dir = cases_dir / "2022"
            term_dir.mkdir()

            case_data = {
                "docket_number": "21-476",
                "term": "2022",
                "oral_arguments": [
                    {"id": 25123, "href": "https://example.com/oral/25123"}
                ],
                "opinion_announcements": [
                    {"id": 25574, "href": "https://example.com/opinion/25574"}
                ],
            }
            (term_dir / "21-476.json").write_text(json.dumps(case_data))

            case_map = build_transcript_to_case_map(cases_dir)

            assert 25123 in case_map
            assert case_map[25123] == ("2022", "21-476")
            assert 25574 in case_map
            assert case_map[25574] == ("2022", "21-476")

    def test_empty_cases_dir(self) -> None:
        """Empty directory returns empty map."""
        with tempfile.TemporaryDirectory() as tmpdir:
            case_map = build_transcript_to_case_map(Path(tmpdir))
            assert case_map == {}


class TestProcessedTranscript:
    """Tests for ProcessedTranscript dataclass."""

    def test_from_raw(self) -> None:
        """Parse full transcript from raw API response."""
        raw = {
            "id": 25123,
            "title": "Oral Argument - December 05, 2022",
            "media_file": [
                {"mime": "audio/mpeg", "href": "https://example.com/audio.mp3"},
                {"mime": "audio/ogg", "href": "https://example.com/audio.ogg"},
            ],
            "transcript": {
                "duration": 100.0,
                "sections": [
                    {
                        "turns": [
                            {
                                "start": 0.0,
                                "stop": 10.0,
                                "speaker": {"ID": 1, "name": "Speaker A"},
                                "text_blocks": [{"text": "Hello world"}],
                            },
                            {
                                "start": 10.0,
                                "stop": 20.0,
                                "speaker": {"ID": 2, "name": "Speaker B"},
                                "text_blocks": [{"text": "Good morning"}],
                            },
                        ]
                    }
                ],
            },
        }
        transcript = ProcessedTranscript.from_raw(raw, "2022", "21-476")

        assert transcript.id == 25123
        assert transcript.case_docket == "21-476"
        assert transcript.term == "2022"
        assert transcript.type == "oral_argument"
        assert transcript.title == "Oral Argument - December 05, 2022"
        assert len(transcript.turns) == 2
        assert transcript.metadata["duration_seconds"] == 100.0
        assert transcript.metadata["turn_count"] == 2

    def test_overlap_detection(self) -> None:
        """Overlapping turns are flagged."""
        turns = [_turn(0.0, 15.0), _turn(10.0, 20.0)]  # 5s overlap
        transcript = ProcessedTranscript.from_raw(_raw(turns), "2022", "test")

        assert transcript.turns[0].is_overlapping is False
        assert transcript.turns[1].is_overlapping is True
        assert transcript.metadata["overlap_count"] == 1

    def test_speaker_stats(self) -> None:
        """Speaker turn counts are computed."""
        turns = [
            {
                "start": 0.0,
                "stop": 10.0,
                "speaker": {"ID": 1, "name": "A"},
                "text_blocks": [{"text": "x"}],
            },
            {
                "start": 10.0,
                "stop": 20.0,
                "speaker": {"ID": 1, "name": "A"},
                "text_blocks": [{"text": "y"}],
            },
            {
                "start": 20.0,
                "stop": 30.0,
                "speaker": {"ID": 2, "name": "B"},
                "text_blocks": [{"text": "z"}],
            },
        ]
        transcript = ProcessedTranscript.from_raw(_raw(turns), "2022", "test")

        speakers = transcript.metadata["speakers"]
        assert len(speakers) == 2
        speaker_a = next(s for s in speakers if s["id"] == 1)
        assert speaker_a["turn_count"] == 2

    def test_audio_urls_extracted(self) -> None:
        """Audio URLs are extracted by format."""
        raw = _raw([])
        raw["media_file"] = [
            {"mime": "audio/mpeg", "href": "https://example.com/a.mp3"},
            {"mime": "audio/ogg", "href": "https://example.com/a.ogg"},
            {"mime": "application/x-mpegURL", "href": "https://example.com/a.m3u8"},
        ]
        t = ProcessedTranscript.from_raw(raw, "2022", "test")

        assert t.metadata["audio_urls"]["mp3"] == "https://example.com/a.mp3"
        assert t.metadata["audio_urls"]["ogg"] == "https://example.com/a.ogg"
        assert t.metadata["audio_urls"]["hls"] == "https://example.com/a.m3u8"

    def test_save_creates_file(self) -> None:
        """Save creates JSON file in correct location."""
        raw = _raw([])
        raw["id"] = 25123
        t = ProcessedTranscript.from_raw(raw, "2022", "21-476")
        with tempfile.TemporaryDirectory() as d:
            t.save(Path(d))
            out = Path(d) / "2022" / "21-476" / "oral_argument.json"
            assert out.exists()
            assert json.loads(out.read_text())["id"] == 25123

    def test_null_transcript(self) -> None:
        """Handle missing transcript data."""
        raw = {
            "id": 1,
            "title": "Oral Argument - Test",
            "media_file": [],
            "transcript": None,
        }
        t = ProcessedTranscript.from_raw(raw, "2022", "test")
        assert len(t.turns) == 0
        assert t.metadata["duration_seconds"] == 0.0

    def test_save_with_source_path(self) -> None:
        """Save includes _meta.source_path when provided."""
        t = ProcessedTranscript.from_raw(_raw([]), "2023", "22-789")
        with tempfile.TemporaryDirectory() as d:
            src = Path("/cache/raw/xyz789.json")
            t.save(Path(d), source_path=src)
            out = Path(d) / "2023" / "22-789" / "oral_argument.json"
            data = json.loads(out.read_text())
            assert data["_meta"]["source_path"] == str(src)

    def test_too_long_ratio_marks_invalid(self) -> None:
        """Turns >50% of recording duration are marked invalid."""
        # 70 words/60s=70wpm (passes wpm check), 30 words/20s=90wpm
        turns = [
            _turn(0.0, 60.0, " ".join(["w"] * 70)),
            _turn(60.0, 80.0, " ".join(["w"] * 30)),
        ]
        t = ProcessedTranscript.from_raw(_raw(turns, dur=80.0), "2023", "test")

        assert t.turns[0].is_valid is False  # 60/80=75%
        assert (
            t.turns[0].invalid_reason and "too_long_ratio" in t.turns[0].invalid_reason
        )
        assert t.turns[1].is_valid is True  # 20/80=25%
        assert t.metadata["invalid_turn_count"] == 1
