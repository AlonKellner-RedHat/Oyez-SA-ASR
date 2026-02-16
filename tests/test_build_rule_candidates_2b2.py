# Edited by Cursor: split from test_build_rule_candidates for lintok.
"""Integration tests: build_rule_candidates (part 2 second half)."""

import json
from pathlib import Path

import pytest

from tests.test_build_rule_candidates_common import run_build_rule_candidates

pytestmark = pytest.mark.slow


def test_build_rule_candidates_digit_letter_mixed_output(tmp_path: Path) -> None:
    """Fixture with 2d, 640L, 1392(d); assert digit_letter_mixed_candidates.json has spoken corrections."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "See 2d and 640L and 1392(d)."},
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
    assert data.get("rule_id") == "digit_letter_mixed"
    candidates = data.get("candidates", [])
    c2d = next((c for c in candidates if c.get("span") == "2d"), None)
    c640 = next((c for c in candidates if c.get("span") == "640L"), None)
    c1392 = next((c for c in candidates if "1392" in c.get("span", "")), None)
    assert c2d is not None, [c.get("span") for c in candidates]
    assert c640 is not None, [c.get("span") for c in candidates]
    assert c1392 is not None, [c.get("span") for c in candidates]
    t2d = [co.get("text") for co in c2d.get("corrections", []) if "text" in co]
    t640 = [co.get("text") for co in c640.get("corrections", []) if "text" in co]
    t1392 = [co.get("text") for co in c1392.get("corrections", []) if "text" in co]
    assert t2d == ["two dee"], t2d
    assert "six forty ell" in t640, t640
    assert "thirteen ninety two dee" in t1392, t1392


def test_build_rule_candidates_numbered_list_marker_output(tmp_path: Path) -> None:
    """Fixture with list context '1) first' and '5) fifth'; assert numbered_list_marker has one, five."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "Reasons: 1) first point 5) fifth."},
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
    path = out_dir / "numbered_list_marker_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    assert data.get("rule_id") == "numbered_list_marker"
    candidates = data.get("candidates", [])
    one_cand = next((c for c in candidates if c.get("span") == "1)"), None)
    five_cand = next((c for c in candidates if c.get("span") == "5)"), None)
    assert one_cand is not None, [c.get("span") for c in candidates]
    assert five_cand is not None, [c.get("span") for c in candidates]
    t1 = [co.get("text") for co in one_cand.get("corrections", []) if "text" in co]
    t5 = [co.get("text") for co in five_cand.get("corrections", []) if "text" in co]
    assert t1 == ["one"], t1
    assert t5 == ["five"], t5


def test_build_rule_candidates_numbered_list_comma(tmp_path: Path) -> None:
    """Transcript 'Well, 1), if you assume' produces numbered_list_marker candidate for 1) with correction one."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [{"index": 0, "text": "Well, 1), if you assume"}],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    run_build_rule_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "numbered_list_marker_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    one_cand = next((c for c in candidates if c.get("span") == "1)"), None)
    assert one_cand is not None, [c.get("span") for c in candidates]
    assert any(co.get("text") == "one" for co in one_cand.get("corrections", []))
