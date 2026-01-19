# Edited by Claude
"""Simple dataset command with embedded audio.

Optimized to load each recording once and extract segments for all
utterances from that recording before moving on.
"""

import json
import os
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console

from .cli_dataset_helpers import require_pyarrow
from .cli_dataset_simple_proc import group_utterances_by_recording, process_by_recording
from .cli_dataset_state import (
    check_match,
    clean_dataset,
    load_state,
    make_state,
    save_state,
)

console = Console(force_terminal=True)


# Re-export for backward compatibility with tests
_group_utterances_by_recording = group_utterances_by_recording


def register_simple_command(app: typer.Typer) -> None:
    """Register the simple command on the given app."""
    app.command(name="simple")(dataset_simple)


def _get_flex_terms(flex_dir: Path) -> list[str]:
    """Get terms from flex dataset index."""
    index_file = flex_dir / "index.json"
    if not index_file.exists():
        return []
    try:
        with index_file.open() as f:
            flex_index = json.load(f)
        return flex_index.get("terms", [])
    except (json.JSONDecodeError, OSError):
        return []


def dataset_simple(
    flex_dir: Annotated[
        Path,
        typer.Option("--flex-dir", "-f", help="Flex dataset directory"),
    ] = Path("datasets/flex"),
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-o", help="Dataset output directory"),
    ] = Path("datasets/simple"),
    shard_size_mb: Annotated[
        int,
        typer.Option("--shard-size", "-s", help="Parquet shard size in MB"),
    ] = 500,
    workers: Annotated[
        int | None,
        typer.Option(
            "--workers", "-w", help="Parallel workers (default: min(CPU/2, 4))"
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-F", help="Force regeneration if output exists"),
    ] = False,
) -> None:
    """Create oyez-sa-asr-simple dataset with embedded audio."""
    pa, pq = require_pyarrow()

    # Default to half CPU count (max 4) to avoid memory exhaustion
    if workers is not None:
        num_workers = workers
    else:
        cpu_count = os.cpu_count() or 2
        num_workers = min(cpu_count // 2, 4) or 1

    console.print("[bold]Creating oyez-sa-asr-simple dataset[/bold]")
    console.print(f"  Flex dir: {flex_dir}")
    console.print(f"  Output dir: {output_dir}")
    console.print(f"  Shard size: {shard_size_mb} MB")
    console.print(f"  Workers: {num_workers}")
    console.print()

    # Validate flex dataset first (needed for state check)
    utterances_pq = flex_dir / "data" / "utterances.parquet"
    if not utterances_pq.exists():
        console.print(f"[red]Error:[/red] {utterances_pq} not found.")
        console.print("Run 'oyez dataset flex' first.")
        raise typer.Exit(1)

    audio_dir = flex_dir / "audio"
    if not audio_dir.exists():
        console.print(f"[red]Error:[/red] {audio_dir} not found.")
        raise typer.Exit(1)

    # Get terms from flex dataset for state tracking
    flex_terms = _get_flex_terms(flex_dir)

    # Check state and handle mismatch/skip
    current_state = make_state(
        "oyez dataset simple", flex_terms, shard_size_mb=shard_size_mb
    )
    existing_state = load_state(output_dir)

    if not force and check_match(current_state, existing_state):
        console.print(
            "[yellow]Skipping:[/yellow] Dataset already exists with matching settings."
        )
        console.print("Use --force to regenerate.")
        return

    if existing_state is not None:
        console.print("[dim]Cleaning existing dataset (settings changed)...[/dim]")
        removed = clean_dataset(output_dir)
        console.print(f"  Removed {removed} files")

    # Save incomplete state before starting
    save_state(output_dir, current_state)

    console.print("Reading utterances...")
    utterances = pq.read_table(utterances_pq).to_pylist()
    console.print(f"  Found {len(utterances)} utterances")

    audio_paths = _build_audio_paths(flex_dir, pq, audio_dir)

    console.print("Embedding audio segments and writing shards...")
    console.print(f"  Recordings: {len(audio_paths)}")
    stats = process_by_recording(
        utterances, audio_paths, output_dir, shard_size_mb, pa, pq, num_workers
    )
    console.print(
        f"  Embedded {stats['embedded']} utterances, skipped {stats['skipped']}"
    )
    if stats["errors"] > 0:
        console.print(f"  [yellow]Warning:[/yellow] {stats['errors']} read errors")
    if stats["shards"] > 0:
        console.print(f"  Wrote {stats['shards']} shard files")

    # Mark as complete
    current_state.completed = True
    save_state(output_dir, current_state)

    console.print()
    console.print("[bold green]Done![/bold green]")
    console.print(f"Output: {output_dir}")


def _build_audio_paths(
    flex_dir: Path, pq: Any, audio_dir: Path
) -> dict[tuple[str, str], Path]:
    """Build audio path lookup from recordings."""
    audio_paths: dict[tuple[str, str], Path] = {}
    recordings_pq = flex_dir / "data" / "recordings.parquet"
    if not recordings_pq.exists():
        return audio_paths

    for rec in pq.read_table(recordings_pq).to_pylist():
        key = (rec["term"], rec["docket"])
        path = audio_dir / rec["audio_path"]
        if path.exists():
            audio_paths[key] = path
    return audio_paths
