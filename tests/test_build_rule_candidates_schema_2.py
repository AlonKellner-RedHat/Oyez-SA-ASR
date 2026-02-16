# Edited by Cursor: split from test_build_rule_candidates for lintok.
"""Integration tests: schema and early rules (2/3) (split_word_merge, latin, quote, parens, dash, non_speech)."""

import json
from pathlib import Path

import pytest

from tests.test_build_rule_candidates_common import run_build_rule_candidates

pytestmark = pytest.mark.slow


def test_build_rule_candidates_quote_output(tmp_path: Path) -> None:
    """Fixture with mixed quotes; assert open/close_double_quote_candidates.json exist with 10 corrections."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": 'The word "a judicial procedure."'},
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

    open_path = out_dir / "open_double_quote_candidates.json"
    close_path = out_dir / "close_double_quote_candidates.json"
    assert open_path.exists(), list(out_dir.iterdir())
    assert close_path.exists(), list(out_dir.iterdir())
    open_data = json.loads(open_path.read_text())
    close_data = json.loads(close_path.read_text())
    assert open_data.get("rule_id") == "open_double_quote"
    assert close_data.get("rule_id") == "close_double_quote"
    expected_corrections = [
        "",
        "quote",
        "start quote",
        "open quote",
        "open the quote",
        "I quote",
        "and I quote",
        "end quote",
        "close quote",
        "close the quote",
    ]
    for data in (open_data, close_data):
        candidates = data.get("candidates", [])
        assert candidates
        for c in candidates:
            corrections = c.get("corrections", [])
            texts = [co.get("text") for co in corrections if "text" in co]
            assert texts == expected_corrections, (data.get("rule_id"), texts)


# Edited by Cursor
def test_build_rule_candidates_single_letter_parens_output(tmp_path: Path) -> None:
    """Fixture with (a) and (b); assert single_letter_parens_candidates.json has corrections ay, bee."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "(a) and (b) option (c)."},
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

    path = out_dir / "single_letter_parens_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    assert data.get("rule_id") == "single_letter_parens"
    candidates = data.get("candidates", [])
    spans = [c.get("span") for c in candidates]
    assert "(a)" in spans and "(b)" in spans
    a_cand = next(c for c in candidates if c.get("span") == "(a)")
    b_cand = next(c for c in candidates if c.get("span") == "(b)")
    a_texts = [co.get("text") for co in a_cand.get("corrections", []) if "text" in co]
    b_texts = [co.get("text") for co in b_cand.get("corrections", []) if "text" in co]
    assert a_texts == ["ay"], a_texts
    assert b_texts == ["bee"], b_texts


def test_build_rule_candidates_number_parens_output(tmp_path: Path) -> None:
    """Fixture with (1) and (32); assert number_parens_candidates.json has one, thirty two."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "See (1) and (32)."},
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

    path = out_dir / "number_parens_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    assert data.get("rule_id") == "number_parens"
    candidates = data.get("candidates", [])
    one_cand = next((c for c in candidates if c.get("span") == "(1)"), None)
    thirty2_cand = next((c for c in candidates if c.get("span") == "(32)"), None)
    assert one_cand is not None, [c.get("span") for c in candidates]
    assert thirty2_cand is not None, [c.get("span") for c in candidates]
    one_texts = [
        co.get("text") for co in one_cand.get("corrections", []) if "text" in co
    ]
    thirty2_texts = [
        co.get("text") for co in thirty2_cand.get("corrections", []) if "text" in co
    ]
    assert one_texts == ["one"], one_texts
    assert thirty2_texts == ["thirty two"], thirty2_texts


def test_build_rule_candidates_dash_output(tmp_path: Path) -> None:
    """Fixture with en/em dash or double hyphen; assert dash_candidates.json normalizes to -."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    # en dash U+2013, em dash U+2014, and ASCII --
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "word\u2013word and two--dashes."},
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

    path = out_dir / "dash_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    assert data.get("rule_id") == "dash"
    candidates = data.get("candidates", [])
    assert candidates
    for c in candidates:
        corrections = c.get("corrections", [])
        texts = [co.get("text") for co in corrections if "text" in co]
        assert texts == ["-"], (c.get("span"), texts)
