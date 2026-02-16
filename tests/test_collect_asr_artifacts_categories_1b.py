# Edited by Cursor: split from test_collect_asr_artifacts (lintok; no new exclusions).
"""Tests for collect_asr_artifacts: percentages, decades, abbreviations, statute."""

import json
from pathlib import Path

from scripts.collect_asr_artifacts import collect_artifacts
from tests.test_collect_asr_artifacts_helpers import _minimal_transcript


class TestCollectAsrArtifactsCategories1b:
    """Percentages, decades, et al., ordinals_word, statute_citation."""

    def test_percentages_collected(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript(
            [{"text": "About 50% and 25 percent.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert "percentages" in report
        assert "50%" in report["percentages"] and "25%" in report["percentages"]

    def test_decades_collected(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript(
            [{"text": "In the 1980s and 1930s.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "opinion.json").write_text(json.dumps(transcript))
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert "decades" in report
        assert "1980s" in report["decades"] and "1930s" in report["decades"]

    def test_et_al_in_abbreviations(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript(
            [{"text": "Smith et al. and Jones et al.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert "abbreviations" in report and "et al." in report["abbreviations"]

    def test_ordinals_word_collected(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript(
            [{"text": "Fifth Circuit and Seventh Amendment.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "opinion.json").write_text(json.dumps(transcript))
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert "ordinals_word" in report
        assert (
            "Fifth" in report["ordinals_word"] and "Seventh" in report["ordinals_word"]
        )

    def test_statute_citation_collected(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript(
            [{"text": "Under 21 U.S.C. and Title 18.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert "statute_citation" in report
        assert any("21" in k and "U" in k for k in report["statute_citation"])
        assert any("Title 18" in k for k in report["statute_citation"])
