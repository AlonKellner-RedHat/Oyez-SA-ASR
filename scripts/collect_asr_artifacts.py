#!/usr/bin/env python3
# Edited by Cursor
"""
Collect potential transcription artifacts for ASR normalization.

Scans processed transcripts and gathers numbers, abbreviations, case IDs,
dates, person titles, and similar tokens that typically need conversion
before training an ASR model (e.g. "Inc." -> "incorporated", "No." -> "number").
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Case/docket: 1-2 digits, hyphen, digits (e.g. 19-1392, 94-1039)
CASE_ID_RE = re.compile(r"\b(\d{1,2}-\d+)\b")
# Four-digit years
YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
# Common abbreviations that may need expansion for ASR
ABBREV_RE = re.compile(
    r"\b(Inc|No|Jr|Sr|Mr|Mrs|Ms|Dr|Gen|Gov|Hon|Sec|Rep|Sen|Prof|St|Vol|Ed|Rev|cf|e\.g|i\.e|etc|vs)\.(?=\s|$|[,\)])",
    re.IGNORECASE,
)
# "versus" or "vs." as standalone
VERSUS_RE = re.compile(r"\b(vs?\.?)\s+(?=[A-Z])", re.IGNORECASE)
# Ordinals: 1st, 2nd, 3rd, 4th, ...
ORDINAL_RE = re.compile(r"\b(\d+)(st|and|rd|th)\b", re.IGNORECASE)
# Section/paragraph symbols and "Section N"
SECTION_RE = re.compile(r"(§|¶|\bSection\s+\d+[\w\(\)\-]*)", re.IGNORECASE)
# Simple numeric date patterns: Month DD, YYYY or DD/MM/YYYY style
MONTH_YEAR_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\b",
    re.IGNORECASE,
)
# Standalone single capital letter (possible initial)
STANDALONE_CAP_RE = re.compile(r"(?<=\s)([A-Z])\.(?=\s|$)")


def _add(counter: Counter[str], key: str, normalize: bool = True) -> None:
    token = key.strip()
    if not token:
        return
    if normalize:
        token = token.replace("  ", " ").strip()
    counter[token] += 1


def collect_from_text(text: str, artifacts: dict[str, Counter[str]]) -> None:
    """Extract artifact candidates from a single turn text."""
    if not text or not isinstance(text, str):
        return
    for m in CASE_ID_RE.finditer(text):
        _add(artifacts["case_ids"], m.group(1))
    for m in YEAR_RE.finditer(text):
        _add(artifacts["years"], m.group(1))
    for m in ABBREV_RE.finditer(text):
        _add(artifacts["abbreviations"], m.group(0))
    for m in VERSUS_RE.finditer(text):
        _add(artifacts["versus"], m.group(1))
    for m in ORDINAL_RE.finditer(text):
        _add(artifacts["ordinals"], m.group(0))
    for m in SECTION_RE.finditer(text):
        _add(artifacts["section_refs"], m.group(1).strip())
    for m in MONTH_YEAR_RE.finditer(text):
        _add(artifacts["dates_month_year"], m.group(0))
    for m in STANDALONE_CAP_RE.finditer(text):
        _add(artifacts["likely_initials"], m.group(0))


def collect_from_speakers(
    speakers: list[dict], artifacts: dict[str, Counter[str]]
) -> None:
    """Extract titles/initials from speaker names (e.g. Jr., Sr., middle initial)."""
    if not speakers:
        return
    for s in speakers:
        name = (s or {}).get("name") if isinstance(s, dict) else None
        if not name or not isinstance(name, str):
            continue
        if ", Jr." in name or " Jr." in name:
            artifacts["abbreviations"]["Jr."] += 1
        if ", Sr." in name or " Sr." in name:
            artifacts["abbreviations"]["Sr."] += 1
        for m in re.finditer(r"\b([A-Z])\.", name):
            _add(artifacts["likely_initials"], m.group(0))


def collect_artifacts(transcripts_dir: Path) -> dict[str, dict[str, int]]:
    """Walk processed transcripts and collect all artifact candidates."""
    artifacts: dict[str, Counter[str]] = defaultdict(Counter)
    for path in sorted(transcripts_dir.rglob("*.json")):
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        for turn in data.get("turns") or []:
            if isinstance(turn, dict):
                collect_from_text(turn.get("text") or "", artifacts)
        speakers = (data.get("metadata") or {}).get("speakers") or []
        collect_from_speakers(speakers, artifacts)
    return {k: dict(v.most_common()) for k, v in sorted(artifacts.items())}


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
    args = parser.parse_args()
    if not args.transcripts_dir.is_dir():
        raise SystemExit(f"Not a directory: {args.transcripts_dir}")
    report = collect_artifacts(args.transcripts_dir)
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
