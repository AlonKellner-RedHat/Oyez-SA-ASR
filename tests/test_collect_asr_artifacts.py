# Edited by Cursor
"""Tests for scripts/collect_asr_artifacts.py."""

import json
import subprocess
import sys
from pathlib import Path

from scripts.collect_asr_artifacts import collect_artifacts


def _run_script(
    transcripts_dir: Path,
    output_path: Path | None = None,
    need_verification: bool = False,
    status_path: Path | None = None,
) -> dict:
    """Run collect_asr_artifacts.py on transcripts_dir; return report dict."""
    cmd = [sys.executable, "scripts/collect_asr_artifacts.py", str(transcripts_dir)]
    if output_path is not None:
        cmd.extend(["-o", str(output_path)])
    if need_verification:
        cmd.append("--need-verification")
    if status_path is not None:
        cmd.extend(["--status", str(status_path)])
    result = subprocess.run(  # noqa: S603
        cmd,
        capture_output=True,
        text=True,
        check=False,
        cwd=Path(__file__).resolve().parents[1],
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    if output_path is not None and output_path.exists():
        return json.loads(output_path.read_text())
    return json.loads(result.stdout)


def _minimal_transcript(turns: list[dict]) -> dict:
    """Minimal processed transcript structure."""
    return {
        "term": "2022",
        "case_docket": "21-1164",
        "type": "oral_argument",
        "turns": turns,
        "metadata": {"speakers": []},
    }


class TestCollectAsrArtifactsNewCategories:
    """Tests for new artifact categories (acronyms, currency, etc.)."""

    def test_acronyms_currency_historical_year_no_context_unspoken_header(
        self, tmp_path: Path
    ) -> None:
        """One turn with acronyms, currency, historical year, No. next token, unspoken header."""
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
        assert "acronyms" in report
        assert "BIA" in report["acronyms"]
        assert "USC" in report["acronyms"]
        assert "currency" in report
        assert "$40000" in report["currency"]
        assert "historical_years" in report
        assert "1215" in report["historical_years"]
        assert "no_dot_context" in report
        assert "I" in report["no_dot_context"]
        assert "unspoken_headers" in report
        assert "ORAL ARGUMENT OF" in report["unspoken_headers"]

    def test_no_dot_citation_collected(self, tmp_path: Path) -> None:
        """No. 96-511 style (citation) is collected in no_dot_citation."""
        fixture = "The opinion of the Court in No. 96-511, Reno versus ACLU."
        transcript = _minimal_transcript([{"text": fixture, "index": 0}])
        (tmp_path / "1996" / "96-511").mkdir(parents=True)
        (tmp_path / "1996" / "96-511" / "opinion.json").write_text(
            json.dumps(transcript)
        )
        report = _run_script(tmp_path)
        assert "no_dot_citation" in report
        assert "No. 96-511" in report["no_dot_citation"]

    def test_need_verification_lists_rules_and_example_paths(
        self, tmp_path: Path
    ) -> None:
        """--need-verification lists rules with < 2 verified and example transcripts."""
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
        assert result.returncode == 0, (result.stdout, result.stderr)
        assert "No." in result.stderr and "number" in result.stderr
        assert "96-511" in result.stderr or "1996" in result.stderr

    def test_collect_artifacts_track_paths_returns_category_to_paths(
        self, tmp_path: Path
    ) -> None:
        """collect_artifacts(track_paths=True) returns (report, category_to_paths)."""
        transcript = _minimal_transcript([{"text": "No. 96-511.", "index": 0}])
        (tmp_path / "a" / "b").mkdir(parents=True)
        (tmp_path / "a" / "b" / "t.json").write_text(json.dumps(transcript))
        result = collect_artifacts(tmp_path, track_paths=True)
        assert isinstance(result, tuple)
        report, category_to_paths = result
        assert "no_dot_citation" in report
        assert "No. 96-511" in report["no_dot_citation"]
        assert "no_dot_citation" in category_to_paths
        assert "a/b/t.json" in category_to_paths["no_dot_citation"]

    def test_ordinal_2nd_22nd_matched(self, tmp_path: Path) -> None:
        """Ordinal 2nd and 22nd matched (regex suffix nd)."""
        transcript = _minimal_transcript(
            [{"text": "On the 2nd and 22nd day.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert "ordinals" in report
        assert "2nd" in report["ordinals"]
        assert "22nd" in report["ordinals"]

    def test_vote_tally_separate_from_case_ids(self, tmp_path: Path) -> None:
        """9-0 goes to vote_tally; 21-1164 goes to case_ids."""
        transcript = _minimal_transcript(
            [{"text": "The vote was 9-0. Case 21-1164.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1164").mkdir(parents=True)
        (tmp_path / "2022" / "21-1164" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        result = collect_artifacts(tmp_path)
        assert isinstance(result, dict)
        report = result
        assert "vote_tally" in report
        assert "9-0" in report["vote_tally"]
        assert "case_ids" in report
        assert "21-1164" in report["case_ids"]
        assert "9-0" not in report["case_ids"]

    def test_roman_numerals_collected(self, tmp_path: Path) -> None:
        """Amendment VII yields VII in roman_numerals."""
        transcript = _minimal_transcript(
            [{"text": "Amendment VII and Title IV.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "opinion.json").write_text(json.dumps(transcript))
        result = collect_artifacts(tmp_path)
        assert isinstance(result, dict)
        report = result
        assert "roman_numerals" in report
        assert "VII" in report["roman_numerals"]
        assert "IV" in report["roman_numerals"]

    def test_percentages_collected(self, tmp_path: Path) -> None:
        """50% and 25 percent appear in percentages."""
        transcript = _minimal_transcript(
            [{"text": "About 50% and 25 percent.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        result = collect_artifacts(tmp_path)
        assert isinstance(result, dict)
        report = result
        assert "percentages" in report
        assert "50%" in report["percentages"]
        assert "25%" in report["percentages"]

    def test_decades_collected(self, tmp_path: Path) -> None:
        """1980s appears in decades."""
        transcript = _minimal_transcript(
            [{"text": "In the 1980s and 1930s.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "opinion.json").write_text(json.dumps(transcript))
        result = collect_artifacts(tmp_path)
        assert isinstance(result, dict)
        report = result
        assert "decades" in report
        assert "1980s" in report["decades"]
        assert "1930s" in report["decades"]

    def test_et_al_in_abbreviations(self, tmp_path: Path) -> None:
        """Et al. appears in abbreviations."""
        transcript = _minimal_transcript(
            [{"text": "Smith et al. and Jones et al.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        result = collect_artifacts(tmp_path)
        assert isinstance(result, dict)
        report = result
        assert "abbreviations" in report
        assert "et al." in report["abbreviations"]

    def test_ordinals_word_collected(self, tmp_path: Path) -> None:
        """Fifth Circuit yields Fifth in ordinals_word."""
        transcript = _minimal_transcript(
            [{"text": "Fifth Circuit and Seventh Amendment.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "opinion.json").write_text(json.dumps(transcript))
        result = collect_artifacts(tmp_path)
        assert isinstance(result, dict)
        report = result
        assert "ordinals_word" in report
        assert "Fifth" in report["ordinals_word"]
        assert "Seventh" in report["ordinals_word"]

    def test_statute_citation_collected(self, tmp_path: Path) -> None:
        """21 U.S.C. and Title 18 appear in statute_citation."""
        transcript = _minimal_transcript(
            [{"text": "Under 21 U.S.C. and Title 18.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        result = collect_artifacts(tmp_path)
        assert isinstance(result, dict)
        report = result
        assert "statute_citation" in report
        assert any("21" in k and "U" in k for k in report["statute_citation"])
        assert any("Title 18" in k for k in report["statute_citation"])

    def test_awareness_non_ascii_or_symbols(self, tmp_path: Path) -> None:
        """Non-ASCII (en dash) yields awareness_non_ascii or awareness_symbols."""
        transcript = _minimal_transcript([{"text": "Range 10\u201312.", "index": 0}])
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        result = collect_artifacts(tmp_path)
        assert isinstance(result, dict)
        report = result
        assert "awareness_non_ascii" in report or "awareness_symbols" in report
        has_awareness = bool(report.get("awareness_non_ascii")) or bool(
            report.get("awareness_symbols")
        )
        assert has_awareness

    def test_awareness_mixed_case_collected(self, tmp_path: Path) -> None:
        """McCloud appears in awareness_mixed_case."""
        transcript = _minimal_transcript(
            [{"text": "Mr. McCloud and Ms. O'Brien.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        result = collect_artifacts(tmp_path)
        assert isinstance(result, dict)
        report = result
        assert "awareness_mixed_case" in report
        assert "McCloud" in report["awareness_mixed_case"]

    def test_awareness_brackets_collected(self, tmp_path: Path) -> None:
        """[cough], (inaudible), 1), {x} yield awareness_brackets_*."""
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
        result = collect_artifacts(tmp_path)
        assert isinstance(result, dict)
        report = result
        assert "awareness_brackets_square" in report
        assert "awareness_brackets_parens" in report
        assert "awareness_brackets_numbered" in report
        assert "awareness_brackets_curly" in report
        assert "[cough]" in report["awareness_brackets_square"]
        assert "(inaudible)" in report["awareness_brackets_parens"]
        assert "1)" in report["awareness_brackets_numbered"]
        assert "2)" in report["awareness_brackets_numbered"]
        assert "{note}" in report["awareness_brackets_curly"]

    def test_awareness_leading_decimal_collected(self, tmp_path: Path) -> None:
        """Leading decimal .66 yields awareness_leading_decimal (point six six)."""
        transcript = _minimal_transcript(
            [{"text": "The ratio was .66 or point six six.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        result = collect_artifacts(tmp_path)
        assert isinstance(result, dict)
        report = result
        assert "awareness_leading_decimal" in report
        assert ".66" in report["awareness_leading_decimal"]

    def test_leading_decimal_collected(self, tmp_path: Path) -> None:
        """Leading decimal .66 yields leading_decimal (first-class category)."""
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
        assert ".66" in report["leading_decimal"]
        assert ".5" in report["leading_decimal"]

    def test_non_speech_brackets_collected(self, tmp_path: Path) -> None:
        """(Inaudible) and [Laughter] yield non_speech_brackets."""
        transcript = _minimal_transcript(
            [
                {
                    "text": "Then (Inaudible) and [Laughter] in the room.",
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
        assert "non_speech_brackets" in report
        assert "(Inaudible)" in report["non_speech_brackets"]
        assert "[Laughter]" in report["non_speech_brackets"]

    def test_editorial_square_bracket_collected(self, tmp_path: Path) -> None:
        """[= Mr.] yields editorial_square_bracket."""
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
        """2010-2015 (en dash) yields dash_range."""
        transcript = _minimal_transcript(
            [{"text": "From 2010\u20132015 the rate increased.", "index": 0}]
        )
        (tmp_path / "2022" / "21-1").mkdir(parents=True)
        (tmp_path / "2022" / "21-1" / "oral_argument.json").write_text(
            json.dumps(transcript)
        )
        report = collect_artifacts(tmp_path)
        assert isinstance(report, dict)
        assert "dash_range" in report
        assert "2010\u20132015" in report["dash_range"]

    def test_ellipsis_collected(self, tmp_path: Path) -> None:
        """Literal ... and U+2026 yield ellipsis."""
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
        assert "..." in report["ellipsis"]
        assert "U+2026" in report["ellipsis"]

    def test_structural_bracket_collected(self, tmp_path: Path) -> None:
        """(a), (b), (1), (2) yield structural_bracket."""
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
        assert "(a)" in report["structural_bracket"]
        assert "(b)" in report["structural_bracket"]
        assert "(1)" in report["structural_bracket"]
        assert "(2)" in report["structural_bracket"]

    def test_numbered_list_marker_collected(self, tmp_path: Path) -> None:
        """1) and 2) yield numbered_list_marker."""
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
        assert "1)" in report["numbered_list_marker"]
        assert "2)" in report["numbered_list_marker"]
