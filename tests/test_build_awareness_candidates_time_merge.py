# Edited by Cursor: split from test_build_awareness_candidates (lintok; no new exclusions).
"""Tests: build_awareness_candidates time_like, merge, stem."""

import json
from pathlib import Path

import pytest

from tests.test_build_awareness_candidates_helpers import (
    _run_build_awareness_candidates,
)

pytestmark = pytest.mark.slow


def test_build_awareness_candidates_time_like(tmp_path: Path) -> None:
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "At 12:34 and 00:35:34 and 9:38.5 we saw it."}
                ],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _run_build_awareness_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "awareness_time_like_candidates.json"
    assert path.exists()
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    spans = [c.get("span") for c in candidates]
    assert "12:34" in spans and "00:35:34" in spans and "9:38.5" in spans


def test_build_awareness_candidates_merge_no_correction(tmp_path: Path) -> None:
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {"metadata": {}, "turns": [{"index": 0, "text": "That is right t."}]},
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _run_build_awareness_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "awareness_non_dictionary_candidates.json"
    assert path.exists()
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    cand_right = next((c for c in candidates if c.get("span") == "right"), None)
    if cand_right is not None:
        assert cand_right.get("corrections") == []


def test_awareness_does_not_flag_word_whose_stem_in_dict() -> None:
    from scripts.build_awareness_candidates import _extract_awareness  # noqa: PLC0415

    dic = frozenset(
        {
            "accommod",
            "that",
            "is",
            "very",
            "sympathetic",
            "to",
            "the",
            "concern",
            "venue",
        }
    )
    text = "That is very sympathetic to the concern that venue accommodation"
    out = _extract_awareness(text, dic=dic)
    non_dict_spans = [
        span for (cat, _si, span) in out if cat == "awareness_non_dictionary"
    ]
    assert "accommodation" not in non_dict_spans
