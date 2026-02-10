# Edited by Cursor (ASR normalization rules expansion)
"""Scan for known name patterns (McLaughlin, McCoy, FitzGerald) — handled, no correction."""

import re

# Mc + capital + lowercase(s); Fitz + capital + lowercase(s). Mark as handled only.
KNOWN_NAMES_RE = re.compile(r"\b(?:Mc[A-Z][a-z]+|Fitz[A-Z][a-z]+)\b")


def scan_turn_known_names(
    text: str,
    path_str: str = "",
) -> list[tuple[str, int, str, str]]:
    """Emit (rule_id, start_index, span, path_str) for known-name tokens (identity normalizer)."""
    result: list[tuple[str, int, str, str]] = []
    for m in KNOWN_NAMES_RE.finditer(text):
        result.append(("known_names", m.start(), m.group(0), path_str))
    return result
