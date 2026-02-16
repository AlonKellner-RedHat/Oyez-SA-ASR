# Edited by Cursor: thin composer for text extraction (lintok; no new exclusions).
"""Extract artifact candidates from single-turn text and speaker lists."""

from collections import Counter

from scripts.collect_asr_artifacts_text_awareness import _collect_from_text_awareness
from scripts.collect_asr_artifacts_text_brackets import _collect_from_text_brackets
from scripts.collect_asr_artifacts_text_core import (
    _collect_from_text_core,
    collect_from_speakers,
)


def collect_from_text(text: str, artifacts: dict[str, Counter[str]]) -> None:
    """Extract artifact candidates from a single turn text."""
    _collect_from_text_core(text, artifacts)
    _collect_from_text_awareness(text, artifacts)
    _collect_from_text_brackets(text, artifacts)


__all__ = ["collect_from_speakers", "collect_from_text"]
