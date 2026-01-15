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

from .audio_utils import get_audio_metadata, load_audio, save_audio

console = Console(force_terminal=True)

# Process files in batches to limit memory usage from pending futures
_BATCH_SIZE = 500
# Limit workers to prevent OOM - audio files can use 300+ MB RAM each
_MAX_WORKERS = 4


def _find_audio_files(cache_dir: Path) -> list[Path]:
    """Find all audio files in cache directory."""
    audio_files = []
    for fmt in ("mp3", "ogg"):
        pattern = f"oyez.case-media.{fmt}/case_data/**/*.{fmt}"
        audio_files.extend(cache_dir.glob(pattern))
    return audio_files


def _extract_term_docket(path: Path) -> tuple[str, str] | None:
    """Extract term and docket from audio path."""
    parts = path.parts
    try:
        idx = parts.index("case_data")
        return parts[idx + 1], parts[idx + 2]
    except (ValueError, IndexError):
        return None


def _process_single_file(
    audio_path: Path, output_dir: Path, bits: int
) -> tuple[bool, str]:
    """Process a single audio file. Returns (success, error_message)."""
    try:
        info = _extract_term_docket(audio_path)
        if info is None:
            return (False, "Could not extract term/docket")

        term, docket = info
        out_dir = output_dir / term / docket
        out_dir.mkdir(parents=True, exist_ok=True)

        meta = get_audio_metadata(audio_path)
        meta["source_path"] = str(audio_path)
        samples, sr = load_audio(audio_path)
        flac_path = out_dir / f"{audio_path.stem}.flac"
        save_audio(samples, sr, flac_path, format="flac", bits_per_sample=bits)
        with (out_dir / f"{audio_path.stem}.metadata.json").open("w") as f:
            json.dump(meta, f, indent=2)

        return (True, "")
    except Exception as e:
        return (False, str(e))


def _filter_pending(
    audio_files: list[Path], output_dir: Path
) -> tuple[list[Path], int]:
    """Filter out already processed files. Returns (pending, skipped_count)."""
    pending, skipped = [], 0
    for audio_path in audio_files:
        info = _extract_term_docket(audio_path)
        if info is None:
            continue
        term, docket = info
        if (output_dir / term / docket / f"{audio_path.stem}.flac").exists():
            skipped += 1
        else:
            pending.append(audio_path)
    return pending, skipped


def _run_parallel(
    pending: list[Path], output_dir: Path, bits: int, num_workers: int
) -> tuple[int, int]:
    """Process files in parallel with batching. Returns (processed, errors)."""
    # Shuffle to distribute load across different years/cases
    shuffled = pending.copy()
    random.shuffle(shuffled)

    processed, errors = 0, 0
    total = len(shuffled)

    with tqdm(total=total, desc="Processing") as pbar:
        # Process in batches to limit memory from pending futures
        for batch_start in range(0, total, _BATCH_SIZE):
            batch = shuffled[batch_start : batch_start + _BATCH_SIZE]

            # Note: max_tasks_per_child causes deadlock in Python 3.14 when all
            # workers recycle simultaneously. Batching handles memory instead.
            with ProcessPoolExecutor(max_workers=num_workers) as executor:
                futures = {
                    executor.submit(_process_single_file, p, output_dir, bits): p
                    for p in batch
                }

                for future in as_completed(futures):
                    try:
                        success, _ = future.result()
                        if success:
                            processed += 1
                        else:
                            errors += 1
                    except BrokenExecutor:
                        # Worker crashed - count as error, pool will restart
                        errors += 1
                    except Exception:
                        errors += 1

                    pbar.update(1)
                    pbar.set_postfix(ok=processed, err=errors)

    return processed, errors


def _run_sequential(
    pending: list[Path], output_dir: Path, bits: int
) -> tuple[int, int]:
    """Process files sequentially. Returns (processed, errors)."""
    processed, errors = 0, 0
    with tqdm(pending, desc="Processing", unit="file") as pbar:
        for audio_path in pbar:
            if _process_single_file(audio_path, output_dir, bits)[0]:
                processed += 1
            else:
                errors += 1
            pbar.set_postfix(ok=processed, err=errors)
    return processed, errors


def add_audio_command(app: typer.Typer) -> None:
    """Add the audio command to the process app."""

    @app.command(name="audio")
    def process_audio(
        cache_dir: Annotated[
            Path,
            typer.Option("--cache-dir", "-c", help="Directory with cached audio"),
        ] = Path(".cache/audio"),
        output_dir: Annotated[
            Path,
            typer.Option("--output-dir", "-o", help="Output directory for audio"),
        ] = Path("data/audio"),
        bits: Annotated[
            int,
            typer.Option("--bits", "-b", help="FLAC bit depth (16 or 24)"),
        ] = 24,
        workers: Annotated[
            int,
            typer.Option("--workers", "-w", help="Number of parallel workers"),
        ] = 0,
    ) -> None:
        """Process cached audio into standardized FLAC format with metadata."""
        # Limit workers to prevent OOM - audio files can use 300+ MB RAM each
        cpu_workers = os.cpu_count() or 1
        num_workers = workers if workers > 0 else min(cpu_workers, _MAX_WORKERS)

        console.print("[bold]Processing cached audio files[/bold]")
        console.print(f"  Cache dir: {cache_dir}")
        console.print(f"  Output dir: {output_dir}")
        console.print(f"  FLAC bit depth: {bits}, Workers: {num_workers}")
        console.print()

        audio_files = _find_audio_files(cache_dir)
        if not audio_files:
            console.print("[yellow]No audio files found in cache.[/yellow]")
            return

        console.print(f"Found {len(audio_files)} audio files")
        pending, skipped = _filter_pending(audio_files, output_dir)

        if skipped > 0:
            console.print(f"  Skipped (existing): {skipped}")
        if not pending:
            console.print("[green]All files already processed.[/green]")
            return

        if num_workers > 1 and len(pending) > 1:
            processed, errors = _run_parallel(pending, output_dir, bits, num_workers)
        else:
            processed, errors = _run_sequential(pending, output_dir, bits)

        console.print()
        console.print(f"[bold green]Done![/bold green] Processed {processed} files.")
        if errors > 0:
            console.print(f"[yellow]Errors:[/yellow] {errors} files failed")
        console.print(f"Output: {output_dir}")
