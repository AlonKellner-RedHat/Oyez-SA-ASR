# Edited by Cursor: split from test_build_rule_candidates for lintok.
"""Integration tests: build_rule_candidates (part 3 first half)."""

import json
from pathlib import Path

import pytest

from tests.test_build_rule_candidates_common import run_build_rule_candidates

pytestmark = pytest.mark.slow


def test_build_rule_candidates_numbered_list_followed_by_dash(tmp_path: Path) -> None:
    """Transcript 'in those cases, 1)--' produces numbered_list_marker for 1) with correction one (awareness_brackets_numbered)."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [{"index": 0, "text": "No. Well, in those cases, 1)--"}],
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


def test_build_rule_candidates_numbered_list_followed_by_dots(tmp_path: Path) -> None:
    """Transcript 'and 2)...' produces numbered_list_marker for 2) with correction two."""
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
                        "text": "that's 1) necessary, and 2)... and I think this is important.",
                    }
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
    candidates = data.get("candidates", [])
    two_cand = next((c for c in candidates if c.get("span") == "2)"), None)
    assert two_cand is not None, [c.get("span") for c in candidates]
    assert any(co.get("text") == "two" for co in two_cand.get("corrections", []))


def test_build_rule_candidates_numbered_list_followed_by_colon(tmp_path: Path) -> None:
    """Transcript 'section (a) 42):' produces numbered_list_marker for 42) with correction forty two."""
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
                        "text": 'quoting from section (a) 42): "Any person who ordered..."',
                    }
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
    candidates = data.get("candidates", [])
    cand = next((c for c in candidates if c.get("span") == "42)"), None)
    assert cand is not None, [c.get("span") for c in candidates]
    assert any(co.get("text") == "forty two" for co in cand.get("corrections", []))
