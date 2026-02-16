# Edited by Cursor: split from test_build_awareness_candidates (lintok; no new exclusions).
"""Integration tests: build_awareness_candidates output schema and non-dictionary."""

import json
from pathlib import Path

import pytest

from tests.test_build_awareness_candidates_helpers import (
    _run_build_awareness_candidates,
)

pytestmark = pytest.mark.slow


def test_build_awareness_candidates_output_has_unified_schema_no_corrections(
    tmp_path: Path,
) -> None:
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
                        "text": "Calf\u00e9 and McCloud [cough] H1N1 virus\u2026",
                    },
                ],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _run_build_awareness_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    out_files = list(out_dir.iterdir())
    assert out_files
    mixed_path = out_dir / "awareness_mixed_case_candidates.json"
    assert mixed_path.exists()
    data = json.loads(mixed_path.read_text())
    assert data.get("rule_id") == "awareness_mixed_case"
    assert "rule_name" in data
    candidates = data.get("candidates", [])
    assert candidates
    c = candidates[0]
    assert "span" in c
    assert c.get("corrections") == []
    assert "occurrences" in c
    for occ in c["occurrences"]:
        assert "path" in occ and "line_num" in occ and "start_index" in occ


def test_build_awareness_candidates_non_dictionary(tmp_path: Path) -> None:
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
                        "text": "the court befair supremecourt the18th June22nd",
                    }
                ],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _run_build_awareness_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "awareness_non_dictionary_candidates.json"
    assert path.exists()
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    spans = [c.get("span") for c in candidates]
    assert "befair" in spans and "supremecourt" in spans
    assert "the" not in spans and "court" not in spans
    assert "the18th" in spans
    cand_18 = next(c for c in candidates if c.get("span") == "the18th")
    assert cand_18.get("corrections") == []


def test_build_awareness_candidates_non_dictionary_punctuation_and_4plus(
    tmp_path: Path,
) -> None:
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
                        "text": "action, Right. second-guess days? don't e.g. xyzqq",
                    }
                ],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _run_build_awareness_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "awareness_non_dictionary_candidates.json"
    assert path.exists()
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    spans = [c.get("span") for c in candidates]
    assert "action," not in spans and "Right." not in spans
    assert "second-guess" not in spans and "days?" not in spans and "e.g." not in spans
    assert "xyzqq" in spans


def test_build_awareness_candidates_non_dictionary_no_split_correction(
    tmp_path: Path,
) -> None:
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps({"metadata": {}, "turns": [{"index": 0, "text": "hedid"}]}, indent=2)
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _run_build_awareness_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    data = json.loads(
        (out_dir / "awareness_non_dictionary_candidates.json").read_text()
    )
    candidates = data.get("candidates", [])
    cand = next((c for c in candidates if c.get("span") == "hedid"), None)
    assert cand is not None
    assert cand.get("corrections") == []


def test_build_awareness_candidates_angle_brackets(tmp_path: Path) -> None:
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {"metadata": {}, "turns": [{"index": 0, "text": "See <foo> here."}]},
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _run_build_awareness_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "awareness_brackets_angle_candidates.json"
    assert path.exists()
    data = json.loads(path.read_text())
    assert data.get("rule_id") == "awareness_brackets_angle"
    candidates = data.get("candidates", [])
    spans = [c.get("span") for c in candidates]
    assert "<foo>" in spans
