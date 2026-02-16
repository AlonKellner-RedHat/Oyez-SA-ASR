# Edited by Cursor: split from test_collect_asr_artifacts (lintok; no new exclusions).
"""Tests for collect_asr_artifacts: non_speech, editorial, dash, ellipsis, structural."""

import json
from pathlib import Path

from scripts.collect_asr_artifacts import collect_artifacts
from tests.test_collect_asr_artifacts_helpers import _minimal_transcript


class TestCollectAsrArtifactsCategories2b:
    """Non_speech_brackets, editorial_square_bracket, dash_range, ellipsis, structural, numbered_list."""

    def test_non_speech_brackets_collected(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript(
            [{"text": "Then (Inaudible) and [Laughter] in the room.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert "non_speech_brackets" in report
        assert "(Inaudible)" in report["non_speech_brackets"]
        assert "[Laughter]" in report["non_speech_brackets"]

    def test_editorial_square_bracket_collected(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript(
            [{"text": "The counsel [= Mr.] Smith replied.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert "editorial_square_bracket" in report
        assert "[= Mr.]" in report["editorial_square_bracket"]

    def test_dash_range_collected(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript(
            [{"text": "From 2010\u20132015 the rate increased.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert "dash_range" in report and "2010\u20132015" in report["dash_range"]

    def test_ellipsis_collected(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript(
            [{"text": "Wait ... or \u2026 then stop.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert "ellipsis" in report
        assert "..." in report["ellipsis"] and "U+2026" in report["ellipsis"]

    def test_structural_bracket_collected(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript(
            [{"text": "Points (a) and (b); step (1) or (2).", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert "structural_bracket" in report
        assert (
            "(a)" in report["structural_bracket"]
            and "(b)" in report["structural_bracket"]
        )
        assert (
            "(1)" in report["structural_bracket"]
            and "(2)" in report["structural_bracket"]
        )

    def test_numbered_list_marker_collected(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript(
            [{"text": "First 1) do this; 2) then that.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert "numbered_list_marker" in report
        assert (
            "1)" in report["numbered_list_marker"]
            and "2)" in report["numbered_list_marker"]
        )
