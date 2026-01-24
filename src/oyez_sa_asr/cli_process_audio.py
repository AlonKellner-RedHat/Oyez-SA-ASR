# Edited by Claude
"""Process audio subcommand for oyez_sa_asr CLI."""

import json
import multiprocessing as mp
import os
import random
from concurrent.futures import BrokenExecutor, ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from tqdm import tqdm

from .audio_analysis import detect_anomalies
from .audio_source import (
    AudioSource,
    find_audio_sources,
    get_preferred_format,
    get_source_era,
)
from .audio_utils import get_audio_metadata, load_audio, save_audio
from .memory_utils import set_pdeathsig

# Use spawn context to avoid issues with forking multithreaded programs
# and ensure proper PR_SET_PDEATHSIG behavior (workers die when main dies).
# Falls back to default context if spawn is unavailable.
try:
    _MP_CONTEXT = mp.get_context("spawn")
except ValueError:
    _MP_CONTEXT = None  # Will use default context

console = Console(force_terminal=True)

_BATCH_SIZE = 500
_MAX_WORKERS = 4


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
    """Validate that all pending sources have FLAC files after processing.

    Returns (missing_count, missing_sources).
    Edited by Claude.
    """
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
) -> tuple[bool, str, dict]:
    """Try to process a single audio file. Returns (success, error, metadata)."""
    try:
        out_dir = output_dir / term / docket
        out_dir.mkdir(parents=True, exist_ok=True)

        meta = get_audio_metadata(audio_path)
        meta["source_path"] = str(audio_path)
        meta["source_format"] = fmt
        meta["source_era"] = get_source_era(term)

        samples, sr = load_audio(audio_path)

        # Detect audio anomalies (silence, constant noise)
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
    """Filter out already processed recordings (unless force=True).

    Edited by Claude: Also check for orphaned metadata files without FLACs.
    """
    if force:
        return list(sources.values()), 0
    pending, skipped = [], 0
    for (term, docket, rec_id), source in sources.items():
        flac_path = output_dir / term / docket / f"{rec_id}.flac"
        meta_path = output_dir / term / docket / f"{rec_id}.metadata.json"

        # Check if FLAC exists (required)
        if flac_path.exists():
            skipped += 1
        else:
            # If metadata exists but FLAC doesn't, clean up orphaned metadata
            # Edited by Claude: Remove orphaned metadata to allow reprocessing
            if meta_path.exists():
                meta_path.unlink()
            pending.append(source)
    return pending, skipped


def _run_parallel_sources(
    pending: list[AudioSource], output_dir: Path, bits: int, num_workers: int
) -> tuple[int, int]:
    """Process recordings in parallel with batching."""
    shuffled = pending.copy()
    random.shuffle(shuffled)

    processed, errors = 0, 0
    with tqdm(total=len(shuffled), desc="Processing") as pbar:
        for batch_start in range(0, len(shuffled), _BATCH_SIZE):
            batch = shuffled[batch_start : batch_start + _BATCH_SIZE]

            with ProcessPoolExecutor(
                max_workers=num_workers,
                mp_context=_MP_CONTEXT,
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


def add_audio_command(app: typer.Typer) -> None:
    """Add the audio command to the process app."""

    @app.command(name="audio")
    def process_audio(
        cache_dir: Annotated[
            Path,
            typer.Option("--cache-dir", "-c", help="Cached audio directory"),
        ] = Path(".cache/audio"),
        output_dir: Annotated[
            Path,
            typer.Option("--output-dir", "-o", help="Output directory"),
        ] = Path("data/audio"),
        terms: Annotated[
            list[str] | None,
            typer.Option("--term", "-T", help="Filter to specific term(s)"),
        ] = None,
        bits: Annotated[
            int,
            typer.Option("--bits", "-b", help="FLAC bit depth (16 or 24)"),
        ] = 24,
        workers: Annotated[
            int,
            typer.Option(
                "--workers",
                "-w",
                help="Parallel workers (default: min(CPUs, 4), ~1GB RAM each)",
            ),
        ] = 0,
        force: Annotated[
            bool,
            typer.Option("--force", "-F", help="Reprocess existing files"),
        ] = False,
    ) -> None:
        """Process cached audio into FLAC format with metadata and anomaly detection."""
        cpu_workers = os.cpu_count() or 1
        num_workers = workers if workers > 0 else min(cpu_workers, _MAX_WORKERS)

        console.print("[bold]Processing cached audio files[/bold]")
        console.print(f"  Cache dir: {cache_dir}")
        console.print(f"  Output dir: {output_dir}")
        if terms:
            console.print(f"  Terms: {', '.join(terms)}")
        console.print(f"  FLAC bit depth: {bits}, Workers: {num_workers}")
        if force:
            console.print("  [yellow]Force mode: reprocessing existing files[/yellow]")
        console.print()

        sources = find_audio_sources(cache_dir, terms)
        if not sources:
            console.print("[yellow]No audio files found in cache.[/yellow]")
            return

        console.print(f"Found {len(sources)} unique recordings")
        pending, skipped = _filter_pending_sources(sources, output_dir, force=force)

        if skipped > 0:
            console.print(f"  Skipped (existing): {skipped}")
        if not pending:
            console.print("[green]All files already processed.[/green]")
            return

        if num_workers > 1 and len(pending) > 1:
            processed, errors = _run_parallel_sources(
                pending, output_dir, bits, num_workers
            )
        else:
            processed, errors = _run_sequential_sources(pending, output_dir, bits)

        console.print()
        console.print(f"[bold green]Done![/bold green] Processed {processed} files.")
        if errors > 0:
            console.print(f"[yellow]Errors:[/yellow] {errors} files failed")

        # Validate FLAC files were actually created
        # Edited by Claude: Check for missing FLACs after processing
        missing_count, missing_sources = _validate_flac_files(pending, output_dir)
        if missing_count > 0:
            console.print(
                f"[yellow]Warning:[/yellow] {missing_count} files were not converted to FLAC successfully"
            )
            # Log first few missing files for debugging
            for source in missing_sources[:5]:
                console.print(
                    f"  Missing: {source.term}/{source.docket}/{source.recording_id}"
                )
            if len(missing_sources) > 5:
                console.print(f"  ... and {len(missing_sources) - 5} more")

        # Report anomaly statistics
        anomaly_count = _count_anomalies(output_dir)
        if anomaly_count > 0:
            console.print(
                f"[yellow]Anomalies:[/yellow] {anomaly_count} files detected "
                "(see metadata.json for details)"
            )

        console.print(f"Output: {output_dir}")
