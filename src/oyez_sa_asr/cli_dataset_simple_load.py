# Edited by Claude
"""Loading and filtering helpers for dataset simple command."""

import json
from pathlib import Path
from typing import Any

from rich.console import Console

console = Console(force_terminal=True)


def get_flex_terms(flex_dir: Path) -> list[str]:
    """Get terms from flex dataset index."""
    index_file = flex_dir / "index.json"
    if not index_file.exists():
        return []
    try:
        with index_file.open() as f:
            return json.load(f).get("terms", [])
    except (json.JSONDecodeError, OSError):
        return []


def load_and_filter_utterances(
    pq: Any, utterances_pq: Path, terms: list[str] | None, *, include_invalid: bool
) -> list[dict[str, Any]]:
    """Load utterances and filter by term and validity."""
    console.print("Reading utterances...")
    all_utterances = pq.read_table(utterances_pq).to_pylist()

    # Filter by term
    if terms:
        term_set = set(terms)
        utterances = [u for u in all_utterances if u.get("term") in term_set]
        console.print(
            f"  Found {len(utterances)} utterances (filtered from {len(all_utterances)})"
        )
    else:
        utterances = all_utterances
        console.print(f"  Found {len(utterances)} utterances")

    # Filter by validity (uses pre-computed 'valid' field from flex dataset)
    if not include_invalid:
        valid_utterances = [u for u in utterances if u.get("valid", True)]
        invalid_count = len(utterances) - len(valid_utterances)
        if invalid_count > 0:
            # Count reasons
            reasons: dict[str, int] = {}
            for u in utterances:
                if not u.get("valid", True):
                    reason = u.get("invalid_reason", "unknown") or "unknown"
                    reasons[reason.split(":")[0]] = (
                        reasons.get(reason.split(":")[0], 0) + 1
                    )
            console.print(f"  Filtered {invalid_count} invalid utterances:")
            for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
                console.print(f"    [yellow]{reason}:[/yellow] {count}")
        utterances = valid_utterances

    return utterances


def build_audio_paths(
    flex_dir: Path, pq: Any, audio_dir: Path, terms: list[str] | None = None
) -> dict[tuple[str, str], Path]:
    """Build audio path lookup from recordings."""
    audio_paths: dict[tuple[str, str], Path] = {}
    recordings_pq = flex_dir / "data" / "recordings.parquet"
    if not recordings_pq.exists():
        return audio_paths

    term_set = set(terms) if terms else None
    for rec in pq.read_table(recordings_pq).to_pylist():
        if term_set and rec["term"] not in term_set:
            continue
        key = (rec["term"], rec["docket"])
        path = audio_dir / rec["audio_path"]
        if path.exists():
            audio_paths[key] = path
    return audio_paths
