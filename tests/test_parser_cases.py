# Edited by Claude
"""Tests for ProcessedCase dataclass."""

import json
import tempfile
from pathlib import Path

from oyez_sa_asr.scraper.parser_cases import ProcessedCase, extract_media_urls


class TestProcessedCase:
    """Tests for ProcessedCase dataclass."""

    def test_from_raw(self) -> None:
        """Parse case from raw API response."""
        raw = {
            "ID": 12345,
            "name": "Test v. Case",
            "docket_number": "21-476",
            "term": "2022",
            "href": "https://example.com/cases/2022/21-476",
            "timeline": [
                {"event": "Argued", "dates": [1670198400]},
                {"event": "Decided", "dates": [1688083200]},
            ],
            "decisions": [
                {
                    "decision_type": "majority opinion",
                    "winning_party": "Test",
                    "majority_vote": 6,
                    "minority_vote": 3,
                }
            ],
            "oral_argument_audio": [
                {
                    "id": 25123,
                    "title": "Oral Argument - December 05, 2022",
                    "href": "https://example.com/case_media/oral_argument_audio/25123",
                    "unavailable": None,
                }
            ],
            "opinion_announcement": [
                {
                    "id": 25574,
                    "title": "Opinion Announcement - June 30, 2023",
                    "href": "https://example.com/case_media/opinion_announcement_audio/25574",
                    "unavailable": False,
                }
            ],
        }
        case = ProcessedCase.from_raw(raw)
        assert case.id == 12345
        assert case.name == "Test v. Case"
        assert case.docket_number == "21-476"
        assert case.term == "2022"
        assert len(case.timeline) == 2
        assert case.decision is not None
        assert case.decision.winner == "Test"
        assert len(case.oral_arguments) == 1
        assert len(case.opinion_announcements) == 1

    def test_save_creates_file(self, tmp_path: Path) -> None:
        """Save creates JSON file with correct structure."""
        case = ProcessedCase(
            id=123,
            name="Test v. Case",
            docket_number="21-476",
            term="2022",
            href="https://example.com/cases/2022/21-476",
            timeline=[],
            decision=None,
            oral_arguments=[],
            opinion_announcements=[],
        )
        case.save(tmp_path)

        expected_file = tmp_path / "2022" / "21-476.json"
        assert expected_file.exists()

        with expected_file.open() as f:
            data = json.load(f)
        assert data["id"] == 123
        assert data["name"] == "Test v. Case"

    def test_from_raw_no_audio(self) -> None:
        """Parse case with no audio."""
        raw = {
            "ID": 999,
            "name": "No Audio Case",
            "docket_number": "99-999",
            "term": "1999",
            "href": "https://example.com/cases/1999/99-999",
            "timeline": [],
            "decisions": [],
            "oral_argument_audio": None,
            "opinion_announcement": None,
        }
        case = ProcessedCase.from_raw(raw)
        assert len(case.oral_arguments) == 0
        assert len(case.opinion_announcements) == 0

    def test_save_with_source_path(self, tmp_path: Path) -> None:
        """Save includes _meta.source_path when provided."""
        case = ProcessedCase(
            id=456,
            name="Provenance v. Test",
            docket_number="22-789",
            term="2023",
            href="https://example.com/cases/2023/22-789",
            timeline=[],
            decision=None,
            oral_arguments=[],
            opinion_announcements=[],
        )
        src = Path("/cache/raw/abc123.json")
        case.save(tmp_path, source_path=src)

        out_file = tmp_path / "2023" / "22-789.json"
        with out_file.open() as f:
            data = json.load(f)
        assert "_meta" in data, "Saved case must include _meta"
        assert data["_meta"]["source_path"] == str(src)


class TestExtractMediaUrls:
    """Tests for extract_media_urls function."""

    def test_extract_media_urls_returns_empty_when_dir_not_exists(self) -> None:
        """Should return empty list when cases_dir doesn't exist (line 37)."""
        urls = extract_media_urls(Path("/nonexistent/path"))
        assert urls == []

    def test_extract_media_urls_skips_non_directories(self) -> None:
        """Should skip non-directory entries (lines 43, 45)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cases_dir = Path(tmpdir)
            # Create a file (not a directory) in cases_dir
            (cases_dir / "not_a_dir.txt").write_text("test")

            # Create a valid term directory
            term_dir = cases_dir / "2024"
            term_dir.mkdir()
            case = {
                "id": 1,
                "oral_arguments": [
                    {"href": "https://example.com/audio.mp3", "unavailable": False}
                ],
                "opinion_announcements": [],
            }
            (term_dir / "22-123.json").write_text(json.dumps(case))

            urls = extract_media_urls(cases_dir)
            # Should only extract from valid directories, skip non-directories
            assert len(urls) == 1

    def test_extract_media_urls_handles_exceptions(self) -> None:
        """Should handle JSONDecodeError, KeyError, TypeError (lines 60-61)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cases_dir = Path(tmpdir)
            term_dir = cases_dir / "2024"
            term_dir.mkdir()

            # Create invalid JSON file
            (term_dir / "invalid.json").write_text("{ invalid json }")

            # Create file with missing keys
            incomplete = {"id": 1}  # Missing oral_arguments, opinion_announcements
            (term_dir / "incomplete.json").write_text(json.dumps(incomplete))

            # Create valid case file
            case = {
                "id": 2,
                "oral_arguments": [
                    {"href": "https://example.com/audio.mp3", "unavailable": False}
                ],
                "opinion_announcements": [],
            }
            (term_dir / "valid.json").write_text(json.dumps(case))

            urls = extract_media_urls(cases_dir)
            # Should handle exceptions gracefully and only extract from valid file
            assert len(urls) == 1
