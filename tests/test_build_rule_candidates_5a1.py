# Edited by Cursor: split from test_build_rule_candidates for lintok.
"""Integration tests: build_rule_candidates (part 5 first half)."""

import json
from pathlib import Path

import pytest

from tests.test_build_rule_candidates_common import run_build_rule_candidates

pytestmark = pytest.mark.slow


def test_build_rule_candidates_website_dot(tmp_path: Path) -> None:
    """Transcript with [befairDOTorg,] produces website_dot candidate with 'befair dot org,'."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "visit [befairDOTorg,] for more."},
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
    path = out_dir / "website_dot_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    cand = next(
        (c for c in candidates if c.get("span") == "[befairDOTorg,]"),
        None,
    )
    assert cand is not None, [c.get("span") for c in candidates]
    texts = [
        co.get("text") for co in cand.get("corrections", []) if "text" in (co or {})
    ]
    assert "befair dot org," in texts, texts


def test_build_rule_candidates_bracket_sentence_unwrap(tmp_path: Path) -> None:
    """Transcript with (which may itself be true) produces bracket_sentence_unwrap with inner text."""
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
                        "text": "visual proof of a product claim (which may itself be true) when the test is a sham.",
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
    path = out_dir / "bracket_sentence_unwrap_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    cand = next(
        (c for c in candidates if c.get("span") == "(which may itself be true)"),
        None,
    )
    assert cand is not None, [c.get("span") for c in candidates]
    texts = [
        co.get("text") for co in cand.get("corrections", []) if "text" in (co or {})
    ]
    assert "which may itself be true" in texts, texts


def test_build_rule_candidates_name_pattern_di(tmp_path: Path) -> None:
    """Transcript with DiBona produces name_pattern_di candidate (identity)."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "Mr. DiBona was deferential."},
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
    path = out_dir / "name_pattern_di_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    cand = next((c for c in candidates if c.get("span") == "DiBona"), None)
    assert cand is not None, [c.get("span") for c in candidates]
    texts = [
        co.get("text") for co in cand.get("corrections", []) if "text" in (co or {})
    ]
    assert "DiBona" in texts, texts
