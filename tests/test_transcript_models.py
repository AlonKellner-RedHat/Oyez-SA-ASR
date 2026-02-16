# Edited by Claude
"""Tests for ProcessedTranscript and case mapping."""

import json
import tempfile
from pathlib import Path
from typing import Any, cast

from oyez_sa_asr.scraper import transcript_models
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

    def test_build_transcript_to_case_map_filters_by_terms(self) -> None:
        """Only scan term dirs in terms list (parser_transcripts line 203)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cases_dir = Path(tmpdir)
            for term in ("2023", "2024"):
                term_dir = cases_dir / term
                term_dir.mkdir()
                case_data = {
                    "term": term,
                    "docket_number": "22-123",
                    "oral_arguments": [
                        {"id": 1000 + int(term), "href": f"https://example.com/{term}"}
                    ],
                    "opinion_announcements": [],
                }
                (term_dir / "22-123.json").write_text(json.dumps(case_data))

            case_map = build_transcript_to_case_map(cases_dir, terms=["2024"])
            # Map key is transcript ID (oral_arguments[].id), not term
            assert 3024 in case_map
            assert case_map[3024] == ("2024", "22-123")
            assert 3023 not in case_map


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

    def test_extract_audio_urls_skips_falsy_media_file_entries(self) -> None:
        """Falsy media_file entries are skipped (transcript_models line 32)."""
        # Intentionally pass list with falsy elements to hit the "if not mf" branch
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
        # Use class from transcript_models so get_filename (line 178) is covered
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

    def test_to_dict_includes_title_date_url_date_date_mismatch(self) -> None:
        """to_dict includes title_date, url_date, date_mismatch from process transcripts."""
        raw = {
            "id": 25123,
            "title": "Oral Argument - December 05, 2022",
            "media_file": [
                {
                    "mime": "audio/mpeg",
                    "href": "https://s3.../21-476_20221205-argument.delivery.mp3",
                },
            ],
            "transcript": {"duration": 0.0, "sections": [{"turns": []}]},
        }
        t = ProcessedTranscript.from_raw(raw, "2022", "21-476")
        data = t.to_dict()
        assert data["title_date"] == "2022-12-05"
        assert data["url_date"] == "2022-12-05"
        assert data["date_mismatch"] is False

    def test_to_dict_date_mismatch_true_when_differ(self) -> None:
        """date_mismatch is True when url_date and title_date differ."""
        raw = {
            "id": 1,
            "title": "Oral Argument - April 26, 1978",
            "media_file": [
                {
                    "mime": "audio/mpeg",
                    "href": "https://s3.../77-529_19780425-argument.delivery.mp3",
                },
            ],
            "transcript": {"duration": 0.0, "sections": [{"turns": []}]},
        }
        t = ProcessedTranscript.from_raw(raw, "1977", "77-529")
        data = t.to_dict()
        assert data["title_date"] == "1978-04-26"
        assert data["url_date"] == "1978-04-25"
        assert data["date_mismatch"] is True

    def test_to_dict_date_fields_none_when_unparseable(self) -> None:
        """title_date and url_date are null when unparseable; date_mismatch False."""
        raw = _raw([])
        raw["id"] = 1
        raw["title"] = "Wisconsin v. Yoder - Life of the Law"
        raw["media_file"] = [
            {"mime": "audio/mpeg", "href": "https://s3.../19711208a_70-110.ogg"},
        ]
        t = ProcessedTranscript.from_raw(raw, "1971", "70-110")
        data = t.to_dict()
        assert data["url_date"] == "1971-12-08"
        assert data["title_date"] is None
        assert data["date_mismatch"] is False
