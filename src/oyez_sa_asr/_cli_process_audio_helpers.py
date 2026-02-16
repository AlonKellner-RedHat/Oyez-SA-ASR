# Edited by Cursor: split from cli_process_audio (lintok; plan).
"""Helpers for process audio: count/validate/try/process/filter/run_parallel/run_sequential."""

import json
import random
from concurrent.futures import BrokenExecutor, ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from tqdm import tqdm

from .audio_analysis import detect_anomalies
from .audio_source import AudioSource, get_preferred_format, get_source_era
from .audio_utils import get_audio_metadata, load_audio, save_audio
from .memory_utils import set_pdeathsig


def _count_anomalies(output_dir: Path) -> int:
    """Count files with detected anomalies by scanning metadata files."""
    count = 0
    for meta_path in output_dir.rglob("*.metadata.json"):
        try:
            with meta_path.open() as f:
                meta = json.load(f)
            if meta.get("is_anomaly"):
                count += 1
        except (json.JSONDecodeError, OSError):
            pass
    return count


def _validate_flac_files(
    pending: list[AudioSource], output_dir: Path
) -> tuple[int, list[AudioSource]]:
    """Validate that all pending sources have FLAC files after processing."""
    missing_count = 0
    missing_sources = []
    for source in pending:
        flac_path = (
            output_dir / source.term / source.docket / f"{source.recording_id}.flac"
        )
        if not flac_path.exists():
            missing_count += 1
            missing_sources.append(source)
    return missing_count, missing_sources


def _try_process_file(
    audio_path: Path,
    recording_id: str,
    term: str,
    docket: str,
    output_dir: Path,
    bits: int,
    fmt: str,
) -> tuple[bool, str, dict[str, Any]]:
    """Try to process a single audio file. Returns (success, error, metadata)."""
    try:
        out_dir = output_dir / term / docket
        out_dir.mkdir(parents=True, exist_ok=True)

        meta = get_audio_metadata(audio_path)
        meta["source_path"] = str(audio_path)
        meta["source_format"] = fmt
        meta["source_era"] = get_source_era(term)

        samples, sr = load_audio(audio_path)
        anomaly_info = detect_anomalies(samples, sr)
        meta.update(anomaly_info)

        flac_path = out_dir / f"{recording_id}.flac"
        save_audio(samples, sr, flac_path, format="flac", bits_per_sample=bits)

        meta_path = out_dir / f"{recording_id}.metadata.json"
        with meta_path.open("w") as f:
            json.dump(meta, f, indent=2)

        return (True, "", meta)
    except Exception as e:
        return (False, str(e), {})


def _process_recording(
    source: AudioSource, output_dir: Path, bits: int
) -> tuple[bool, str]:
    """Process a recording with era-aware format preference and fallback."""
    preferred, fallback = get_preferred_format(source.term)

    preferred_path = source.mp3_path if preferred == "mp3" else source.ogg_path
    fallback_path = source.ogg_path if preferred == "mp3" else source.mp3_path

    if preferred_path is not None:
        success, err, _ = _try_process_file(
            preferred_path,
            source.recording_id,
            source.term,
            source.docket,
            output_dir,
            bits,
            preferred,
        )
        if success:
            return (True, "")

    if fallback_path is not None:
        success, err, _ = _try_process_file(
            fallback_path,
            source.recording_id,
            source.term,
            source.docket,
            output_dir,
            bits,
            fallback,
        )
        if success:
            return (True, "")
        return (False, err)

    return (False, "No valid source file")


def _filter_pending_sources(
    sources: dict[tuple[str, str, str], AudioSource],
    output_dir: Path,
    *,
    force: bool = False,
) -> tuple[list[AudioSource], int]:
    """Filter out already processed recordings (unless force=True)."""
    if force:
        return list(sources.values()), 0
    pending, skipped = [], 0
    for (term, docket, rec_id), source in sources.items():
        flac_path = output_dir / term / docket / f"{rec_id}.flac"
        meta_path = output_dir / term / docket / f"{rec_id}.metadata.json"

        if flac_path.exists():
            skipped += 1
        else:
            if meta_path.exists():
                meta_path.unlink()
            pending.append(source)
    return pending, skipped


def _run_parallel_sources(
    pending: list[AudioSource],
    output_dir: Path,
    bits: int,
    num_workers: int,
    mp_context: Any,
    batch_size: int,
) -> tuple[int, int]:
    """Process recordings in parallel with batching."""
    shuffled = pending.copy()
    random.shuffle(shuffled)

    processed, errors = 0, 0
    with tqdm(total=len(shuffled), desc="Processing") as pbar:
        for batch_start in range(0, len(shuffled), batch_size):
            batch = shuffled[batch_start : batch_start + batch_size]

            with ProcessPoolExecutor(
                max_workers=num_workers,
                mp_context=mp_context,
                initializer=set_pdeathsig,
            ) as executor:
                futures = {
                    executor.submit(_process_recording, src, output_dir, bits): src
                    for src in batch
                }
                for future in as_completed(futures):
                    try:
                        success, _ = future.result()
                        processed += 1 if success else 0
                        errors += 0 if success else 1
                    except (BrokenExecutor, Exception):
                        errors += 1
                    pbar.update(1)
                    pbar.set_postfix(ok=processed, err=errors)

    return processed, errors


def _run_sequential_sources(
    pending: list[AudioSource], output_dir: Path, bits: int
) -> tuple[int, int]:
    """Process recordings sequentially."""
    processed, errors = 0, 0
    with tqdm(pending, desc="Processing", unit="file") as pbar:
        for source in pbar:
            success, _ = _process_recording(source, output_dir, bits)
            processed += 1 if success else 0
            errors += 0 if success else 1
            pbar.set_postfix(ok=processed, err=errors)
    return processed, errors
