# Edited by Cursor: split from test_build_rule_candidates for lintok.
"""Integration tests: build_rule_candidates (part 3 second half)."""

import json
from pathlib import Path

import pytest

from tests.test_build_rule_candidates_common import run_build_rule_candidates

pytestmark = pytest.mark.slow


def test_build_rule_candidates_editorial_dollar(tmp_path: Path) -> None:
    """Fixture with '$<forty-two thousand> [= 42,000]' -> editorial_dollar candidates with both corrections."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "Amount $<forty-two thousand> [= 42,000]."},
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
    path = out_dir / "editorial_dollar_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    span_val = "$<forty-two thousand> [= 42,000]"
    cand = next((c for c in candidates if c.get("span") == span_val), None)
    assert cand is not None, [c.get("span") for c in candidates]
    texts = [co.get("text") for co in cand.get("corrections", []) if "text" in co]
    assert (
        "forty-two thousand dollars" in texts and "forty-two thousand dollar" in texts
    ), texts


# Edited by Cursor (TDD plan item 6: known names MacKinnon, LeMaistre)
def test_build_rule_candidates_known_names_mackinnon_lemaistre(tmp_path: Path) -> None:
    """Fixture 'MacKinnon and LeMaistre' -> known_names_candidates contains those spans."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [{"index": 0, "text": "MacKinnon and LeMaistre"}],
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
    assert "MacKinnon" in spans, spans
    assert "LeMaistre" in spans, spans


def test_build_rule_candidates_known_names_lapenta(tmp_path: Path) -> None:
    """Transcript containing LaPenta produces known_names candidate (identity)."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [{"index": 0, "text": "Counsel LaPenta argued."}],
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
    assert "LaPenta" in spans, spans
