# Edited by Cursor: shared helpers for test_collect_asr_artifacts_* (lintok; no new exclusions).
"""Shared helpers for collect_asr_artifacts tests."""

import json
import subprocess
import sys
from pathlib import Path


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
