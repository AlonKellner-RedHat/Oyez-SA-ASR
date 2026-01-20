# Edited by Claude
"""Utterance filtering for dataset quality control.

Filters out invalid or corrupted utterances based on:
- Abnormal words-per-minute (too fast or too slow)
- Overlapping utterances (>3s overlap with others)
- Utterances taking >50% of recording duration
- Invalid timestamps (negative duration, end < start)
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FilterStats:
    """Statistics about filtered utterances."""

    total: int = 0
    invalid_timestamps: int = 0
    abnormal_wpm: int = 0
    overlapping: int = 0
    too_long_ratio: int = 0
    passed: int = 0


def _calculate_wpm(utterance: dict[str, Any]) -> float:
    """Calculate words per minute for an utterance."""
    duration = utterance.get("duration_sec", 0)
    word_count = utterance.get("word_count", 0)
    if duration <= 0:
        return 0.0
    return word_count / (duration / 60)


def _check_invalid_timestamps(utterance: dict[str, Any]) -> bool:
    """Check for invalid timestamps."""
    start = utterance.get("start_sec", 0)
    end = utterance.get("end_sec", 0)
    duration = utterance.get("duration_sec", 0)

    # Negative values
    if start < 0 or end < 0 or duration < 0:
        return True
    # End before start
    if end < start:
        return True
    # Duration mismatch (allow 1s tolerance)
    return abs(duration - (end - start)) > 1


def _check_abnormal_wpm(utterance: dict[str, Any]) -> bool:
    """Check for abnormal words-per-minute."""
    wpm = _calculate_wpm(utterance)
    duration = utterance.get("duration_sec", 0)

    # Only check WPM for utterances > 10 seconds
    if duration < 10:
        return False

    return wpm > 600 or wpm < 30


def _find_overlapping(
    utterances: list[dict[str, Any]], threshold_sec: float = 3.0
) -> set[int]:
    """Find utterances with >threshold overlap with others."""
    # Group by recording (term + docket + transcript_type)
    by_recording: dict[tuple[str, str, str], list[tuple[int, dict[str, Any]]]] = (
        defaultdict(list)
    )

    for i, u in enumerate(utterances):
        key = (u.get("term", ""), u.get("docket", ""), u.get("transcript_type", ""))
        by_recording[key].append((i, u))

    overlapping_indices: set[int] = set()

    for _key, rec_utts in by_recording.items():
        # Sort by start time
        rec_utts.sort(key=lambda x: x[1].get("start_sec", 0))

        for i, (idx_i, u_i) in enumerate(rec_utts):
            start_i = u_i.get("start_sec", 0)
            end_i = u_i.get("end_sec", 0)

            for idx_j, u_j in rec_utts[i + 1 :]:
                start_j = u_j.get("start_sec", 0)
                end_j = u_j.get("end_sec", 0)

                # If j starts after i ends, no more overlaps possible
                if start_j >= end_i:
                    break

                # Calculate overlap
                overlap_start = max(start_i, start_j)
                overlap_end = min(end_i, end_j)
                overlap_dur = overlap_end - overlap_start

                if overlap_dur > threshold_sec:
                    overlapping_indices.add(idx_i)
                    overlapping_indices.add(idx_j)

    return overlapping_indices


def _calculate_recording_durations(
    utterances: list[dict[str, Any]],
) -> dict[tuple[str, str, str], float]:
    """Calculate max end time for each recording."""
    max_end: dict[tuple[str, str, str], float] = defaultdict(float)

    for u in utterances:
        key = (u.get("term", ""), u.get("docket", ""), u.get("transcript_type", ""))
        end = u.get("end_sec", 0)
        max_end[key] = max(max_end[key], end)

    return max_end


def _check_too_long_ratio(
    utterance: dict[str, Any],
    recording_durations: dict[tuple[str, str, str], float],
    threshold: float = 0.5,
) -> bool:
    """Check if utterance takes >threshold of recording duration."""
    key = (
        utterance.get("term", ""),
        utterance.get("docket", ""),
        utterance.get("transcript_type", ""),
    )
    recording_dur = recording_durations.get(key, 0)
    utterance_dur = utterance.get("duration_sec", 0)

    if recording_dur <= 0:
        return False

    return utterance_dur / recording_dur > threshold


def filter_utterances(
    utterances: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], FilterStats]:
    """Filter utterances based on quality criteria.

    Returns
    -------
        Tuple of (filtered_utterances, stats)
    """
    stats = FilterStats(total=len(utterances))

    # Pre-calculate recording durations
    recording_durations = _calculate_recording_durations(utterances)

    # Find overlapping utterances (batch operation)
    overlapping_indices = _find_overlapping(utterances, threshold_sec=3.0)

    filtered: list[dict[str, Any]] = []

    for i, u in enumerate(utterances):
        # Check invalid timestamps
        if _check_invalid_timestamps(u):
            stats.invalid_timestamps += 1
            continue

        # Check abnormal WPM
        if _check_abnormal_wpm(u):
            stats.abnormal_wpm += 1
            continue

        # Check overlapping
        if i in overlapping_indices:
            stats.overlapping += 1
            continue

        # Check too long ratio
        if _check_too_long_ratio(u, recording_durations):
            stats.too_long_ratio += 1
            continue

        filtered.append(u)
        stats.passed += 1

    logger.info(
        "Filtered %d -> %d utterances: "
        "%d invalid timestamps, %d abnormal WPM, %d overlapping, %d too long",
        stats.total,
        stats.passed,
        stats.invalid_timestamps,
        stats.abnormal_wpm,
        stats.overlapping,
        stats.too_long_ratio,
    )

    return filtered, stats
