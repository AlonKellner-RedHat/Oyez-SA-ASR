# Edited by Claude
"""Core implementation for simple dataset creation."""

from pathlib import Path

import typer
from rich.console import Console

from .cli_dataset_helpers import require_pyarrow
from .cli_dataset_simple_load import (
    build_audio_paths,
    get_flex_terms,
    load_and_filter_utterances,
)
from .cli_dataset_simple_proc import process_by_recording
from .cli_dataset_state import (
    DatasetState,
    check_match,
    clean_dataset,
    load_state,
    make_state,
    save_state,
)

console = Console(force_terminal=True)


def _validate_flex_dataset(flex_dir: Path) -> tuple[Path, Path]:
    """Validate flex dataset exists and return paths."""
    utterances_pq = flex_dir / "data" / "utterances.parquet"
    if not utterances_pq.exists():
        console.print(f"[red]Error:[/red] {utterances_pq} not found.")
        console.print("Run 'oyez dataset flex' first.")
        raise typer.Exit(1)

    audio_dir = flex_dir / "audio"
    if not audio_dir.exists():
        console.print(f"[red]Error:[/red] {audio_dir} not found.")
        raise typer.Exit(1)

    return utterances_pq, audio_dir


def _check_state_and_clean(
    output_dir: Path, current_state: DatasetState, force: bool
) -> bool:
    """Check state and clean if needed. Returns True if should skip."""
    existing_state = load_state(output_dir)

    if not force and check_match(current_state, existing_state):
        console.print(
            "[yellow]Skipping:[/yellow] Dataset already exists with matching settings."
        )
        console.print("Use --force to regenerate.")
        return True

    if existing_state is not None:
        console.print("[dim]Cleaning existing dataset (settings changed)...[/dim]")
        removed = clean_dataset(output_dir)
        console.print(f"  Removed {removed} files")

    return False


def run_simple_dataset(
    flex_dir: Path,
    output_dir: Path,
    terms: list[str] | None,
    shard_size_mb: int,
    workers: int,
    force: bool,
    include_invalid: bool,
    min_duration_sec: float,
    max_duration_sec: float,
    flavor_name: str,
) -> None:
    """Core implementation for simple dataset creation."""
    pa, pq = require_pyarrow()

    console.print(f"[bold]Creating {flavor_name} dataset[/bold]")
    console.print(f"  Flex dir: {flex_dir}")
    console.print(f"  Output dir: {output_dir}")
    if terms:
        console.print(f"  Terms: {', '.join(terms)}")
    dur_desc = f"{min_duration_sec:.0f}s-{max_duration_sec:.0f}s"
    console.print(
        f"  Duration: {dur_desc}, Shard: {shard_size_mb}MB, Workers: {workers}"
    )
    console.print()

    utterances_pq, audio_dir = _validate_flex_dataset(flex_dir)

    effective_terms = terms if terms else get_flex_terms(flex_dir)
    current_state = make_state(
        flavor_name,
        effective_terms,
        shard_size_mb=shard_size_mb,
        min_duration=min_duration_sec,
        max_duration=max_duration_sec,
    )

    if _check_state_and_clean(output_dir, current_state, force):
        return

    save_state(output_dir, current_state)
    utterances = load_and_filter_utterances(
        pq,
        utterances_pq,
        terms,
        include_invalid=include_invalid,
        min_duration_sec=min_duration_sec,
        max_duration_sec=max_duration_sec,
    )
    audio_paths = build_audio_paths(flex_dir, pq, audio_dir, terms)

    console.print("Embedding audio segments and writing shards...")
    console.print(f"  Recordings: {len(audio_paths)}")
    try:
        stats = process_by_recording(
            utterances, audio_paths, output_dir, shard_size_mb, pa, pq, workers
        )
    except Exception as e:
        console.print()
        console.print("[bold red]Error: Processing failed![/bold red]")
        console.print(f"  {type(e).__name__}: {e}")
        console.print()
        console.print("[yellow]This is often caused by Out-Of-Memory (OOM).[/yellow]")
        console.print("Try running with fewer workers: --workers 1")
        raise typer.Exit(1) from e
    console.print(
        f"  Embedded {stats['embedded']} utterances, skipped {stats['skipped']}"
    )
    if stats["errors"] > 0:
        console.print(f"  [yellow]Warning:[/yellow] {stats['errors']} read errors")
    if stats["shards"] > 0:
        console.print(f"  Wrote {stats['shards']} shard files")

    current_state.completed = True
    save_state(output_dir, current_state)
    console.print()
    console.print("[bold green]Done![/bold green]")
    console.print(f"Output: {output_dir}")
