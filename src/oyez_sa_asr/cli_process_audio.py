# Edited by Claude. Edited by Cursor: split helpers to _cli_process_audio_helpers (lintok; plan).
"""Process audio subcommand for oyez_sa_asr CLI."""

import multiprocessing as mp
import os
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from ._cli_process_audio_helpers import (
    _count_anomalies,
    _filter_pending_sources,
    _process_recording,
    _run_sequential_sources,
    _try_process_file,
    _validate_flac_files,
)
from ._cli_process_audio_helpers import (
    _run_parallel_sources as _run_parallel_sources_impl,
)
from .audio_source import AudioSource, find_audio_sources

# Re-exported for tests; keep so ruff does not remove as unused.
__all__ = ["_process_recording", "_try_process_file", "add_audio_command"]


def _run_parallel_sources(
    pending: list["AudioSource"], output_dir: Path, bits: int, num_workers: int
) -> tuple[int, int]:
    """Thin wrapper that passes _MP_CONTEXT and _BATCH_SIZE to impl."""
    return _run_parallel_sources_impl(
        pending, output_dir, bits, num_workers, _MP_CONTEXT, _BATCH_SIZE
    )


try:
    _MP_CONTEXT = mp.get_context("spawn")
except ValueError:
    _MP_CONTEXT = None

console = Console(force_terminal=True)

_BATCH_SIZE = 500
_MAX_WORKERS = 4


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

        missing_count, missing_sources = _validate_flac_files(pending, output_dir)
        if missing_count > 0:
            console.print(
                f"[yellow]Warning:[/yellow] {missing_count} files were not converted to FLAC successfully"
            )
            for source in missing_sources[:5]:
                console.print(
                    f"  Missing: {source.term}/{source.docket}/{source.recording_id}"
                )
            if len(missing_sources) > 5:
                console.print(f"  ... and {len(missing_sources) - 5} more")

        anomaly_count = _count_anomalies(output_dir)
        if anomaly_count > 0:
            console.print(
                f"[yellow]Anomalies:[/yellow] {anomaly_count} files detected "
                "(see metadata.json for details)"
            )

        console.print(f"Output: {output_dir}")
