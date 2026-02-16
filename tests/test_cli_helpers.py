# Edited by Cursor: shared helpers for test_cli_* (lintok; no new exclusions).
"""Shared helpers for CLI tests."""

import re


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)
