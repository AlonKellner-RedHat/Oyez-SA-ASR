#!/usr/bin/env python3
# Edited by Cursor (lintok split: regex + collect + thin main)
"""
Collect potential transcription artifacts for ASR normalization.

Scans processed transcripts and gathers numbers, abbreviations, case IDs,
dates, person titles, and similar tokens that typically need conversion
before training an ASR model (e.g. "Inc." -> "incorporated", "No." -> "number").
"""

import argparse
import json
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.collect_asr_artifacts_collect import (
    _run_need_verification,
    collect_artifacts,
)


def main() -> None:
    """Parse args, collect artifacts from transcripts, and print or write report."""
    parser = argparse.ArgumentParser(
        description="Collect potential ASR transcription artifacts from processed transcripts."
    )
    parser.add_argument(
        "transcripts_dir",
        type=Path,
        nargs="?",
        default=Path("data/transcripts"),
        help="Root directory of processed transcript JSON files",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write JSON report here; default is stdout",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a short text summary to stderr",
    )
    parser.add_argument(
        "--need-verification",
        action="store_true",
        help="List rules with fewer than --min-instances verified and example transcripts",
    )
    parser.add_argument(
        "--min-instances",
        type=int,
        default=2,
        metavar="N",
        help="Minimum verified instances per rule (default: 2)",
    )
    parser.add_argument(
        "--status",
        type=Path,
        default=Path("data/asr_verification_status.json"),
        help="Path to JSON with current verified count per rule (default: data/asr_verification_status.json)",
    )
    args = parser.parse_args()
    if not args.transcripts_dir.is_dir():
        raise SystemExit(f"Not a directory: {args.transcripts_dir}")
    track_paths = args.need_verification
    result = collect_artifacts(args.transcripts_dir, track_paths=track_paths)
    if track_paths:
        report, category_to_paths = result
        _run_need_verification(
            args.transcripts_dir,
            args.status,
            args.min_instances,
            category_to_paths,
        )
    else:
        report = result
    out = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(out)
    else:
        print(out)
    if args.summary:
        total = sum(len(v) for v in report.values())
        for cat, counts in report.items():
            n = len(counts)
            top = list(counts.keys())[:5]
            print(f"  {cat}: {n} unique", file=sys.stderr)
            print(f"    sample: {top}", file=sys.stderr)
        print(f"  Total unique artifacts: {total}", file=sys.stderr)


if __name__ == "__main__":
    main()
