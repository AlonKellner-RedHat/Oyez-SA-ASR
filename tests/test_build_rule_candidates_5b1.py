# Edited by Cursor: split from test_build_rule_candidates for lintok.
"""Integration tests: build_rule_candidates (part 5 second half)."""

import json
from pathlib import Path

import pytest

from tests.test_build_rule_candidates_common import run_build_rule_candidates

pytestmark = pytest.mark.slow


def test_build_rule_candidates_short_mixed_acronym(tmp_path: Path) -> None:
    """Transcript with DoD and DiRe produces short_mixed_acronym candidates with letter-by-letter corrections."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "The DoD and DiRe cases."},
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
    path = out_dir / "short_mixed_acronym_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    dod_cand = next((c for c in candidates if c.get("span") == "DoD"), None)
    dire_cand = next((c for c in candidates if c.get("span") == "DiRe"), None)
    assert dod_cand is not None and dire_cand is not None, [
        c.get("span") for c in candidates
    ]
    dod_texts = [
        co.get("text") for co in dod_cand.get("corrections", []) if "text" in co
    ]
    dire_texts = [
        co.get("text") for co in dire_cand.get("corrections", []) if "text" in co
    ]
    assert "dee oh dee" in dod_texts, dod_texts
    assert "dee eye ar ee" in dire_texts, dire_texts


# Plan item 3: common acronym PhD
def test_build_rule_candidates_common_acronym_phd(tmp_path: Path) -> None:
    """Fixture with 'PhD' produces common_acronym candidate with correction pee aych dee."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [{"index": 0, "text": "She has a PhD in law."}],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    run_build_rule_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "common_acronym_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    phd_cand = next((c for c in candidates if c.get("span") == "PhD"), None)
    assert phd_cand is not None, [c.get("span") for c in candidates]
    texts = [co.get("text") for co in phd_cand.get("corrections", []) if "text" in co]
    assert "pee aych dee" in texts, texts


# Plan item 2: title abbreviations
def test_build_rule_candidates_title_abbreviation(tmp_path: Path) -> None:
    """Fixture 'Mr. Smith and Dr. Jones' yields title_abbreviation_candidates with Mr., Dr. and corrections Mister, Doctor."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [{"index": 0, "text": "Mr. Smith and Dr. Jones"}],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    run_build_rule_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "title_abbreviation_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    mr_cand = next((c for c in candidates if c.get("span") == "Mr."), None)
    dr_cand = next((c for c in candidates if c.get("span") == "Dr."), None)
    assert mr_cand is not None and dr_cand is not None, [
        c.get("span") for c in candidates
    ]
    mr_texts = [co.get("text") for co in mr_cand.get("corrections", []) if "text" in co]
    dr_texts = [co.get("text") for co in dr_cand.get("corrections", []) if "text" in co]
    assert "Mister" in mr_texts, mr_texts
    assert "Doctor" in dr_texts, dr_texts


# Plan item 1: DeShaney
