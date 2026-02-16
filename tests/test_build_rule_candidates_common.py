# Edited by Cursor: shared helper for build_rule_candidates integration tests (lintok split).
"""Shared helper for build_rule_candidates integration tests."""

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow


def run_build_rule_candidates(
    transcripts_dir: Path,
    output_dir: Path,
    cwd: Path | None = None,
) -> None:
    """Run build_rule_candidates CLI; assert exit 0."""
    root = cwd or Path(__file__).resolve().parents[1]
    cmd = [
        sys.executable,
        "-m",
        "scripts.build_rule_candidates",
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
