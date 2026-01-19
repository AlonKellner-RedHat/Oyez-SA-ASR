# Edited by Claude
"""Stats commands for displaying aggregate statistics."""

from collections import Counter
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from .cli_dataset_helpers import collect_recordings
from .cli_stats_cases import register_cases_command
from .cli_stats_speakers import add_stats_speakers_command
from .cli_stats_transcripts import register_transcripts_command

stats_app = typer.Typer(help="Display statistics for processed data")
console = Console(force_terminal=True)

# Register subcommands
register_cases_command(stats_app)
add_stats_speakers_command(stats_app)
register_transcripts_command(stats_app)


def _format_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024  # type: ignore[assignment]
    return f"{size_bytes:.1f} PB"


def _format_hours(seconds: float) -> str:
    """Format seconds as hours with one decimal."""
    hours = seconds / 3600
    return f"{hours:,.1f}"


@stats_app.command(name="audio")
def stats_audio(
    data_dir: Annotated[
        Path,
        typer.Option("--data-dir", "-d", help="Processed data directory"),
    ] = Path("data"),
    terms: Annotated[
        list[str] | None,
        typer.Option("--term", "-T", help="Filter to specific term(s)"),
    ] = None,
) -> None:
    """Display audio recording statistics."""
    audio_dir = data_dir / "audio"

    if not audio_dir.exists():
        console.print(f"[red]Error:[/red] {audio_dir} not found.")
        console.print("Run 'oyez process audio' first.")
        raise typer.Exit(1)

    recordings = collect_recordings(audio_dir, terms)

    if not recordings:
        console.print("[yellow]No recordings found.[/yellow]")
        return

    total_duration = sum(float(r.get("duration_sec") or 0) for r in recordings)
    total_size = 0

    for r in recordings:
        audio_path_str = r.get("audio_path")
        if audio_path_str and isinstance(audio_path_str, str):
            audio_path = audio_dir / audio_path_str
            if audio_path.exists():
                total_size += audio_path.stat().st_size

    era_counts: Counter[str] = Counter()
    format_counts: Counter[str] = Counter()
    term_counts: Counter[str] = Counter()
    for r in recordings:
        era_counts[str(r.get("source_era") or "unknown")] += 1
        format_counts[str(r.get("source_format") or "unknown")] += 1
        term_counts[str(r.get("term") or "unknown")] += 1

    console.print()
    console.print("[bold]Audio Statistics[/bold]")
    console.print("=" * 40)
    console.print(f"Total recordings: {len(recordings):,}")
    console.print(f"Total duration: {_format_hours(total_duration)} hours")
    console.print(f"Total size: {_format_size(total_size)}")
    console.print()

    console.print("[bold]By era:[/bold]")
    for era, count in era_counts.most_common():
        pct = count / len(recordings) * 100
        console.print(f"  {era}: {count:,} files ({pct:.1f}%)")
    console.print()

    console.print("[bold]By source format:[/bold]")
    for fmt, count in format_counts.most_common():
        console.print(f"  {fmt}: {count:,} files")
    console.print()

    console.print("[bold]By term (top 5):[/bold]")
    for term, count in term_counts.most_common(5):
        console.print(f"  {term}: {count:,} files")
