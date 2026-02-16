# Edited by Cursor: split from test_cli_process (lintok; plan).
"""Shared helpers and TestHelperFunctions for process subcommand tests."""

import re

from typer.testing import CliRunner

from oyez_sa_asr.cli_process_cases import _get_term_from_raw

runner = CliRunner()


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_term_from_raw_with_term(self) -> None:
        """Extracts term from raw data."""
        result = _get_term_from_raw({"term": "2024"})
        assert result == "2024"

    def test_get_term_from_raw_no_term(self) -> None:
        """Returns None for missing term."""
        result = _get_term_from_raw({})
        assert result is None

    def test_get_term_from_raw_empty_term(self) -> None:
        """Returns None for empty term."""
        result = _get_term_from_raw({"term": ""})
        assert result is None
