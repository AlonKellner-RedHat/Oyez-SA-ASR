# Edited by Cursor: split from test_build_rule_candidates for lintok.
"""Integration tests: build_rule_candidates (part 5 first half)."""

import json
from pathlib import Path

import pytest

from tests.test_build_rule_candidates_common import run_build_rule_candidates

pytestmark = pytest.mark.slow


def test_build_rule_candidates_mixed_case_accept_6plus(tmp_path: Path) -> None:
    """Transcript with PowerEx produces mixed_case_accept_6plus candidate (identity)."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "Petitioner PowerEx was not a foreign state."},
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
    path = out_dir / "mixed_case_accept_6plus_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    cand = next((c for c in candidates if c.get("span") == "PowerEx"), None)
    assert cand is not None, [c.get("span") for c in candidates]
    texts = [
        co.get("text") for co in cand.get("corrections", []) if "text" in (co or {})
    ]
    assert "PowerEx" in texts, texts


def test_build_rule_candidates_pascal_case_accept(tmp_path: Path) -> None:
    """Transcript with CattleAnd and ByteDance produces pascal_case_accept candidates (identity)."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "CattleAnd and ByteDance here."},
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
    path = out_dir / "pascal_case_accept_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    cattle = next((c for c in candidates if c.get("span") == "CattleAnd"), None)
    byte_ = next((c for c in candidates if c.get("span") == "ByteDance"), None)
    assert cattle is not None and byte_ is not None, [c.get("span") for c in candidates]
    cattle_texts = [
        co.get("text")
        for co in (cattle.get("corrections") or [])
        if "text" in (co or {})
    ]
    byte_texts = [
        co.get("text")
        for co in (byte_.get("corrections") or [])
        if "text" in (co or {})
    ]
    assert "CattleAnd" in cattle_texts, cattle_texts
    assert "ByteDance" in byte_texts, byte_texts


# Plan: currency [$] N raw number
def test_build_rule_candidates_special_currency_raw(tmp_path: Path) -> None:
    """Transcript with [$] 43,000 and [$] 86,000 produces special_currency candidates with spoken form."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "Costs [$] 43,000 and [$] 86,000."},
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
    path = out_dir / "special_currency_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    c43 = next((c for c in candidates if c.get("span") == "[$] 43,000"), None)
    c86 = next((c for c in candidates if c.get("span") == "[$] 86,000"), None)
    assert c43 is not None and c86 is not None, [c.get("span") for c in candidates]
    texts43 = [
        co.get("text") for co in c43.get("corrections", []) if "text" in (co or {})
    ]
    texts86 = [
        co.get("text") for co in c86.get("corrections", []) if "text" in (co or {})
    ]
    assert any("forty three thousand" in t for t in texts43), texts43
    assert any("eighty six thousand" in t for t in texts86), texts86


# Plan: inline typo word[: correction]
def test_build_rule_candidates_inline_typo(tmp_path: Path) -> None:
    """Transcript with interaconnection[:interconnection] produces inline_typo candidate with correction interconnection."""
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
                        "text": "the rate of interaconnection[:interconnection] from",
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
    path = out_dir / "inline_typo_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    cand = next(
        (
            c
            for c in candidates
            if "interaconnection[:interconnection]" in (c.get("span") or "")
        ),
        None,
    )
    assert cand is not None, [c.get("span") for c in candidates]
    texts = [
        co.get("text") for co in cand.get("corrections", []) if "text" in (co or {})
    ]
    assert "interconnection" in texts, texts


# Plan: short mixed-case acronym (DoD, DiRe)
