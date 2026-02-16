# Edited by Cursor: split from test_transcript_models (lintok; plan).
"""ProcessedTranscript tests: save_with_source_path, too_long_ratio, to_dict date fields."""

import json
import tempfile
from pathlib import Path
from typing import Any

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


class TestProcessedTranscriptSaveAndToDict:
    """ProcessedTranscript: save_with_source_path, too_long_ratio, to_dict dates."""

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
        turns = [
            _turn(0.0, 60.0, " ".join(["w"] * 70)),
            _turn(60.0, 80.0, " ".join(["w"] * 30)),
        ]
        t = ProcessedTranscript.from_raw(_raw(turns, dur=80.0), "2023", "test")

        assert t.turns[0].is_valid is False
        assert (
            t.turns[0].invalid_reason and "too_long_ratio" in t.turns[0].invalid_reason
        )
        assert t.turns[1].is_valid is True
        assert t.metadata["invalid_turn_count"] == 1

    def test_to_dict_includes_title_date_url_date_date_mismatch(self) -> None:
        """to_dict includes title_date, url_date, date_mismatch."""
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
