# Edited by Cursor: split from test_build_rule_candidates for lintok.
"""Integration tests: build_rule_candidates (part 5 second half)."""

import json
from pathlib import Path

import pytest

from tests.test_build_rule_candidates_common import run_build_rule_candidates

pytestmark = pytest.mark.slow


def test_build_rule_candidates_known_names_deshaney(tmp_path: Path) -> None:
    """Fixture containing 'DeShaney' yields known_names_candidates with that span."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [{"index": 0, "text": "See DeShaney and others."}],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    run_build_rule_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "known_names_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    spans = [c.get("span") for c in candidates]
    assert "DeShaney" in spans, spans


# Edited by Cursor (TDD plan item 5: double-letter parens (ph))
def test_build_rule_candidates_double_letter_parens(tmp_path: Path) -> None:
    """Fixture 'See (ph).' -> candidates with span '(ph)' and correction 'pee aych'."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [{"index": 0, "text": "See (ph)."}],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    run_build_rule_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "double_letter_parens_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    ph_cand = next((c for c in candidates if c.get("span") == "(ph)"), None)
    assert ph_cand is not None, [c.get("span") for c in candidates]
    texts = [co.get("text") for co in ph_cand.get("corrections", []) if "text" in co]
    assert "pee aych" in texts, texts


# Edited by Cursor (TDD plan item 4: digit-letter F2A, 1395(ff))
def test_build_rule_candidates_digit_letter_f2a_1395ff(tmp_path: Path) -> None:
    """Fixture 'F2A and 1395(ff)' -> digit_letter_mixed_candidates has those spans."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "F2A and 1395(ff)."},
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
    path = out_dir / "digit_letter_mixed_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    spans = [c.get("span") for c in candidates]
    assert "F2A" in spans, spans
    assert "1395(ff)" in spans, spans


# Edited by Cursor (TDD plan item 1: symbols and currency)
def test_build_rule_candidates_symbols_currency(tmp_path: Path) -> None:
    """Fixture with '§ §1519 © £ £40'; assert currency/symbol candidates and £40 both corrections."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "§ §1519 © £ £40"},
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
    path = out_dir / "currency_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    pound40 = next((c for c in candidates if c.get("span") == "£40"), None)
    assert pound40 is not None, [c.get("span") for c in candidates]
    texts = [co.get("text") for co in pound40.get("corrections", []) if "text" in co]
    assert "forty pounds" in texts and "forty pound" in texts, texts
