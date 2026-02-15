# Edited by Cursor (ASR normalization rules expansion)
"""Scan for numbered list markers (1), 5)) only when unmatched (list context)."""

import re

NUMBERED_LIST_RE = re.compile(r"\b(\d+)\)")
# Hyphen U+002D, en-dash U+2013 (e.g. "26-10)" in "page A (26-10).")
PRECEDED_CHARS = " \t\n.:," + "\u002d\u2013"


def scan_turn_numbered_list(
    text: str,
    path_str: str = "",
) -> list[tuple[str, int, str, str]]:
    """Emit (rule_id, start_index, span, path_str) for N) when list-marker context (preceded by start/space/colon/period/comma/hyphen/en-dash; followed by space/comma/-/./:/(). Edited by Cursor (awareness_brackets_numbered)."""
    result: list[tuple[str, int, str, str]] = []
    n = len(text)
    for m in NUMBERED_LIST_RE.finditer(text):
        start, end = m.start(), m.end()
        preceded = start == 0 or (start > 0 and text[start - 1] in PRECEDED_CHARS)
        # Allow followed by space, comma, dash (1)--), period (2)...), colon (42):), open-paren (67)(c)
        followed = end >= n or text[end].isspace() or text[end] in ".,-:("
        if preceded and followed:
            result.append(("numbered_list_marker", start, m.group(0), path_str))
    return result
