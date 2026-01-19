# Edited by Claude
"""Stats transcripts command for oyez_sa_asr CLI."""

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console

from .term_filter import filter_dirs

console = Console(force_terminal=True)


def _format_hours(seconds: float) -> str:
    """Format seconds as hours with one decimal."""
    hours = seconds / 3600
    return f"{hours:,.1f}"


def _get_speaker_bucket(num_speakers: int) -> str:
    """Get the distribution bucket for a speaker count."""
    if num_speakers == 1:
        return "1"
    if num_speakers == 2:
        return "2"
    if num_speakers <= 5:
        return "3-5"
    if num_speakers <= 10:
        return "6-10"
    return "11+"


@dataclass
class TranscriptStats:
    """Accumulated transcript statistics."""

    total_transcripts: int = 0
    total_turns: int = 0
    total_valid_turns: int = 0
    total_spoken_seconds: float = 0.0
    total_words: int = 0
    speaker_counts: Counter[str] = field(default_factory=Counter)
    type_counts: Counter[str] = field(default_factory=Counter)
    speaker_count_distribution: Counter[str] = field(default_factory=Counter)
    recordings_by_speakers: list[dict[str, Any]] = field(default_factory=list)


def _collect_transcript_stats(
    transcripts_dir: Path, terms: list[str] | None
) -> TranscriptStats:
    """Collect statistics from processed transcripts."""
    stats = TranscriptStats()
    term_dirs = filter_dirs(list(transcripts_dir.iterdir()), terms)

    for term_dir in term_dirs:
        if not term_dir.is_dir():
            continue
        for docket_dir in term_dir.iterdir():
            if not docket_dir.is_dir():
                continue
            for transcript_file in docket_dir.glob("*.json"):
                _process_transcript_file(transcript_file, stats)

    return stats


def _process_transcript_file(transcript_file: Path, stats: TranscriptStats) -> None:
    """Process a single transcript file and update stats."""
    try:
        with transcript_file.open() as f:
            data = json.load(f)

        stats.total_transcripts += 1
        transcript_type = data.get("type", "unknown")
        stats.type_counts[transcript_type] += 1

        transcript_speakers: set[str] = set()

        for turn in data.get("turns", []):
            stats.total_turns += 1
            if turn.get("is_valid"):
                stats.total_valid_turns += 1
                stats.total_spoken_seconds += turn.get("duration", 0) or 0
                stats.total_words += turn.get("word_count", 0) or 0
                speaker = turn.get("speaker_name")
                if speaker:
                    stats.speaker_counts[speaker] += 1
                    transcript_speakers.add(speaker)

        num_speakers = len(transcript_speakers)
        bucket = _get_speaker_bucket(num_speakers)
        stats.speaker_count_distribution[bucket] += 1

        term = data.get("term", "unknown")
        docket = data.get("case_docket", "unknown")
        stats.recordings_by_speakers.append(
            {
                "id": f"{term}/{docket}",
                "type": transcript_type,
                "speaker_count": num_speakers,
            }
        )

    except (json.JSONDecodeError, KeyError):
        pass


def stats_transcripts(
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
        typer.Option("--top", "-n", help="Number of top items to display"),
    ] = 10,
) -> None:
    """Display transcript statistics."""
    transcripts_dir = data_dir / "transcripts"

    if not transcripts_dir.exists():
        console.print(f"[red]Error:[/red] {transcripts_dir} not found.")
        console.print("Run 'oyez process transcripts' first.")
        raise typer.Exit(1)

    stats = _collect_transcript_stats(transcripts_dir, terms)

    if stats.total_transcripts == 0:
        console.print("[yellow]No transcripts found.[/yellow]")
        return

    valid_pct = (
        stats.total_valid_turns / stats.total_turns * 100
        if stats.total_turns > 0
        else 0
    )

    console.print()
    console.print("[bold]Transcript Statistics[/bold]")
    console.print("=" * 40)
    console.print(f"Total transcripts: {stats.total_transcripts:,}")
    console.print(f"Total turns: {stats.total_turns:,}")
    console.print(f"Total valid turns: {stats.total_valid_turns:,} ({valid_pct:.1f}%)")
    console.print(f"Total spoken time: {_format_hours(stats.total_spoken_seconds)} h")
    console.print(f"Total words: {stats.total_words:,}")
    console.print()

    console.print("[bold]By type:[/bold]")
    for transcript_type, count in stats.type_counts.most_common():
        console.print(f"  {transcript_type}: {count:,}")
    console.print()

    console.print("[bold]Recordings by speaker count:[/bold]")
    for bucket in ["1", "2", "3-5", "6-10", "11+"]:
        count = stats.speaker_count_distribution.get(bucket, 0)
        if count > 0:
            pct = count / stats.total_transcripts * 100
            label = "speaker" if bucket == "1" else "speakers"
            console.print(f"  {bucket} {label}: {count:,} recordings ({pct:.1f}%)")
    console.print()

    console.print(f"[bold]Top {top} speakers by turns:[/bold]")
    for i, (speaker, count) in enumerate(stats.speaker_counts.most_common(top), 1):
        console.print(f"  {i}. {speaker} - {count:,} turns")
    console.print()

    sorted_recs = sorted(
        stats.recordings_by_speakers, key=lambda r: r["speaker_count"], reverse=True
    )
    console.print(f"[bold]Top {top} recordings by speaker count:[/bold]")
    for i, rec in enumerate(sorted_recs[:top], 1):
        console.print(
            f"  {i}. {rec['id']} ({rec['type']}) - {rec['speaker_count']} speakers"
        )


def register_transcripts_command(app: typer.Typer) -> None:
    """Register the transcripts command with the stats app."""
    app.command(name="transcripts")(stats_transcripts)
