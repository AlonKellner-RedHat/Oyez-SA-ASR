# Edited by Cursor: split from test_build_rule_candidates for lintok.
"""Integration tests: build_rule_candidates (part 2 first half)."""

import json
from pathlib import Path

import pytest

from tests.test_build_rule_candidates_common import run_build_rule_candidates

pytestmark = pytest.mark.slow


def test_build_rule_candidates_dash_ellipsis_output(tmp_path: Path) -> None:
    """Fixture with ellipsis …; assert dash rule emits it and correction is -."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "word\u2026word"},
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
    candidates = data.get("candidates", [])
    ellipsis_cand = next((c for c in candidates if "\u2026" in c.get("span", "")), None)
    assert ellipsis_cand is not None, [c.get("span") for c in candidates]
    texts = [
        co.get("text") for co in ellipsis_cand.get("corrections", []) if "text" in co
    ]
    assert texts == ["-"], texts


def test_build_rule_candidates_ordinals_output(tmp_path: Path) -> None:
    """Fixture with 37th and 3rd; assert ordinals_candidates.json with thirty seventh, third."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "37th Congress and 3rd Session."},
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
    path = out_dir / "ordinals_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    assert data.get("rule_id") == "ordinals"
    candidates = data.get("candidates", [])
    thirty7 = next((c for c in candidates if c.get("span") == "37th"), None)
    third = next((c for c in candidates if c.get("span") == "3rd"), None)
    assert thirty7 is not None, [c.get("span") for c in candidates]
    assert third is not None, [c.get("span") for c in candidates]
    t7_texts = [co.get("text") for co in thirty7.get("corrections", []) if "text" in co]
    t3_texts = [co.get("text") for co in third.get("corrections", []) if "text" in co]
    assert t7_texts == ["thirty seventh"], t7_texts
    assert t3_texts == ["third"], t3_texts


def test_build_rule_candidates_curly_single_quotes_output(tmp_path: Path) -> None:
    """Fixture with curly single quotes; assert open/close_double_quote contain U+2018/U+2019."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "\u2018I object.\u2019"},
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
    open_data = json.loads((out_dir / "open_double_quote_candidates.json").read_text())
    close_data = json.loads(
        (out_dir / "close_double_quote_candidates.json").read_text()
    )
    open_spans = [c.get("span") for c in open_data.get("candidates", [])]
    close_spans = [c.get("span") for c in close_data.get("candidates", [])]
    assert "\u2018" in open_spans, open_spans
    assert "\u2019" in close_spans, close_spans
