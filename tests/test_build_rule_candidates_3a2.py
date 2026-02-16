# Edited by Cursor: split from test_build_rule_candidates for lintok.
"""Integration tests: build_rule_candidates (part 3 first half)."""

import json
from pathlib import Path

import pytest

from tests.test_build_rule_candidates_common import run_build_rule_candidates

pytestmark = pytest.mark.slow


def test_build_rule_candidates_numbered_list_followed_by_paren(tmp_path: Path) -> None:
    """Transcript 'section 67)(c)' produces numbered_list_marker for 67) with correction sixty seven."""
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
                        "text": "The problem was dealt with in section 67)(c), where entities like that were said to be treated.",
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
    cand = next((c for c in candidates if c.get("span") == "67)"), None)
    assert cand is not None, [c.get("span") for c in candidates]
    assert any(co.get("text") == "sixty seven" for co in cand.get("corrections", []))


def test_build_rule_candidates_numbered_list_preceded_by_endash(tmp_path: Path) -> None:
    """Transcript 'page A (26-10).' produces numbered_list_marker for 10) with correction ten (en-dash before 10)."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    # en-dash U+2013 between 26 and 10
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [{"index": 0, "text": "It's on page A (26\u201310)."}],
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
    cand = next((c for c in candidates if c.get("span") == "10)"), None)
    assert cand is not None, [c.get("span") for c in candidates]
    assert any(co.get("text") == "ten" for co in cand.get("corrections", []))


# Edited by Cursor (TDD plan item 10: timestamp non-speech)
def test_build_rule_candidates_non_speech_audio_cut(tmp_path: Path) -> None:
    """Fixture with '(audio abruptly cut 00:35:34-00:35:40)' -> non_speech_brackets includes it with correction ''."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    span_text = "(audio abruptly cut 00:35:34-00:35:40)"
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [{"index": 0, "text": f"Silence {span_text} then resumed."}],
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
    candidates = data.get("candidates", [])
    cand = next((c for c in candidates if c.get("span") == span_text), None)
    assert cand is not None, [c.get("span") for c in candidates]
    texts = [co.get("text") for co in cand.get("corrections", []) if "text" in co]
    assert "" in texts, texts


# Edited by Cursor (TDD plan item 9: leading decimal)
def test_build_rule_candidates_leading_decimal(tmp_path: Path) -> None:
    """Fixture '.06 and .31' -> leading_decimal_candidates with expected spans/corrections."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    fixture = transcripts_dir / "sample" / "oral_argument.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        json.dumps(
            {
                "metadata": {},
                "turns": [{"index": 0, "text": ".06 and .31"}],
            },
            indent=2,
        )
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    run_build_rule_candidates(
        transcripts_dir, out_dir, cwd=Path(__file__).resolve().parents[1]
    )
    path = out_dir / "leading_decimal_candidates.json"
    assert path.exists(), list(out_dir.iterdir())
    data = json.loads(path.read_text())
    candidates = data.get("candidates", [])
    span_06 = next((c for c in candidates if c.get("span") == ".06"), None)
    span_31 = next((c for c in candidates if c.get("span") == ".31"), None)
    assert span_06 is not None and span_31 is not None, [
        c.get("span") for c in candidates
    ]
    texts_06 = [co.get("text") for co in span_06.get("corrections", []) if "text" in co]
    texts_31 = [co.get("text") for co in span_31.get("corrections", []) if "text" in co]
    assert "point oh six" in texts_06, texts_06
    assert "point three one" in texts_31 and "point thirty one" in texts_31, texts_31


# Edited by Cursor (TDD plan item 7: editorial dollar)
