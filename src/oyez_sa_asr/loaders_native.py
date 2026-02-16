# Edited by Cursor: split from loaders (lintok; no new exclusions).
"""Native Python loaders (load_simple, load_flex, load_raw)."""

from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from oyez_sa_asr._loaders_constants import (
    DEFAULT_FLEX_DIR,
    DEFAULT_RAW_DIR,
    DEFAULT_SIMPLE_DIR,
)


def load_simple(
    split: str = "lt1m",
    data_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Load simple dataset split as raw dicts (legacy)."""
    base = data_dir or DEFAULT_SIMPLE_DIR
    splits = ["lt1m", "lt5m", "lt30m"] if split == "all" else [split]
    utterances: list[dict[str, Any]] = []
    for s in splits:
        split_dir = base / s / "data" / "utterances"
        if not split_dir.exists():
            continue
        for shard in sorted(split_dir.glob("train-*.parquet")):
            table = pq.read_table(shard)
            for row in table.to_pylist():
                row["_split"] = s
                utterances.append(row)
    return utterances


def load_flex(
    data_dir: Path | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load flex dataset metadata. Returns (recordings, utterances)."""
    base = data_dir or DEFAULT_FLEX_DIR
    recordings_pq = base / "data" / "recordings.parquet"
    utterances_pq = base / "data" / "utterances.parquet"
    recordings = (
        pq.read_table(recordings_pq).to_pylist() if recordings_pq.exists() else []
    )
    utterances = (
        pq.read_table(utterances_pq).to_pylist() if utterances_pq.exists() else []
    )
    return recordings, utterances


def load_raw(data_dir: Path | None = None) -> list[dict[str, Any]]:
    """Load raw dataset as item-based rows."""
    import json  # noqa: PLC0415

    base = data_dir or DEFAULT_RAW_DIR
    audio_dir = base / "audio"
    case_index: dict[tuple[str, str], Path] = {}
    for case_path in (base / "cases").glob("*.json"):
        try:
            with case_path.open() as f:
                case_data = json.load(f)
            term = str(case_data.get("term", ""))
            docket = case_data.get("docket_number", "")
            if term and docket:
                case_index[(term, docket)] = case_path
        except (json.JSONDecodeError, OSError):
            pass
    transcript_index: dict[str, Path] = {}
    for t_path in (base / "transcripts").glob("*.json"):
        try:
            with t_path.open() as f:
                t_data = json.load(f)
            for mf in t_data.get("media_file") or []:
                if not mf:
                    continue
                href = mf.get("href", "")
                filename = href.rsplit("/", 1)[-1]
                rec_id = filename.split(".")[0]
                if rec_id:
                    transcript_index[rec_id] = t_path
        except (json.JSONDecodeError, OSError):
            pass
    mp3_files = {p.stem.split(".")[0]: p for p in audio_dir.rglob("*.mp3")}
    ogg_files = {p.stem.split(".")[0]: p for p in audio_dir.rglob("*.ogg")}
    all_rec_ids = set(mp3_files.keys()) | set(ogg_files.keys())
    items: list[dict[str, Any]] = []
    for rec_id in sorted(all_rec_ids):
        mp3_path = mp3_files.get(rec_id)
        ogg_path = ogg_files.get(rec_id)
        primary = mp3_path or ogg_path
        assert primary is not None
        term = primary.parent.parent.name
        docket = primary.parent.name
        items.append(
            {
                "recording_id": rec_id,
                "term": term,
                "docket": docket,
                "audio_path": mp3_path,
                "audio_ogg_path": ogg_path,
                "transcript_path": transcript_index.get(rec_id),
                "case_path": case_index.get((term, docket)),
            }
        )
    return items
