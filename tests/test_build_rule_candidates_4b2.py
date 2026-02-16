# Edited by Cursor: split from test_build_rule_candidates for lintok.
"""Integration tests: build_rule_candidates (part 4 second half)."""

import json
from pathlib import Path

import pytest

from tests.test_build_rule_candidates_common import run_build_rule_candidates

pytestmark = pytest.mark.slow


def test_build_rule_candidates_dual_notation_variants(tmp_path: Path) -> None:
    """Dual notation variants [<X>], <X> [81-523] yield angle content as correction."""
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
                        "text": "The savings statute, [<twenty-three oh five point one five>] is unconstitutional.",
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
    path = out_dir / "dual_notation_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    cand = next(
        (c for c in candidates if "[<" in (c.get("span") or "")),
        None,
    )
    assert cand is not None, [c.get("span") for c in candidates]
    texts = [co.get("text") for co in cand.get("corrections", []) if "text" in co]
    assert any("twenty-three oh five point one five" in t for t in texts), texts


# Plan item 5: special currency
def test_build_rule_candidates_special_currency(tmp_path: Path) -> None:
    """Fixture with '$ 3 billion' and '$ 21 hundred' yields special_currency candidates with both corrections."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "Cost $ 3 billion and $ 21 hundred."},
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
    c_billion = next(
        (c for c in candidates if "3 billion" in (c.get("span") or "")), None
    )
    c_hundred = next(
        (c for c in candidates if "21 hundred" in (c.get("span") or "")), None
    )
    assert c_billion is not None and c_hundred is not None, [
        c.get("span") for c in candidates
    ]
    t_b = [co.get("text") for co in c_billion.get("corrections", []) if "text" in co]
    t_h = [co.get("text") for co in c_hundred.get("corrections", []) if "text" in co]
    assert "three billion dollars" in t_b and "three billion dollar" in t_b, t_b
    assert "twenty one hundred dollars" in t_h and "twenty one hundred dollar" in t_h, (
        t_h
    )


# Plan item 4: time of day
def test_build_rule_candidates_time_of_day(tmp_path: Path) -> None:
    """Fixture 'at 8:40 and 1:00' yields time_of_day_candidates with expected spans and corrections."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [{"index": 0, "text": "At 8:40 and 1:00."}],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    run_build_rule_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "time_of_day_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    c840 = next((c for c in candidates if c.get("span") == "8:40"), None)
    c100 = next((c for c in candidates if c.get("span") == "1:00"), None)
    assert c840 is not None and c100 is not None, [c.get("span") for c in candidates]
    t840 = [co.get("text") for co in c840.get("corrections", []) if "text" in co]
    t100 = [co.get("text") for co in c100.get("corrections", []) if "text" in co]
    assert "eight forty" in t840, t840
    assert "one" in t100 and "one oh oh" in t100, t100


# Plan: bracket acronyms (MPSC), (NRDC)
def test_build_rule_candidates_bracket_acronym(tmp_path: Path) -> None:
    """Transcript with (MPSC) and (NRDC) produces bracket_acronym candidates with letter-by-letter corrections."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "See (MPSC) and (NRDC) for that."},
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
    path = out_dir / "bracket_acronym_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    mpsc_c = next((c for c in candidates if c.get("span") == "(MPSC)"), None)
    nrdc_c = next((c for c in candidates if c.get("span") == "(NRDC)"), None)
    assert mpsc_c is not None and nrdc_c is not None, [
        c.get("span") for c in candidates
    ]
    mpsc_texts = [
        co.get("text") for co in mpsc_c.get("corrections", []) if "text" in (co or {})
    ]
    nrdc_texts = [
        co.get("text") for co in nrdc_c.get("corrections", []) if "text" in (co or {})
    ]
    assert "em pee ess cee" in mpsc_texts, mpsc_texts
    assert "en ar dee cee" in nrdc_texts, nrdc_texts


# Plan: PascalCase accept (CattleAnd, ByteDance)
