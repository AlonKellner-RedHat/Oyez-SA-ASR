# Edited by Cursor: shared helpers for test_build_awareness_candidates_* (lintok; no new exclusions).
"""Shared helpers for build_awareness_candidates tests."""

import subprocess
import sys
from pathlib import Path


def _run_build_awareness_candidates(
    transcripts_dir: Path,
    output_dir: Path,
    cwd: Path | None = None,
) -> None:
    root = cwd or Path(__file__).resolve().parents[1]
    cmd = [
        sys.executable,
        "-m",
        "scripts.build_awareness_candidates",
        "-i",
        str(transcripts_dir),
        "-o",
        str(output_dir),
        "--allow-no-enchant",
    ]
    result = subprocess.run(  # noqa: S603
        cmd,
        capture_output=True,
        text=True,
        cwd=root,
        check=False,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
