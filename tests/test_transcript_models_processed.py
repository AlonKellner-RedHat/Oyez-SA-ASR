# Edited by Cursor: split from test_transcript_models (lintok; plan).
"""Tests for ProcessedTranscript dataclass."""

import json
import tempfile
from pathlib import Path
from typing import Any, cast

from oyez_sa_asr.scraper import transcript_models
from oyez_sa_asr.scraper.parser_transcripts import ProcessedTranscript


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
        turns = [_turn(0.0, 15.0), _turn(10.0, 20.0)]
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

    def test_extract_audio_urls_skips_falsy_media_file_entries(self) -> None:
        """Falsy media_file entries are skipped (transcript_models line 32)."""
        raw_list: list[dict[str, Any] | None] = [
            {"mime": "audio/mpeg", "href": "https://example.com/audio.mp3"},
            None,
            {},
        ]
        result = transcript_models._extract_audio_urls(
            cast("list[dict[str, Any]] | None", raw_list)
        )
        assert result["mp3"] == "https://example.com/audio.mp3"

    def test_get_filename_without_speaker(self) -> None:
        """get_filename returns type-only name when speaker is None (line 178)."""
        t = transcript_models.ProcessedTranscript(
            id=1,
            case_docket="21-476",
            term="2022",
            type="oral_argument",
            speaker=None,
            title="Oral Argument",
            metadata={},
            turns=[],
        )
        assert t.get_filename() == "oral_argument.json"

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
