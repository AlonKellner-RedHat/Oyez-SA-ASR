# Edited by Cursor: split from test_audio_source (lintok; plan).
"""Tests for get_* and extract_transcript_date (audio_source)."""

from pathlib import Path

from oyez_sa_asr.audio_source import (
    extract_transcript_date,
    get_preferred_format,
    get_recording_id,
    get_recording_id_from_transcript,
)


class TestGetRecordingIdFromTranscript:
    """Tests for get_recording_id_from_transcript."""

    def test_modern_mp3_url(self) -> None:
        t = {
            "metadata": {
                "audio_urls": {
                    "mp3": "https://s3.../19-1392_20211201-argument.delivery.mp3",
                },
            },
        }
        assert get_recording_id_from_transcript(t) == "19-1392_20211201-argument"

    def test_legacy_mp3_url(self) -> None:
        t = {
            "metadata": {
                "audio_urls": {
                    "mp3": "https://s3.../19951010a_94-1039.delivery.mp3",
                },
            },
        }
        assert get_recording_id_from_transcript(t) == "19951010a_94-1039"

    def test_missing_audio_urls_returns_none(self) -> None:
        assert get_recording_id_from_transcript({"metadata": {}}) is None

    def test_missing_mp3_returns_none(self) -> None:
        t = {"metadata": {"audio_urls": {"ogg": "https://..."}}}
        assert get_recording_id_from_transcript(t) is None


class TestExtractTranscriptDate:
    """Tests for extract_transcript_date."""

    def test_modern_transcript(self) -> None:
        t = {
            "metadata": {
                "audio_urls": {
                    "mp3": "https://s3.../19-1392_20211201-argument.delivery.mp3",
                },
            },
        }
        assert extract_transcript_date(t) == (2021, 12, 1)

    def test_legacy_transcript(self) -> None:
        t = {
            "metadata": {
                "audio_urls": {
                    "mp3": "https://s3.../19951010a_94-1039.delivery.mp3",
                },
            },
        }
        assert extract_transcript_date(t) == (1995, 10, 10)

    def test_no_audio_urls_returns_none(self) -> None:
        assert extract_transcript_date({"metadata": {}}) is None


class TestGetRecordingId:
    """Tests for get_recording_id function."""

    def test_strips_delivery_suffix(self) -> None:
        path = Path("audio.delivery.mp3")
        assert get_recording_id(path) == "audio"

    def test_keeps_normal_stem(self) -> None:
        path = Path("20240101a_22-123.ogg")
        assert get_recording_id(path) == "20240101a_22-123"


class TestGetPreferredFormat:
    """Tests for get_preferred_format function."""

    def test_digital_era_prefers_mp3(self) -> None:
        assert get_preferred_format("2010") == ("mp3", "ogg")

    def test_analog_era_prefers_ogg(self) -> None:
        assert get_preferred_format("2000") == ("ogg", "mp3")

    def test_invalid_term_defaults_to_mp3(self) -> None:
        assert get_preferred_format("invalid") == ("mp3", "ogg")
