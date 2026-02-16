# Edited by Cursor: split from test_collect_asr_artifacts (lintok; no new exclusions).
"""Tests for collect_asr_artifacts: script run, citation, ordinals, vote_tally, roman."""

import json
import subprocess
import sys
from pathlib import Path

from scripts.collect_asr_artifacts import collect_artifacts
from tests.test_collect_asr_artifacts_helpers import (
    _minimal_transcript,
    _run_script,
)


class TestCollectAsrArtifactsCategories1a:
    """Script run, no_dot_citation, need_verification, track_paths, ordinals, vote_tally, roman."""

    def test_acronyms_currency_historical_year_no_context_unspoken_header(
        self, tmp_path: Path
    ) -> None:
        fixture = (
            "We have BIA and USC. Cost is $40,000. In 1215 the Magna Carta. "
            "No. I disagree. Mr. McCoy. ORAL ARGUMENT OF JEFFREY W. McCOY"
        )
        transcript = _minimal_transcript([{"text": fixture, "index": 0}])
        (tmp_path / "2022" / "21-1164").mkdir(parents=True)
        (tmp_path / "2022" / "21-1164" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = _run_script(tmp_path)
        assert "acronyms" in report and "BIA" in report["acronyms"]
        assert "currency" in report and "$40000" in report["currency"]
        assert "historical_years" in report and "1215" in report["historical_years"]
        assert "no_dot_context" in report and "I" in report["no_dot_context"]
        assert (
            "unspoken_headers" in report
            and "ORAL ARGUMENT OF" in report["unspoken_headers"]
        )

    def test_no_dot_citation_collected(self, tmp_path: Path) -> None:
        fixture = "The opinion of the Court in No. 96-511, Reno versus ACLU."
        transcript = _minimal_transcript([{"text": fixture, "index": 0}])
        (tmp_path / "1996" / "96-511").mkdir(parents=True)
        (tmp_path / "1996" / "96-511" / "opinion.json").write_text(
            json.dumps(transcript)
        )
        report = _run_script(tmp_path)
        assert "no_dot_citation" in report and "No. 96-511" in report["no_dot_citation"]

    def test_need_verification_lists_rules_and_example_paths(
        self, tmp_path: Path
    ) -> None:
        transcript = _minimal_transcript(
            [{"text": "The opinion in No. 96-511, Reno v. ACLU.", "index": 0}]
        )
        (tmp_path / "1996" / "96-511").mkdir(parents=True)
        (tmp_path / "1996" / "96-511" / "opinion.json").write_text(
            json.dumps(transcript)
        )
        status = {"no_number": 0, "case_ids": 4}
        (tmp_path / "status.json").write_text(json.dumps(status))
        result = subprocess.run(  # noqa: S603
            [
                sys.executable,
                "scripts/collect_asr_artifacts.py",
                str(tmp_path),
                "--need-verification",
                "--min-instances",
                "2",
                "--status",
                str(tmp_path / "status.json"),
                "-o",
                str(tmp_path / "report.json"),
            ],
            capture_output=True,
            text=True,
            check=False,
            cwd=Path(__file__).resolve().parents[1],
        )
        assert result.returncode == 0
        assert "No." in result.stderr and "number" in result.stderr
        assert "96-511" in result.stderr or "1996" in result.stderr

    def test_collect_artifacts_track_paths_returns_category_to_paths(
        self, tmp_path: Path
    ) -> None:
        transcript = _minimal_transcript([{"text": "No. 96-511.", "index": 0}])
        (tmp_path / "a" / "b").mkdir(parents=True)
        (tmp_path / "a" / "b" / "t.json").write_text(json.dumps(transcript))
        result = collect_artifacts(tmp_path, track_paths=True)
        assert isinstance(result, tuple)
        report, category_to_paths = result
        assert "no_dot_citation" in report and "No. 96-511" in report["no_dot_citation"]
        assert "no_dot_citation" in category_to_paths
        assert "a/b/t.json" in category_to_paths["no_dot_citation"]

    def test_ordinal_2nd_22nd_matched(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript(
            [{"text": "On the 2nd and 22nd day.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert (
            "ordinals" in report
            and "2nd" in report["ordinals"]
            and "22nd" in report["ordinals"]
        )

    def test_vote_tally_separate_from_case_ids(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript(
            [{"text": "The vote was 9-0. Case 21-1164.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1164").mkdir(parents=True)
        (tmp_path / "2022" / "21-1164" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert "vote_tally" in report and "9-0" in report["vote_tally"]
        assert "case_ids" in report and "21-1164" in report["case_ids"]
        assert "9-0" not in report["case_ids"]

    def test_roman_numerals_collected(self, tmp_path: Path) -> None:
        transcript = _minimal_transcript(
            [{"text": "Amendment VII and Title IV.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "opinion.json").write_text(json.dumps(transcript))
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert "roman_numerals" in report
        assert "VII" in report["roman_numerals"] and "IV" in report["roman_numerals"]
