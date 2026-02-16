# Edited by Cursor: split from test_cli_process_speakers (lintok; plan).
"""Shared helpers for process speakers tests."""

import re

from typer.testing import CliRunner

runner = CliRunner()


def _strip_ansi(text: str) -> str:
    """Strip ANSI escape codes from a string."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _create_transcript(
    term: str,
    docket: str,
    transcript_type: str = "oral_argument",
    turns: list[dict] | None = None,
) -> dict:
    """Create a mock transcript structure."""
    if turns is None:
        turns = [
            {
                "index": 0,
                "speaker_id": 123,
                "speaker_name": "Justice Smith",
                "start": 0.0,
                "stop": 10.0,
                "duration": 10.0,
                "is_valid": True,
                "word_count": 50,
                "text": "This is a test.",
            },
            {
                "index": 1,
                "speaker_id": 456,
                "speaker_name": "Mr. Jones",
                "start": 10.0,
                "stop": 20.0,
                "duration": 10.0,
                "is_valid": True,
                "word_count": 60,
                "text": "Response to the test.",
            },
        ]
    return {
        "id": 1,
        "case_docket": docket,
        "term": term,
        "type": transcript_type,
        "title": "Oral Argument",
        "metadata": {"duration_seconds": 100.0},
        "turns": turns,
    }


def _create_case(term: str, docket: str, name: str = "Test v. Case") -> dict:
    """Create a mock case structure."""
    return {
        "id": 1,
        "name": name,
        "docket_number": docket,
        "term": term,
        "href": f"https://api.oyez.org/cases/{term}/{docket}",
    }
