# Edited by Cursor: extracted from build_rule_candidates for lintok.
"""Write rule candidate JSON files (unified schema)."""

import json
from pathlib import Path

from scripts.build_rule_candidates_registry import (
    ALL_RULE_IDS,
    RULE_LABELS,
    RULE_NORMALIZER,
)


def write_rule_candidate_files(
    out_dir: Path,
    groups: dict,
    typo_corrections: dict,
    latin_corrections_map: dict,
) -> None:
    """Build and write per-rule JSON files from groups and correction maps."""
    for rule_id in ALL_RULE_IDS:
        candidates: list[dict] = []
        for (rid, span), occurrences_raw in groups.items():
            if rid != rule_id:
                continue
            if rule_id == "typo_levenshtein":
                correction_set = {
                    typo_corrections[(p, ln, si)]
                    for (p, ln, si) in occurrences_raw
                    if (p, ln, si) in typo_corrections
                }
                corrections = [{"text": t} for t in sorted(correction_set)]
            elif rule_id == "latin_extended" and span in latin_corrections_map:
                corrections = list(latin_corrections_map[span])
            else:
                normalizer = RULE_NORMALIZER.get(rule_id)
                raw = normalizer(span) if normalizer else [span]
                if raw and isinstance(raw[0], dict) and "text" in raw[0]:
                    corrections = list(raw)
                else:
                    corrections = [{"text": t} for t in raw]
            occurrences = [
                {"path": p, "line_num": ln, "start_index": si}
                for p, ln, si in occurrences_raw
            ]
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
            "rule_id": rule_id,
            "rule_name": RULE_LABELS.get(rule_id, rule_id),
            "candidates": candidates,
            "filter_note": None,
        }
        out_path = out_dir / f"{rule_id}_candidates.json"
        out_path.write_text(json.dumps(payload, indent=2))
