# Edited by Cursor: awareness extraction for collect_asr_artifacts (lintok; no new exclusions).
"""Awareness and leading-decimal extraction from single-turn text."""

from scripts.collect_asr_artifacts_regex import (
    ALL_CAPS_LONG_RE,
    AWARENESS_SYMBOLS,
    LEADING_DECIMAL_RE,
    MIXED_CASE_RE,
    TIME_LIKE_RE,
)
from scripts.collect_asr_artifacts_text_core import _add


def _collect_from_text_awareness(text: str, artifacts: dict[str, object]) -> None:
    """Extract awareness_* and leading_decimal from a single turn text."""
    if not text or not isinstance(text, str):
        return
    for c in text:
        if ord(c) > 127:
            artifacts["awareness_non_ascii"][f"U+{ord(c):04X}"] += 1
    for m in MIXED_CASE_RE.finditer(text):
        _add(artifacts["awareness_mixed_case"], m.group(0), normalize=False)
    for m in ALL_CAPS_LONG_RE.finditer(text):
        _add(artifacts["awareness_all_caps_long"], m.group(0), normalize=False)
    for sym in AWARENESS_SYMBOLS:
        if sym in text:
            artifacts["awareness_symbols"][f"U+{ord(sym):04X}"] += 1
    if "..." in text:
        artifacts["awareness_symbols"]["..."] += 1
    for m in TIME_LIKE_RE.finditer(text):
        artifacts["awareness_time_like"][m.group(0)] += 1
    for m in LEADING_DECIMAL_RE.finditer(text):
        frag = m.group(1)
        artifacts["awareness_leading_decimal"][frag] += 1
        if len(frag) != 5 or not (frag.startswith(".1") or frag.startswith(".2")):
            artifacts["leading_decimal"][frag] += 1
