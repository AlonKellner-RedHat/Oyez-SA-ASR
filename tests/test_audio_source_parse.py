# Edited by Cursor: split from test_audio_source (lintok; plan).
"""Tests for parse_* (audio_source)."""

from oyez_sa_asr.audio_source import (
    parse_date_from_recording_id,
    parse_date_from_title,
    parse_transcript_type_from_recording_id,
)


class TestParseTranscriptTypeFromRecordingId:
    """Tests for parse_transcript_type_from_recording_id function."""

    def test_modern_argument(self) -> None:
        assert (
            parse_transcript_type_from_recording_id("21-86_20221107-argument")
            == "oral_argument"
        )

    def test_modern_opinion(self) -> None:
        assert (
            parse_transcript_type_from_recording_id("22-166_20230525-opinion")
            == "opinion"
        )

    def test_modern_opinion_dissent(self) -> None:
        assert (
            parse_transcript_type_from_recording_id("21-476_20230630-opinion-dissent")
            == "dissent"
        )

    def test_modern_opinion_concurrence(self) -> None:
        assert (
            parse_transcript_type_from_recording_id(
                "20-1199_20230629-opinion-concurrence"
            )
            == "concurrence"
        )

    def test_modern_opinion_concur(self) -> None:
        assert (
            parse_transcript_type_from_recording_id("23-726_20240627-opinion-concur")
            == "concurrence"
        )

    def test_legacy_argument(self) -> None:
        assert (
            parse_transcript_type_from_recording_id("20000418a_99-224")
            == "oral_argument"
        )

    def test_legacy_opinion(self) -> None:
        assert parse_transcript_type_from_recording_id("20000619o_99-224") == "opinion"

    def test_legacy_reargument(self) -> None:
        assert (
            parse_transcript_type_from_recording_id("20000329r_98-6322")
            == "oral_argument"
        )

    def test_unknown_format(self) -> None:
        assert parse_transcript_type_from_recording_id("random-id") == "unknown"

    def test_empty_string(self) -> None:
        assert parse_transcript_type_from_recording_id("") == "unknown"


class TestParseDateFromRecordingId:
    """Tests for parse_date_from_recording_id."""

    def test_modern_argument(self) -> None:
        assert parse_date_from_recording_id("19-1392_20211201-argument") == (
            2021,
            12,
            1,
        )

    def test_modern_opinion(self) -> None:
        assert parse_date_from_recording_id("22-166_20230525-opinion") == (
            2023,
            5,
            25,
        )

    def test_legacy_argument(self) -> None:
        assert parse_date_from_recording_id("19951010a_94-1039") == (1995, 10, 10)

    def test_legacy_reargument(self) -> None:
        assert parse_date_from_recording_id("19551013r_3") == (1955, 10, 13)

    def test_unknown_format_returns_none(self) -> None:
        assert parse_date_from_recording_id("random-id") is None

    def test_empty_returns_none(self) -> None:
        assert parse_date_from_recording_id("") is None


class TestParseDateFromTitle:
    """Tests for parse_date_from_title."""

    def test_dash_format(self) -> None:
        assert parse_date_from_title("Oral Argument - December 01, 2021") == (
            2021,
            12,
            1,
        )

    def test_comma_format(self) -> None:
        assert parse_date_from_title("Oral Argument, March 23, 2015") == (
            2015,
            3,
            23,
        )

    def test_opinion_announcement(self) -> None:
        assert parse_date_from_title("Opinion Announcement - May 20, 1996") == (
            1996,
            5,
            20,
        )

    def test_no_date_returns_none(self) -> None:
        assert parse_date_from_title("Wisconsin v. Yoder - Life of the Law") is None

    def test_empty_returns_none(self) -> None:
        assert parse_date_from_title("") is None
        assert parse_date_from_title(None) is None  # type: ignore[arg-type]
