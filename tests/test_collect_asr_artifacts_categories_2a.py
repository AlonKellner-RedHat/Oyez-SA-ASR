# Edited by Cursor: split from test_collect_asr_artifacts (lintok; no new exclusions).
"""Tests for collect_asr_artifacts: awareness categories."""

import json
from pathlib import Path

from scripts.collect_asr_artifacts import collect_artifacts
from tests.test_collect_asr_artifacts_helpers import (
    _minimal_transcript,
    _run_script,
)


class TestCollectAsrArtifactsCategories2a:
    """Artifact categories: awareness, brackets, leading_decimal, ellipsis, etc."""

    def test_awareness_non_ascii_or_symbols(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript([{"text": "Range 10\u201312.", "index": 0}])
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert "awareness_non_ascii" in report or "awareness_symbols" in report
        has_awareness = bool(report.get("awareness_non_ascii")) or bool(
            report.get("awareness_symbols")
        )
        assert has_awareness

    def test_awareness_mixed_case_collected(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript(
            [{"text": "Mr. McCloud and Ms. O'Brien.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert "awareness_mixed_case" in report
        assert "McCloud" in report["awareness_mixed_case"]

    def test_awareness_brackets_collected(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript(
            [
                {
                    "text": "Then [cough] he said (inaudible) and 1) first 2) second {note}.",
                    "index": 0,
                }
            ]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert (
            "awareness_brackets_square" in report
            and "[cough]" in report["awareness_brackets_square"]
        )
        assert (
            "awareness_brackets_parens" in report
            and "(inaudible)" in report["awareness_brackets_parens"]
        )
        assert "awareness_brackets_numbered" in report
        assert (
            "1)" in report["awareness_brackets_numbered"]
            and "2)" in report["awareness_brackets_numbered"]
        )
        assert (
            "awareness_brackets_curly" in report
            and "{note}" in report["awareness_brackets_curly"]
        )

    def test_awareness_brackets_angle_collected(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript([{"text": "See <foo> and <bar>.", "index": 0}])
        (tmp_path / "2022" / "21-1164").mkdir(parents=True)
        (tmp_path / "2022" / "21-1164" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = _run_script(tmp_path)
        assert "awareness_brackets_angle" in report
        assert (
            "<foo>" in report["awareness_brackets_angle"]
            and "<bar>" in report["awareness_brackets_angle"]
        )

    def test_awareness_time_like_collected(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript(
            [{"text": "At 12:34 and 00:35:34 and 9:38.5 we saw it.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1164").mkdir(parents=True)
        (tmp_path / "2022" / "21-1164" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = _run_script(tmp_path)
        assert "awareness_time_like" in report
        assert "12:34" in report["awareness_time_like"]
        assert (
            "00:35:34" in report["awareness_time_like"]
            and "9:38.5" in report["awareness_time_like"]
        )

    def test_awareness_leading_decimal_collected(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript(
            [{"text": "The ratio was .66 or point six six.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert "awareness_leading_decimal" in report
        assert ".66" in report["awareness_leading_decimal"]

    def test_leading_decimal_collected(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript(
            [{"text": "The value was .66 and .5.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert "leading_decimal" in report
        assert ".66" in report["leading_decimal"] and ".5" in report["leading_decimal"]
