# Edited by Cursor: split from test_build_rule_candidates for lintok.
"""Integration tests: build_rule_candidates (part 4 second half)."""

import json
from pathlib import Path

import pytest

from tests.test_build_rule_candidates_common import run_build_rule_candidates

pytestmark = pytest.mark.slow


def test_build_rule_candidates_known_mixed_case(tmp_path: Path) -> None:
    """Transcript containing TikTok produces known_mixed_case_entities candidate (identity)."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [{"index": 0, "text": "Seen on TikTok and YouTube."}],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    run_build_rule_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "known_mixed_case_entities_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    cand = next((c for c in candidates if c.get("span") == "TikTok"), None)
    assert cand is not None, [c.get("span") for c in candidates]
    assert cand.get("corrections") == [{"text": "TikTok"}]


def test_build_rule_candidates_single_digit_valid_word(tmp_path: Path) -> None:
    """Transcript with n4or, 9put, eviden3ce (word list has nor, put, evidence) produces corrections."""
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
                        "text": "act n4or omission when we 9put in eviden3ce",
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
    path = out_dir / "single_digit_valid_word_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    spans = [c.get("span") for c in candidates]
    assert "n4or" in spans, spans
    cand_nor = next(c for c in candidates if c.get("span") == "n4or")
    assert any(co.get("text") == "nor" for co in cand_nor.get("corrections", []))
    cand_put = next(c for c in candidates if c.get("span") == "9put")
    assert any(co.get("text") == "put" for co in cand_put.get("corrections", []))
    cand_ev = next(c for c in candidates if c.get("span") == "eviden3ce")
    assert any(co.get("text") == "evidence" for co in cand_ev.get("corrections", []))


def test_build_rule_candidates_typo_levenshtein(tmp_path: Path) -> None:
    """Transcript with G1eneral in one turn and General in another produces typo_levenshtein with correction General."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "General Motors and General Electric."},
                    {"index": 1, "text": "a case between G1eneral Ferguson."},
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
    path = out_dir / "typo_levenshtein_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    cand = next((c for c in candidates if c.get("span") == "G1eneral"), None)
    assert cand is not None, [c.get("span") for c in candidates]
    texts = [co.get("text") for co in cand.get("corrections", []) if "text" in co]
    assert "General" in texts, texts
