# Edited by Cursor: brackets/dash/ellipsis extraction for collect_asr_artifacts (lintok; no new exclusions).
"""Bracket, editorial, dash, ellipsis, structural extraction from single-turn text."""

import re

from scripts.collect_asr_artifacts_regex import (
    _BRACKET_CONTENT_MAX,
    _NON_SPEECH_CONTENT_RE,
    BRACKETS_ANGLE_RE,
    BRACKETS_CURLY_RE,
    BRACKETS_NUMBERED_RE,
    BRACKETS_PAREN_RE,
    BRACKETS_SQUARE_RE,
    DASH_RANGE_RE,
    EDITORIAL_SQUARE_RE,
    STRUCTURAL_PAREN_LETTER_RE,
    STRUCTURAL_PAREN_NUM_RE,
)


def _collect_from_text_brackets(text: str, artifacts: dict[str, object]) -> None:
    """Extract bracket, editorial, dash, ellipsis, structural from a single turn text."""
    if not text or not isinstance(text, str):
        return
    for m in BRACKETS_PAREN_RE.finditer(text):
        content = m.group(1).strip()
        if len(content) > _BRACKET_CONTENT_MAX:
            content = content[:_BRACKET_CONTENT_MAX] + "..."
        key = f"({content})" if content else "()"
        artifacts["awareness_brackets_parens"][key] += 1
        norm = content.strip().rstrip(".").strip()
        if norm and _NON_SPEECH_CONTENT_RE.search(norm):
            artifacts["non_speech_brackets"][key] += 1
    for m in BRACKETS_SQUARE_RE.finditer(text):
        content = m.group(1).strip()
        if len(content) > _BRACKET_CONTENT_MAX:
            content = content[:_BRACKET_CONTENT_MAX] + "..."
        key = f"[{content}]" if content else "[]"
        artifacts["awareness_brackets_square"][key] += 1
        norm = content.strip().rstrip(".").strip()
        if norm and _NON_SPEECH_CONTENT_RE.search(norm):
            artifacts["non_speech_brackets"][key] += 1
    for m in BRACKETS_CURLY_RE.finditer(text):
        content = m.group(1).strip()
        if len(content) > _BRACKET_CONTENT_MAX:
            content = content[:_BRACKET_CONTENT_MAX] + "..."
        key = f"{{{content}}}" if content else "{}"
        artifacts["awareness_brackets_curly"][key] += 1
    for m in BRACKETS_NUMBERED_RE.finditer(text):
        artifacts["awareness_brackets_numbered"][m.group(0)] += 1
        artifacts["numbered_list_marker"][m.group(0)] += 1
    for m in BRACKETS_ANGLE_RE.finditer(text):
        key = m.group(0)
        if len(key) > _BRACKET_CONTENT_MAX + 2:
            key = key[: _BRACKET_CONTENT_MAX + 1] + "...>"
        artifacts["awareness_brackets_angle"][key] += 1
    for m in EDITORIAL_SQUARE_RE.finditer(text):
        artifacts["editorial_square_bracket"][m.group(0)] += 1
    for m in DASH_RANGE_RE.finditer(text):
        artifacts["dash_range"][m.group(0)] += 1
    for _ in re.finditer(r"\.\.\.", text):
        artifacts["ellipsis"]["..."] += 1
    if "\u2026" in text:
        artifacts["ellipsis"]["U+2026"] += text.count("\u2026")
    for m in STRUCTURAL_PAREN_LETTER_RE.finditer(text):
        artifacts["structural_bracket"][m.group(0)] += 1
    for m in STRUCTURAL_PAREN_NUM_RE.finditer(text):
        artifacts["structural_bracket"][m.group(0)] += 1
