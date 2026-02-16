# Edited by Cursor: split from test_build_rule_candidates for lintok.
"""Integration tests: build_rule_candidates (part 4 first half)."""

import json
from pathlib import Path

import pytest

from tests.test_build_rule_candidates_common import run_build_rule_candidates

pytestmark = pytest.mark.slow


def test_build_rule_candidates_roman_parens(tmp_path: Path) -> None:
    """Transcript with (ii) and (iv) produces roman_parens candidates with corrections two and four."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {
                        "index": 0,
                        "text": "to have (ii) so that when Romanette (iii) says same as (iv) and (vi)",
                    },
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
    path = out_dir / "roman_parens_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    spans = [c.get("span") for c in candidates]
    assert "(ii)" in spans, spans
    assert "(iv)" in spans, spans
    cand_ii = next(c for c in candidates if c.get("span") == "(ii)")
    assert any(co.get("text") == "two" for co in cand_ii.get("corrections", []))
    cand_iv = next(c for c in candidates if c.get("span") == "(iv)")
    assert any(co.get("text") == "four" for co in cand_iv.get("corrections", []))


def test_build_rule_candidates_letter_roman_clause(tmp_path: Path) -> None:
    """Transcript with '(C)(iii), Your Honor' produces letter_roman_clause candidate with correction 'cee three'."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "If you look at (C)(iii), Your Honor."},
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
    path = out_dir / "letter_roman_clause_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    spans = [c.get("span") for c in candidates]
    assert "(C)(iii)" in spans, spans
    cand = next(c for c in candidates if c.get("span") == "(C)(iii)")
    assert any(co.get("text") == "cee three" for co in cand.get("corrections", [])), (
        cand.get("corrections", [])
    )


def test_build_rule_candidates_letter_dash(tmp_path: Path) -> None:
    """Transcript with 'to the (R-5), which' and 'to the R-5, which' produce letter_dash_sequence candidates with correction 'ar five'."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "to the (R-5), which and to the R-5, which"},
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
    path = out_dir / "letter_dash_sequence_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    spans = [c.get("span") for c in candidates]
    assert "(R-5)" in spans, spans
    assert "R-5" in spans, spans
    for cand in candidates:
        assert any(co.get("text") == "ar five" for co in cand.get("corrections", [])), (
            cand.get("corrections", [])
        )
