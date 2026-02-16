# Edited by Cursor: scan helpers (lintok; no new exclusions).
"""Regex and Latin scan helpers for the scanner registry."""

import bisect

from scripts.build_rule_candidates_registry_regex import (
    LATIN_EXTENDED_CHAR_RE,
    RULE_REGEX,
)


def _scan_turn(text: str, path_str: str) -> list[tuple[str, int, str, str]]:
    """Emit (rule_id, start_index, span, path_str) for each match."""
    out: list[tuple[str, int, str, str]] = []
    for rule_id, (pattern, group_ix) in RULE_REGEX.items():
        for m in pattern.finditer(text):
            span = m.group(0) if group_ix == 0 else m.group(group_ix)
            out.append((rule_id, m.start(), span, path_str))
    return out


def _scan_turn_batch(
    full_text: str,
    _path_str: str,
    turn_boundaries: list[tuple[int, int, str, int]],
) -> list[tuple[str, int, int, str, str]]:
    """Emit (rule_id, turn_index, start_index, span, path_str) for each match."""
    if not turn_boundaries:
        return []
    turn_starts = [b[0] for b in turn_boundaries]
    out: list[tuple[str, int, int, str, str]] = []
    for rule_id, (pattern, group_ix) in RULE_REGEX.items():
        for m in pattern.finditer(full_text):
            pos = m.start()
            idx = bisect.bisect_right(turn_starts, pos) - 1
            if idx < 0 or pos >= turn_boundaries[idx][1]:
                continue
            start, _end, pstr, turn_index = turn_boundaries[idx]
            span = m.group(0) if group_ix == 0 else m.group(group_ix)
            out.append((rule_id, turn_index, pos - start, span, pstr))
    return out


def _scan_turn_filter(rule_id: str, span: str) -> bool:
    """Return False to skip adding this result (leading_decimal .YYYY, single_letter_parens (i))."""
    if (
        rule_id == "leading_decimal"
        and len(span) == 5
        and span.startswith(".")
        and span[1:].isdigit()
        and (span[1:].startswith("1") or span[1:].startswith("20"))
    ):
        return False
    if (
        rule_id == "single_letter_parens"
        and len(span) >= 3
        and span[0] == "("
        and span[-1] == ")"
    ):
        inner = span[1:-1].strip().lower()
        if inner == "i":
            return False
    return True


def _scan_turn_latin(text: str, path_str: str) -> list[tuple[str, int, str, str]]:
    """Emit (latin_extended, start_index, word, path_str) for words containing Latin extended chars."""
    out: list[tuple[str, int, str, str]] = []
    seen_start: set[int] = set()
    for m in LATIN_EXTENDED_CHAR_RE.finditer(text):
        start = m.start()
        end = m.end()
        while start > 0 and not text[start - 1].isspace():
            start -= 1
        while end < len(text) and not text[end].isspace():
            end += 1
        if start not in seen_start:
            seen_start.add(start)
            out.append(("latin_extended", start, text[start:end], path_str))
    return out
