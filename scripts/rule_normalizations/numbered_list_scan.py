# Edited by Cursor (ASR normalization rules expansion)
"""Scan for numbered list markers (1), 5)) only when unmatched (list context)."""

import re

NUMBERED_LIST_RE = re.compile(r"\b(\d+)\)")


def scan_turn_numbered_list(
    text: str,
    path_str: str = "",
) -> list[tuple[str, int, str, str]]:
    """Emit (rule_id, start_index, span, path_str) for 1) only when list-marker context (preceded by start/space/colon/period, followed by space)."""
    result: list[tuple[str, int, str, str]] = []
    n = len(text)
    for m in NUMBERED_LIST_RE.finditer(text):
        start, end = m.start(), m.end()
        preceded = start == 0 or (start > 0 and text[start - 1] in " \t\n.:")
        followed = end >= n or text[end].isspace()
        if preceded and followed:
            result.append(("numbered_list_marker", start, m.group(0), path_str))
    return result
