# Edited by Cursor: split from test_scrape_audio (lintok; plan).
"""Tests for extract_audio_urls (TestExtractAudioUrls)."""

import json
import tempfile
from pathlib import Path

from oyez_sa_asr.scraper.parser_transcripts import extract_audio_urls


class TestExtractAudioUrls:
    """Tests for extract_audio_urls function."""

    def test_extracts_all_formats(self) -> None:
        """Extract mp3, ogg, and hls URLs from transcripts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            transcripts_dir = Path(tmpdir) / "transcripts"
            term_dir = transcripts_dir / "2022" / "21-476"
            term_dir.mkdir(parents=True)

            transcript = {
                "metadata": {
                    "audio_urls": {
                        "mp3": "https://s3.amazonaws.com/bucket/audio.mp3",
                        "ogg": "https://s3.amazonaws.com/bucket/audio.ogg",
                        "hls": "https://s3.amazonaws.com/bucket/audio.m3u8",
                    }
                }
            }
            (term_dir / "oral_argument.json").write_text(json.dumps(transcript))

            urls = extract_audio_urls(transcripts_dir)

            assert len(urls) == 3
            assert "https://s3.amazonaws.com/bucket/audio.mp3" in urls
            assert "https://s3.amazonaws.com/bucket/audio.ogg" in urls
            assert "https://s3.amazonaws.com/bucket/audio.m3u8" in urls

    def test_empty_directory(self) -> None:
        """Return empty list for empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            transcripts_dir = Path(tmpdir) / "transcripts"
            transcripts_dir.mkdir()

            urls = extract_audio_urls(transcripts_dir)
            assert urls == []

    def test_nonexistent_directory(self) -> None:
        """Return empty list for nonexistent directory."""
        urls = extract_audio_urls(Path("/nonexistent/path"))
        assert urls == []

    def test_extract_audio_urls_filters_by_terms(self) -> None:
        """Only scan term dirs in terms list (parser_transcripts line 251)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            transcripts_dir = Path(tmpdir)
            for term in ("2023", "2024"):
                term_dir = transcripts_dir / term / "22-123"
                term_dir.mkdir(parents=True)
                transcript = {
                    "metadata": {
                        "audio_urls": {
                            "mp3": f"https://example.com/{term}/audio.mp3",
                        }
                    }
                }
                (term_dir / "oral_argument.json").write_text(json.dumps(transcript))

            urls = extract_audio_urls(transcripts_dir, terms=["2024"])
            assert len(urls) == 1
            assert "2024" in urls[0]

    def test_deduplicates_urls(self) -> None:
        """Deduplicate URLs across multiple transcripts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            transcripts_dir = Path(tmpdir) / "transcripts"
            term_dir = transcripts_dir / "2022" / "21-476"
            term_dir.mkdir(parents=True)

            # Same URL in multiple files
            transcript = {
                "metadata": {
                    "audio_urls": {
                        "mp3": "https://s3.amazonaws.com/bucket/shared.mp3",
                    }
                }
            }
            (term_dir / "file1.json").write_text(json.dumps(transcript))
            (term_dir / "file2.json").write_text(json.dumps(transcript))

            urls = extract_audio_urls(transcripts_dir)
            assert len(urls) == 1
