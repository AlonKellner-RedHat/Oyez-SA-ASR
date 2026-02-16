# Edited by Cursor: split from test_build_rule_candidates for lintok.
"""Integration tests: build_rule_candidates (part 4 first half)."""

import json
from pathlib import Path

import pytest

from tests.test_build_rule_candidates_common import run_build_rule_candidates

pytestmark = pytest.mark.slow


def test_build_rule_candidates_half_number_times(tmp_path: Path) -> None:
    """Fixture 'sold at 18 ½ times' yields half_number candidate with eighteen and a half times."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [{"index": 0, "text": "sold at 18 ½ times earnings."}],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    run_build_rule_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "half_number_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    cand = next(
        (
            c
            for c in candidates
            if "18" in (c.get("span") or "") and "times" in (c.get("span") or "")
        ),
        None,
    )
    assert cand is not None, [c.get("span") for c in candidates]
    texts = [co.get("text") for co in cand.get("corrections", []) if "text" in co]
    assert any("eighteen and a half times" in t for t in texts), texts


# Plan item 6: dual notation
def test_build_rule_candidates_dual_notation(tmp_path: Path) -> None:
    """Fixture with '<thirty> [= 30]' yields dual_notation_candidates with correction thirty."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [{"index": 0, "text": "See <thirty> [= 30] here."}],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    run_build_rule_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "dual_notation_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    span_val = "<thirty> [= 30]"
    cand = next((c for c in candidates if c.get("span") == span_val), None)
    assert cand is not None, [c.get("span") for c in candidates]
    texts = [co.get("text") for co in cand.get("corrections", []) if "text" in co]
    assert "thirty" in texts, texts


def test_build_rule_candidates_section_header(tmp_path: Path) -> None:
    """Turn ending with all-caps header produces section_header candidate with empty correction."""
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
                        "text": "It is late. REBUTTAL ARGUMENT OF MATTHEW D. McGILL",
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
    path = out_dir / "section_header_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    cand = next(
        (c for c in candidates if "REBUTTAL" in (c.get("span") or "")),
        None,
    )
    assert cand is not None, [c.get("span") for c in candidates]
    texts = [co.get("text") for co in cand.get("corrections", []) if "text" in co]
    assert "" in texts, texts
