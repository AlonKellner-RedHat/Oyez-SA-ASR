# Edited by Cursor: split from test_transcript_models (lintok; plan).
"""Tests for build_transcript_to_case_map."""

import json
import tempfile
from pathlib import Path

from oyez_sa_asr.scraper.parser_transcripts import build_transcript_to_case_map


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
            assert 3024 in case_map
            assert case_map[3024] == ("2024", "22-123")
            assert 3023 not in case_map
