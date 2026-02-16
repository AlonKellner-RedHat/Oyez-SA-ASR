# Edited by Cursor: split from test_build_rule_candidates for lintok.
"""Integration tests: build_rule_candidates (part 2 first half)."""

import json
from pathlib import Path

import pytest

from tests.test_build_rule_candidates_common import run_build_rule_candidates

pytestmark = pytest.mark.slow


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


def test_build_rule_candidates_non_speech_sic(tmp_path: Path) -> None:
    """Plan: 'fish may travel has (sic) many' -> non_speech_brackets candidate with span (sic) and correction ''."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "fish may travel has (sic) many"},
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
    sic_c = next((c for c in candidates if c.get("span") == "(sic)"), None)
    assert sic_c is not None, [c.get("span") for c in candidates]
    assert [co.get("text") for co in sic_c.get("corrections", []) if "text" in co] == [
        ""
    ]


def test_build_rule_candidates_non_speech_noon_recess(tmp_path: Path) -> None:
    """Fixture 'lunch counsel. [Noon Recess] Mr. Eggers,' produces non_speech_brackets candidate with empty correction."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "lunch counsel. [Noon Recess] Mr. Eggers,"},
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
    recess_cand = next(
        (c for c in candidates if c.get("span") == "[Noon Recess]"), None
    )
    assert recess_cand is not None, [c.get("span") for c in candidates]
    texts = [
        co.get("text") for co in recess_cand.get("corrections", []) if "text" in co
    ]
    assert "" in texts, texts
