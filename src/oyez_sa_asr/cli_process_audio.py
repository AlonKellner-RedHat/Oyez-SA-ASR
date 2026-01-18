# Edited by Claude
"""Process audio subcommand for oyez_sa_asr CLI."""

import json
import os
import random
from concurrent.futures import BrokenExecutor, ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from tqdm import tqdm

from .audio_source import (
    AudioSource,
    find_audio_sources,
    get_preferred_format,
    get_source_era,
)
from .audio_utils import get_audio_metadata, load_audio, save_audio

console = Console(force_terminal=True)

_BATCH_SIZE = 500
_MAX_WORKERS = 4


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
    sources: dict[tuple[str, str, str], AudioSource], output_dir: Path
) -> tuple[list[AudioSource], int]:
    """Filter out already processed recordings."""
    pending, skipped = [], 0
    for key, source in sources.items():
        term, docket, rec_id = key
        if (output_dir / term / docket / f"{rec_id}.flac").exists():
            skipped += 1
        else:
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

            with ProcessPoolExecutor(max_workers=num_workers) as executor:
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
            typer.Option("--workers", "-w", help="Parallel workers"),
        ] = 0,
    ) -> None:
        """Process cached audio into standardized FLAC format with metadata."""
        cpu_workers = os.cpu_count() or 1
        num_workers = workers if workers > 0 else min(cpu_workers, _MAX_WORKERS)

        console.print("[bold]Processing cached audio files[/bold]")
        console.print(f"  Cache dir: {cache_dir}")
        console.print(f"  Output dir: {output_dir}")
        if terms:
            console.print(f"  Terms: {', '.join(terms)}")
        console.print(f"  FLAC bit depth: {bits}, Workers: {num_workers}")
        console.print()

        sources = find_audio_sources(cache_dir, terms)
        if not sources:
            console.print("[yellow]No audio files found in cache.[/yellow]")
            return

        console.print(f"Found {len(sources)} unique recordings")
        pending, skipped = _filter_pending_sources(sources, output_dir)

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
        console.print(f"Output: {output_dir}")
