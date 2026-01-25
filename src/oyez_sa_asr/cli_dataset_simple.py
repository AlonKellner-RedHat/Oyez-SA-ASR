# Edited by Claude
"""Simple dataset command with embedded audio.

Uses memory-efficient streaming extraction via PyAV seeking.
See cli_dataset_simple_flavors.py for duration-based variants.
"""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from .cli_dataset_helpers import collect_speakers, require_pyarrow
from .cli_dataset_simple_core import run_simple_dataset
from .cli_dataset_simple_flavors import (
    dataset_simple_lt1m,
    dataset_simple_lt5m,
    dataset_simple_lt30m,
)
from .cli_dataset_simple_proc import group_utterances_by_recording

console = Console(force_terminal=True)

# Re-export for backward compatibility with tests
_group_utterances_by_recording = group_utterances_by_recording


def register_simple_command(app: typer.Typer) -> None:
    """Register the simple commands on the given app."""
    app.command(name="simple")(dataset_simple)
    app.command(name="simple-lt1m")(dataset_simple_lt1m)
    app.command(name="simple-lt5m")(dataset_simple_lt5m)
    app.command(name="simple-lt30m")(dataset_simple_lt30m)


def dataset_simple(
    flex_dir: Annotated[
        Path,
        typer.Option("--flex-dir", "-f", help="Flex dataset directory"),
    ] = Path("datasets/flex"),
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-o", help="Base output directory"),
    ] = Path("datasets/simple"),
    terms: Annotated[
        list[str] | None,
        typer.Option("--term", "-T", help="Filter to specific term(s)"),
    ] = None,
    shard_size_mb: Annotated[
        int,
        typer.Option("--shard-size", "-s", help="Shard size in MB"),
    ] = 100,
    max_workers: Annotated[
        int | None,
        typer.Option("--max-workers", "-W", help="Max workers per step"),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-F", help="Force regeneration"),
    ] = False,
    include_invalid: Annotated[
        bool,
        typer.Option("--include-invalid", help="Include invalid utterances"),
    ] = False,
) -> None:
    """Create all three simple dataset splits (lt1m, lt5m, lt30m) sequentially."""
    if max_workers is not None and max_workers < 1:
        raise typer.BadParameter("--max-workers must be at least 1")

    console.print("[bold]Running all simple dataset splits sequentially[/bold]\n")

    # lt1m: [0, 60s) with up to 8 workers
    console.print("[cyan]━━━ Step 1/3: lt1m (<1 min) ━━━[/cyan]")
    run_simple_dataset(
        flex_dir,
        output_dir / "lt1m",
        terms,
        shard_size_mb,
        min(8, max_workers) if max_workers else 8,
        force,
        include_invalid,
        0,
        60,
        "oyez dataset simple-lt1m",
    )

    # lt5m: [60s, 300s) with up to 4 workers
    console.print("\n[cyan]━━━ Step 2/3: lt5m (1-5 min) ━━━[/cyan]")
    run_simple_dataset(
        flex_dir,
        output_dir / "lt5m",
        terms,
        shard_size_mb,
        min(4, max_workers) if max_workers else 4,
        force,
        include_invalid,
        60,
        300,
        "oyez dataset simple-lt5m",
    )

    # lt30m: [300s, 1800s) with up to 1 worker
    console.print("\n[cyan]━━━ Step 3/3: lt30m (5-30 min) ━━━[/cyan]")
    run_simple_dataset(
        flex_dir,
        output_dir / "lt30m",
        terms,
        shard_size_mb,
        min(1, max_workers) if max_workers else 1,
        force,
        include_invalid,
        300,
        1800,
        "oyez dataset simple-lt30m",
    )

    console.print("\n[bold green]All splits complete![/bold green]")
    console.print(f"Output directories: {output_dir}/lt1m, lt5m, lt30m")

    # Generate speakers parquet (shared across all splits)
    # Edited by Claude: Add speakers mode to simple dataset
    speakers_dir = Path("data/speakers")
    if speakers_dir.exists():
        console.print("\n[cyan]━━━ Generating speakers.parquet ━━━[/cyan]")
        pa, pq = require_pyarrow()
        speakers = collect_speakers(speakers_dir, terms)
        if speakers:
            data_dir = output_dir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            table = pa.Table.from_pylist(speakers)
            pq.write_table(table, data_dir / "speakers.parquet")
            console.print(f"  Generated speakers.parquet with {len(speakers)} speakers")
        else:
            console.print("  [yellow]No speakers found[/yellow]")
    else:
        console.print(
            "\n[yellow]Note:[/yellow] data/speakers not found. Skipping speakers.parquet generation."
        )
        console.print("  Run 'oyez process speakers' first to generate speaker data.")
