# Edited by Cursor: split from test_build_rule_candidates for lintok.
"""Integration tests: build_rule_candidates (part 2 second half)."""

import json
from pathlib import Path

import pytest

from tests.test_build_rule_candidates_common import run_build_rule_candidates

pytestmark = pytest.mark.slow


def test_build_rule_candidates_laughs_output(tmp_path: Path) -> None:
    """Fixture with (Laughs); assert non_speech_brackets has correction [""]."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "Then (Laughs) and we continued."},
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
    laughs_cand = next(
        (c for c in data.get("candidates", []) if "Laughs" in c.get("span", "")),
        None,
    )
    assert laughs_cand is not None
    texts = [
        co.get("text") for co in laughs_cand.get("corrections", []) if "text" in co
    ]
    assert texts == [""], texts


def test_build_rule_candidates_dash_dots_output(tmp_path: Path) -> None:
    """Fixture with ...; assert dash_candidates.json has span ... and correction -."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "word...word"},
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
    dots_cand = next(
        (c for c in data.get("candidates", []) if c.get("span") == "..."), None
    )
    assert dots_cand is not None, [c.get("span") for c in data.get("candidates", [])]
    texts = [co.get("text") for co in dots_cand.get("corrections", []) if "text" in co]
    assert texts == ["-"], texts


def test_build_rule_candidates_decades_1860s_2010s_output(tmp_path: Path) -> None:
    """Fixture with 1860s and 2010s; assert decades_candidates.json has eighteen sixties, twenty tens."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "1860s and 2010s."},
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
    path = out_dir / "decades_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    c1860 = next((c for c in candidates if c.get("span") == "1860s"), None)
    c2010 = next((c for c in candidates if c.get("span") == "2010s"), None)
    assert c1860 is not None, [c.get("span") for c in candidates]
    assert c2010 is not None, [c.get("span") for c in candidates]
    t1860 = [co.get("text") for co in c1860.get("corrections", []) if "text" in co]
    t2010 = [co.get("text") for co in c2010.get("corrections", []) if "text" in co]
    assert t1860 == ["eighteen sixties"], t1860
    assert t2010 == ["twenty tens"], t2010


# Edited by Cursor (ASR normalization rules expansion)
