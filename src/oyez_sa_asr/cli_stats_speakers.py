# Edited by Claude
"""Stats speakers command for oyez_sa_asr CLI."""

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console

from .cli_stats_speakers_helpers import (
    _format_hours,
    _get_hours_bucket,
    _get_recording_bucket,
    print_role_hours_breakdown,
    print_top_by_hours,
    print_top_by_recordings,
)

console = Console(force_terminal=True)


@dataclass
class SpeakerStats:
    """Aggregated statistics for speakers display."""

    total_speakers: int = 0
    total_turns: int = 0
    total_duration_seconds: float = 0.0
    total_words: int = 0
    role_counts: Counter[str] = field(default_factory=Counter)
    recording_distribution: Counter[str] = field(default_factory=Counter)
    hours_distribution: Counter[str] = field(default_factory=Counter)
    speakers: list[dict[str, Any]] = field(default_factory=list)


def _load_speaker_files(
    speakers_dir: Path, terms: list[str] | None
) -> list[dict[str, Any]]:
    """Load all speaker files from subdirectories (justices/, other/)."""
    speakers: list[dict[str, Any]] = []
    term_set = set(terms) if terms else None

    for speaker_file in speakers_dir.glob("*/*.json"):
        try:
            with speaker_file.open() as f:
                data = json.load(f)

            if term_set:
                by_term = data.get("by_term", {})
                matching_terms = set(by_term.keys()) & term_set
                if not matching_terms:
                    continue
                data["totals"] = _recalculate_totals(by_term, matching_terms)

            speakers.append(data)
        except (json.JSONDecodeError, KeyError):
            continue

    return speakers


def _recalculate_totals(
    by_term: dict[str, Any], matching_terms: set[str]
) -> dict[str, Any]:
    """Recalculate totals for matching terms only."""
    totals = {"recordings": 0, "turns": 0, "duration_seconds": 0.0, "word_count": 0}
    for term in matching_terms:
        ts = by_term[term]
        totals["recordings"] += ts.get("recordings", 0)
        totals["turns"] += ts.get("turns", 0)
        totals["duration_seconds"] += ts.get("duration_seconds", 0)
        totals["word_count"] += ts.get("word_count", 0)
    return totals


def _collect_stats(speakers: list[dict[str, Any]]) -> SpeakerStats:
    """Collect aggregate statistics from speaker data."""
    stats = SpeakerStats()
    stats.total_speakers = len(speakers)
    stats.speakers = speakers

    for speaker in speakers:
        totals = speaker.get("totals", {})
        stats.total_turns += totals.get("turns", 0)
        stats.total_duration_seconds += totals.get("duration_seconds", 0.0)
        stats.total_words += totals.get("word_count", 0)

        stats.role_counts[speaker.get("role", "unknown")] += 1
        stats.recording_distribution[
            _get_recording_bucket(totals.get("recordings", 0))
        ] += 1
        stats.hours_distribution[
            _get_hours_bucket(totals.get("duration_seconds", 0.0))
        ] += 1

    return stats


def _print_recording_distribution(dist: Counter[str], total: int) -> None:
    """Print speaker distribution by recording count."""
    console.print("[bold]Speakers by recording count:[/bold]")
    bucket_order = ["1", "2", "3-5", "6-10", "11+"]
    for bucket in bucket_order:
        count = dist.get(bucket, 0)
        if count > 0:
            pct = count / total * 100 if total > 0 else 0
            label = "recording" if bucket == "1" else "recordings"
            console.print(f"  {bucket} {label}: {count:,} speakers ({pct:.1f}%)")
    console.print()


def _print_hours_distribution(dist: Counter[str], total: int) -> None:
    """Print speaker distribution by hours spoken."""
    console.print("[bold]Speakers by time spoken:[/bold]")
    bucket_order = [
        "<1m",
        "1-5m",
        "5-15m",
        "15-30m",
        "30-60m",
        "1-2h",
        "2-5h",
        "5-10h",
        "10-50h",
        "50-100h",
        "100h+",
    ]
    for bucket in bucket_order:
        count = dist.get(bucket, 0)
        if count > 0:
            pct = count / total * 100 if total > 0 else 0
            console.print(f"  {bucket}: {count:,} speakers ({pct:.1f}%)")
    console.print()


def stats_speakers(
    data_dir: Annotated[
        Path, typer.Option("--data-dir", "-d", help="Processed data directory")
    ] = Path("data"),
    terms: Annotated[
        list[str] | None,
        typer.Option("--term", "-T", help="Filter to specific term(s)"),
    ] = None,
    top: Annotated[
        int, typer.Option("--top", "-n", help="Number of top speakers to display")
    ] = 10,
) -> None:
    """Display speaker statistics."""
    speakers_dir = data_dir / "speakers"

    if not speakers_dir.exists():
        console.print(f"[red]Error:[/red] {speakers_dir} not found.")
        console.print("Run 'oyez process speakers' first.")
        raise typer.Exit(1)

    speakers = _load_speaker_files(speakers_dir, terms)
    if not speakers:
        console.print("[yellow]No speakers found.[/yellow]")
        return

    stats = _collect_stats(speakers)

    console.print()
    console.print("[bold]Speaker Statistics[/bold]")
    console.print("=" * 40)
    console.print(f"Total speakers: {stats.total_speakers:,}")
    console.print(f"Total turns: {stats.total_turns:,}")
    console.print(f"Total spoken time: {_format_hours(stats.total_duration_seconds)} h")
    console.print(f"Total words: {stats.total_words:,}")
    console.print()

    console.print("[bold]By role:[/bold]")
    for role, count in stats.role_counts.most_common():
        pct = count / stats.total_speakers * 100 if stats.total_speakers > 0 else 0
        console.print(f"  {role}: {count:,} ({pct:.1f}%)")
    console.print()

    print_role_hours_breakdown(stats.speakers)
    _print_recording_distribution(stats.recording_distribution, stats.total_speakers)
    _print_hours_distribution(stats.hours_distribution, stats.total_speakers)

    sorted_speakers = sorted(
        stats.speakers, key=lambda s: s.get("totals", {}).get("turns", 0), reverse=True
    )
    console.print(f"[bold]Top {top} speakers by turns:[/bold]")
    for i, speaker in enumerate(sorted_speakers[:top], 1):
        console.print(
            f"  {i}. {speaker.get('name', 'Unknown')} - "
            f"{speaker.get('totals', {}).get('turns', 0):,} turns"
        )
    console.print()

    print_top_by_recordings(stats.speakers, top)
    console.print()
    print_top_by_hours(stats.speakers, top)


def add_stats_speakers_command(app: typer.Typer) -> None:
    """Register the speakers command with the stats app."""
    app.command(name="speakers")(stats_speakers)
