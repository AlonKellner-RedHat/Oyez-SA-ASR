# Edited by Claude
"""Stats speakers command for oyez_sa_asr CLI."""

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console

console = Console(force_terminal=True)


def _format_hours(seconds: float) -> str:
    """Format seconds as hours with one decimal."""
    hours = seconds / 3600
    return f"{hours:,.1f}"


@dataclass
class SpeakerStats:
    """Aggregated statistics for speakers display."""

    total_speakers: int = 0
    total_turns: int = 0
    total_duration_seconds: float = 0.0
    total_words: int = 0
    role_counts: Counter[str] = field(default_factory=Counter)
    recording_distribution: Counter[str] = field(default_factory=Counter)
    speakers: list[dict[str, Any]] = field(default_factory=list)


def _load_speaker_files(
    speakers_dir: Path, terms: list[str] | None
) -> list[dict[str, Any]]:
    """Load all speaker files from subdirectories (justices/, other/)."""
    speakers: list[dict[str, Any]] = []
    term_set = set(terms) if terms else None

    # Search in subdirectories (justices/, other/)
    for speaker_file in speakers_dir.glob("*/*.json"):
        try:
            with speaker_file.open() as f:
                data = json.load(f)

            # If filtering by term, only include speakers with data in those terms
            if term_set:
                by_term = data.get("by_term", {})
                matching_terms = set(by_term.keys()) & term_set
                if not matching_terms:
                    continue

                # Recalculate totals for matching terms only
                filtered_totals = {
                    "recordings": 0,
                    "turns": 0,
                    "duration_seconds": 0.0,
                    "word_count": 0,
                }
                for term in matching_terms:
                    term_stats = by_term[term]
                    filtered_totals["recordings"] += term_stats.get("recordings", 0)
                    filtered_totals["turns"] += term_stats.get("turns", 0)
                    filtered_totals["duration_seconds"] += term_stats.get(
                        "duration_seconds", 0
                    )
                    filtered_totals["word_count"] += term_stats.get("word_count", 0)

                data["totals"] = filtered_totals

            speakers.append(data)

        except (json.JSONDecodeError, KeyError):
            continue

    return speakers


def _get_recording_bucket(num_recordings: int) -> str:
    """Get the distribution bucket for a recording count."""
    if num_recordings == 1:
        return "1"
    if num_recordings == 2:
        return "2"
    if num_recordings <= 5:
        return "3-5"
    if num_recordings <= 10:
        return "6-10"
    return "11+"


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

        role = speaker.get("role", "unknown")
        stats.role_counts[role] += 1

        # Recording distribution
        num_recordings = totals.get("recordings", 0)
        bucket = _get_recording_bucket(num_recordings)
        stats.recording_distribution[bucket] += 1

    return stats


def _print_recording_distribution(stats: SpeakerStats) -> None:
    """Print speaker distribution by recording count."""
    console.print("[bold]Speakers by recording count:[/bold]")
    # Order buckets correctly
    bucket_order = ["1", "2", "3-5", "6-10", "11+"]
    for bucket in bucket_order:
        count = stats.recording_distribution.get(bucket, 0)
        if count > 0:
            pct = count / stats.total_speakers * 100 if stats.total_speakers > 0 else 0
            label = "recording" if bucket == "1" else "recordings"
            console.print(f"  {bucket} {label}: {count:,} speakers ({pct:.1f}%)")
    console.print()


def _print_top_by_role(speakers: list[dict[str, Any]], top: int) -> None:
    """Print top speakers separated by role."""
    justices = [s for s in speakers if s.get("role") == "justice"]
    others = [s for s in speakers if s.get("role") != "justice"]

    # Sort by recordings
    justices_by_rec = sorted(
        justices, key=lambda s: s.get("totals", {}).get("recordings", 0), reverse=True
    )
    others_by_rec = sorted(
        others, key=lambda s: s.get("totals", {}).get("recordings", 0), reverse=True
    )

    console.print(f"[bold]Top {top} justices by recordings:[/bold]")
    for i, speaker in enumerate(justices_by_rec[:top], 1):
        name = speaker.get("name", "Unknown")
        recordings = speaker.get("totals", {}).get("recordings", 0)
        console.print(f"  {i}. {name} - {recordings:,} recordings")
    console.print()

    console.print(f"[bold]Top {top} others by recordings:[/bold]")
    for i, speaker in enumerate(others_by_rec[:top], 1):
        name = speaker.get("name", "Unknown")
        recordings = speaker.get("totals", {}).get("recordings", 0)
        console.print(f"  {i}. {name} - {recordings:,} recordings")


def stats_speakers(
    data_dir: Annotated[
        Path,
        typer.Option("--data-dir", "-d", help="Processed data directory"),
    ] = Path("data"),
    terms: Annotated[
        list[str] | None,
        typer.Option("--term", "-T", help="Filter to specific term(s)"),
    ] = None,
    top: Annotated[
        int,
        typer.Option("--top", "-n", help="Number of top speakers to display"),
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

    # Output
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
        pct = (count / stats.total_speakers) * 100 if stats.total_speakers > 0 else 0
        console.print(f"  {role}: {count:,} ({pct:.1f}%)")
    console.print()

    # Recording distribution
    _print_recording_distribution(stats)

    # Top speakers by turn count
    sorted_speakers = sorted(
        stats.speakers, key=lambda s: s.get("totals", {}).get("turns", 0), reverse=True
    )

    console.print(f"[bold]Top {top} speakers by turns:[/bold]")
    for i, speaker in enumerate(sorted_speakers[:top], 1):
        name = speaker.get("name", "Unknown")
        turns = speaker.get("totals", {}).get("turns", 0)
        console.print(f"  {i}. {name} - {turns:,} turns")
    console.print()

    # Top speakers by recordings, separated by role
    _print_top_by_role(stats.speakers, top)


def add_stats_speakers_command(app: typer.Typer) -> None:
    """Register the speakers command with the stats app."""
    app.command(name="speakers")(stats_speakers)
