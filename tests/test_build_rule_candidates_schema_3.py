# Edited by Cursor: split from test_build_rule_candidates for lintok.
"""Integration tests: schema and early rules (3/3) (split_word_merge, latin, quote, parens, dash, non_speech)."""

import json
from pathlib import Path

import pytest

from tests.test_build_rule_candidates_common import run_build_rule_candidates

pytestmark = pytest.mark.slow


def test_build_rule_candidates_parens_with_spaces_output(tmp_path: Path) -> None:
    """Fixture with (a ) and ( 12); assert single_letter_parens and number_parens corrections."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "(a ) and ( 12)."},
                ],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    run_build_rule_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    letter_path = out_dir / "single_letter_parens_candidates.json"
    number_path = out_dir / "number_parens_candidates.json"
    assert letter_path.exists(), list(out_dir.iterdir())
    assert number_path.exists(), list(out_dir.iterdir())
    letter_data = json.loads(letter_path.read_text())
    number_data = json.loads(number_path.read_text())
    a_cand = next(
        (c for c in letter_data.get("candidates", []) if "a" in c.get("span", "")),
        None,
    )
    twelve_cand = next(
        (c for c in number_data.get("candidates", []) if "12" in c.get("span", "")),
        None,
    )
    assert a_cand is not None
    assert twelve_cand is not None
    a_texts = [co.get("text") for co in a_cand.get("corrections", []) if "text" in co]
    twelve_texts = [
        co.get("text") for co in twelve_cand.get("corrections", []) if "text" in co
    ]
    assert a_texts == ["ay"], a_texts
    assert twelve_texts == ["twelve"], twelve_texts


def test_build_rule_candidates_non_speech_brackets_output(tmp_path: Path) -> None:
    """Fixture with (Inaudible) and [Laughter]; assert non_speech_brackets corrections [""]."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "(Inaudible) and [Laughter]."},
                ],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    run_build_rule_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "non_speech_brackets_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    assert data.get("rule_id") == "non_speech_brackets"
    candidates = data.get("candidates", [])
    assert candidates
    for c in candidates:
        corrections = c.get("corrections", [])
        texts = [co.get("text") for co in corrections if "text" in co]
        assert texts == [""], (c.get("span"), texts)


def test_build_rule_candidates_non_speech_brackets_inaudibles(tmp_path: Path) -> None:
    """Fixture with [Inaudibles.] (keyword 'inaudible') -> non_speech_brackets with correction ''."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [{"index": 0, "text": "Then [Inaudibles.] and we continued."}],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    run_build_rule_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "non_speech_brackets_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    cand = next((c for c in candidates if "Inaudibles" in (c.get("span") or "")), None)
    assert cand is not None, [c.get("span") for c in candidates]
    texts = [co.get("text") for co in cand.get("corrections", []) if "text" in co]
    assert "" in texts, texts


def test_build_rule_candidates_non_speech_overlap_and_2lev(tmp_path: Path) -> None:
    """Plan: (Overlap) and (Inaudibel) (2-Lev inaudible) produce non_speech_brackets with empty correction."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "Then (Overlap) and (Inaudibel) here."},
                ],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    run_build_rule_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "non_speech_brackets_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    overlap_c = next((c for c in candidates if c.get("span") == "(Overlap)"), None)
    inau_c = next((c for c in candidates if c.get("span") == "(Inaudibel)"), None)
    assert overlap_c is not None and inau_c is not None, [
        c.get("span") for c in candidates
    ]
    assert [
        co.get("text") for co in overlap_c.get("corrections", []) if "text" in co
    ] == [""]
    assert [co.get("text") for co in inau_c.get("corrections", []) if "text" in co] == [
        ""
    ]
