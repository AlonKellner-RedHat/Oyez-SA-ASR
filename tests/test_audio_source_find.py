# Edited by Cursor: split from test_audio_source (lintok; plan).
"""Tests for get_source_era, extract_term_docket, find_audio_sources."""

from pathlib import Path

from oyez_sa_asr.audio_source import (
    extract_term_docket,
    find_audio_sources,
    get_source_era,
)


class TestGetSourceEra:
    """Tests for get_source_era function."""

    def test_digital_era(self) -> None:
        """Post-2005 terms are digital."""
        assert get_source_era("2010") == "digital"

    def test_analog_era(self) -> None:
        """Pre-2006 terms are analog."""
        assert get_source_era("2000") == "analog"

    def test_invalid_term_returns_unknown(self) -> None:
        """Invalid term returns unknown."""
        assert get_source_era("invalid") == "unknown"


class TestExtractTermDocket:
    """Tests for extract_term_docket function."""

    def test_extracts_from_valid_path(self) -> None:
        """Extracts term and docket from valid path."""
        path = Path("/cache/oyez.case-media.mp3/case_data/2024/22-123/audio.mp3")
        assert extract_term_docket(path) == ("2024", "22-123")

    def test_returns_none_for_invalid_path(self) -> None:
        """Returns None for paths without case_data."""
        path = Path("/cache/audio/2024/22-123/audio.mp3")
        assert extract_term_docket(path) is None

    def test_returns_none_for_short_path(self) -> None:
        """Returns None for paths too short after case_data."""
        path = Path("/cache/case_data/2024")
        assert extract_term_docket(path) is None


class TestFindAudioSources:
    """Tests for find_audio_sources function."""

    def test_finds_mp3_files(self, tmp_path: Path) -> None:
        """Finds MP3 files in cache."""
        mp3_dir = tmp_path / "oyez.case-media.mp3" / "case_data" / "2024" / "22-123"
        mp3_dir.mkdir(parents=True)
        (mp3_dir / "audio.delivery.mp3").write_bytes(b"mp3")

        sources = find_audio_sources(tmp_path)
        assert len(sources) == 1
        assert ("2024", "22-123", "audio") in sources

    def test_filters_by_term(self, tmp_path: Path) -> None:
        """Filters sources by term."""
        for term in ["2023", "2024"]:
            mp3_dir = tmp_path / "oyez.case-media.mp3" / "case_data" / term / "docket"
            mp3_dir.mkdir(parents=True)
            (mp3_dir / "audio.mp3").write_bytes(b"mp3")

        sources = find_audio_sources(tmp_path, ["2024"])
        assert len(sources) == 1
        assert ("2024", "docket", "audio") in sources

    def test_combines_mp3_and_ogg(self, tmp_path: Path) -> None:
        """Combines MP3 and OGG for same recording."""
        for fmt in ["mp3", "ogg"]:
            fmt_dir = (
                tmp_path / f"oyez.case-media.{fmt}" / "case_data" / "2024" / "22-123"
            )
            fmt_dir.mkdir(parents=True)
            if fmt == "mp3":
                (fmt_dir / "audio.delivery.mp3").write_bytes(b"mp3")
            else:
                (fmt_dir / "audio.ogg").write_bytes(b"ogg")

        sources = find_audio_sources(tmp_path)
        assert len(sources) == 1
        source = sources[("2024", "22-123", "audio")]
        assert source.mp3_path is not None
        assert source.ogg_path is not None
