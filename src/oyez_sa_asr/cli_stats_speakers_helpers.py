# Edited by Claude
"""Helper functions for stats speakers command."""

from collections.abc import Callable
from typing import Any

from rich.console import Console

console = Console(force_terminal=True)


def _format_hours(seconds: float) -> str:
    """Format seconds as hours with one decimal."""
    return f"{seconds / 3600:,.1f}"


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


def _get_hours_bucket(duration_seconds: float) -> str:
    """Get the distribution bucket for spoken hours."""
    hours = duration_seconds / 3600
    thresholds = [
        (1, "<1h"),
        (2, "1-2h"),
        (5, "2-5h"),
        (10, "5-10h"),
        (50, "10-50h"),
        (100, "50-100h"),
    ]
    for threshold, label in thresholds:
        if hours < threshold:
            return label
    return "100h+"


def _split_by_role(speakers: list[dict[str, Any]]) -> tuple[list, list]:
    """Split speakers into justices and others."""
    justices = [s for s in speakers if s.get("role") == "justice"]
    others = [s for s in speakers if s.get("role") != "justice"]
    return justices, others


def _print_top_list(
    title: str,
    speakers: list[dict[str, Any]],
    top: int,
    get_value: Callable[[dict], Any],
    format_value: Callable[[Any], str],
) -> None:
    """Print a top N list of speakers."""
    console.print(f"[bold]{title}[/bold]")
    sorted_list = sorted(speakers, key=get_value, reverse=True)
    for i, speaker in enumerate(sorted_list[:top], 1):
        name = speaker.get("name", "Unknown")
        value = format_value(get_value(speaker))
        console.print(f"  {i}. {name} - {value}")


def print_role_hours_breakdown(speakers: list[dict[str, Any]]) -> None:
    """Print spoken hours breakdown by role."""
    justices, others = _split_by_role(speakers)

    justice_hours = (
        sum(s.get("totals", {}).get("duration_seconds", 0) for s in justices) / 3600
    )
    other_hours = (
        sum(s.get("totals", {}).get("duration_seconds", 0) for s in others) / 3600
    )
    total_hours = justice_hours + other_hours

    console.print("[bold]Spoken hours by role:[/bold]")
    if total_hours > 0:
        console.print(
            f"  Justices: {justice_hours:,.1f} h ({justice_hours / total_hours * 100:.1f}%)"
        )
        console.print(
            f"  Others: {other_hours:,.1f} h ({other_hours / total_hours * 100:.1f}%)"
        )
    else:
        console.print("  Justices: 0.0 h (0.0%)")
        console.print("  Others: 0.0 h (0.0%)")
    console.print()


def print_top_by_hours(speakers: list[dict[str, Any]], top: int) -> None:
    """Print top speakers by hours spoken, separated by role."""
    justices, others = _split_by_role(speakers)

    def get_duration(s: dict) -> float:
        return s.get("totals", {}).get("duration_seconds", 0)

    def fmt_hours(secs: float) -> str:
        return f"{secs / 3600:,.1f} h"

    _print_top_list(
        f"Top {top} justices by hours spoken:", justices, top, get_duration, fmt_hours
    )
    console.print()
    _print_top_list(
        f"Top {top} others by hours spoken:", others, top, get_duration, fmt_hours
    )


def print_top_by_recordings(speakers: list[dict[str, Any]], top: int) -> None:
    """Print top speakers by recordings, separated by role."""
    justices, others = _split_by_role(speakers)

    def get_recordings(s: dict) -> int:
        return s.get("totals", {}).get("recordings", 0)

    def fmt_recordings(n: int) -> str:
        return f"{n:,} recordings"

    _print_top_list(
        f"Top {top} justices by recordings:",
        justices,
        top,
        get_recordings,
        fmt_recordings,
    )
    console.print()
    _print_top_list(
        f"Top {top} others by recordings:", others, top, get_recordings, fmt_recordings
    )
