# Edited by Cursor: split from test_build_rule_candidates for lintok.
"""Integration tests: build_rule_candidates (part 3 second half)."""

import json
from pathlib import Path

import pytest

from tests.test_build_rule_candidates_common import run_build_rule_candidates

pytestmark = pytest.mark.slow


def test_build_rule_candidates_known_names_dupont(tmp_path: Path) -> None:
    """Transcript containing DuPoint produces known_names candidate (identity)."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [{"index": 0, "text": "DuPoint and DuPage County."}],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    run_build_rule_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "known_names_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    spans = [c.get("span") for c in candidates]
    assert "DuPoint" in spans, spans
    assert "DuPage" in spans, spans


def test_build_rule_candidates_all_caps_accept(tmp_path: Path) -> None:
    """Transcript containing CERCLA produces all_caps_accept candidate (identity)."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [{"index": 0, "text": "Under CERCLA that is preempted."}],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    run_build_rule_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "all_caps_accept_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    cand = next((c for c in candidates if c.get("span") == "CERCLA"), None)
    assert cand is not None, [c.get("span") for c in candidates]
    assert cand.get("corrections") == [{"text": "CERCLA"}]


# Plan item 7: half symbol ½
def test_build_rule_candidates_half_number(tmp_path: Path) -> None:
    """Fixture 'below to 12½%' yields half_number candidate with correction twelve and a half percent."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [{"index": 0, "text": "below to 12½%."}],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    run_build_rule_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "half_number_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    cand = next((c for c in candidates if "½" in (c.get("span") or "")), None)
    assert cand is not None, [c.get("span") for c in candidates]
    assert any(
        "twelve and a half percent" in (co.get("text") or "")
        for co in cand.get("corrections", [])
    ), cand.get("corrections")


def test_build_rule_candidates_fraction(tmp_path: Path) -> None:
    """Transcript with 1/3 or 2/5 or ½ or ¾ produces fraction candidate with expected corrections."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [
                    {"index": 0, "text": "from 1/3 up to ½ and ¾ of a gram, take 2/5."}
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
    path = out_dir / "fraction_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    spans = [c.get("span") for c in candidates]
    assert "1/3" in spans, spans
    assert "2/5" in spans, spans
    assert "¾" in spans, spans
    cand_three_quarters = next(c for c in candidates if c.get("span") == "¾")
    assert any(
        "three fourths" in (co.get("text") or "")
        or "three quarters" in (co.get("text") or "")
        for co in cand_three_quarters.get("corrections", [])
    ), cand_three_quarters.get("corrections")
    cand_13 = next(c for c in candidates if c.get("span") == "1/3")
    assert any(
        "one third" in (co.get("text") or "") for co in cand_13.get("corrections", [])
    )
    cand_25 = next(c for c in candidates if c.get("span") == "2/5")
    assert any(
        "two fifths" in (co.get("text") or "") for co in cand_25.get("corrections", [])
    )
