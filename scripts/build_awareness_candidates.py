#!/usr/bin/env python3
# Edited by Cursor (lintok split: helpers + extract + thin main)
"""
Scan transcripts for awareness categories (no normalization rules).

Only detects words (space-delimited tokens). Group by (category, span),
write per-category JSON in unified schema with corrections: [].
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_awareness_extract import _extract_awareness
from scripts.build_awareness_helpers import AWARENESS_LABELS, FILTER_NOTE
from scripts.dictionary_loader import get_english_dictionary, set_allow_no_enchant


def main() -> None:
    """Build awareness candidate JSON files from transcripts (unified schema, no corrections)."""
    parser = argparse.ArgumentParser(
        description="Build awareness candidates from transcripts (no normalization)."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("data/transcripts"),
        help="Transcripts directory (recursive *.json)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("data"),
        help="Output directory for <category>_candidates.json",
    )
    parser.add_argument(
        "--profile",
        type=int,
        default=0,
        metavar="N",
        help="If N>0, process first N transcripts only and print per-category CPU time (then exit without writing).",
    )
    parser.add_argument(
        "--profile-report",
        type=Path,
        default=None,
        metavar="PATH",
        help="When using --profile, write a markdown report to this path (default: docs/awareness_timing_report.md).",
    )
    parser.add_argument(
        "--allow-no-enchant",
        action="store_true",
        help="Allow fallback to word list when enchant (spell checker) is unavailable.",
    )
    args = parser.parse_args()
    set_allow_no_enchant(getattr(args, "allow_no_enchant", False))
    transcripts_dir = args.input
    out_dir = args.output
    if not transcripts_dir.is_dir():
        print(f"Input directory not found: {transcripts_dir}")
        raise SystemExit(1)
    out_dir.mkdir(parents=True, exist_ok=True)

    profile_n = getattr(args, "profile", 0) or 0
    profile_times: defaultdict[str, float] = defaultdict(float)
    paths_list = sorted(transcripts_dir.rglob("*.json"))
    if profile_n > 0:
        paths_list = paths_list[:profile_n]
    dic = get_english_dictionary()

    groups: dict[tuple[str, str], list[tuple[str, int, int, str | None]]] = defaultdict(
        list
    )
    for path in paths_list:
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        try:
            rel = path.relative_to(transcripts_dir)
        except ValueError:
            rel = path
        path_str = str(rel).replace("\\", "/")
        for turn in data.get("turns") or []:
            if not isinstance(turn, dict):
                continue
            text = turn.get("text") or ""
            turn_index = turn.get("index", -1)
            if turn_index < 0:
                continue
            for category_id, start_index, span in _extract_awareness(
                text,
                profile_times=profile_times if profile_n else None,
                dic=dic if profile_n else None,
            ):
                groups[(category_id, span)].append((path_str, turn_index, start_index))

    if profile_n:
        total = sum(profile_times.values())
        sorted_cats = sorted(profile_times.keys(), key=lambda k: -profile_times[k])
        print(
            "Profile (first",
            profile_n,
            "transcripts) — per-category total (extract):",
        )
        for cat in sorted_cats:
            t = profile_times[cat]
            pct = 100 * t / total if total else 0
            print(f"  {cat}: {t:.2f}s ({pct:.1f}%)")
        report_path = getattr(args, "profile_report", None) or Path(
            "docs/awareness_timing_report.md"
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Awareness timing report",
            "",
            f"Per-category CPU time (first {profile_n} transcripts).",
            "",
            "| Rank | Category | Time (s) | % |",
            "| ---:| --- | ---: | ---: |",
        ]
        for rank, cat in enumerate(sorted_cats, 1):
            t = profile_times[cat]
            pct = 100 * t / total if total else 0
            lines.append(f"| {rank} | {cat} | {t:.2f} | {pct:.1f} |")
        report_path.write_text("\n".join(lines) + "\n")
        print(f"Wrote report to {report_path}")
        return

    for category_id, rule_name in AWARENESS_LABELS.items():
        candidates: list[dict] = []
        for (cid, span), occurrences_raw in groups.items():
            if cid != category_id:
                continue
            occurrences = [
                {"path": p, "line_num": ln, "start_index": si}
                for p, ln, si in occurrences_raw
            ]
            corrections: list[dict] = []
            candidates.append(
                {
                    "span": span,
                    "corrections": corrections,
                    "count": len(occurrences),
                    "occurrences": occurrences,
                    "occurrences_truncated": False,
                }
            )
        payload = {
            "rule_id": category_id,
            "rule_name": rule_name,
            "candidates": candidates,
            "filter_note": FILTER_NOTE,
        }
        out_path = out_dir / f"{category_id}_candidates.json"
        out_path.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {len(AWARENESS_LABELS)} awareness candidate files to {out_dir}")


if __name__ == "__main__":
    main()
