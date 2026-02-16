# Edited by Cursor: split from cli_dataset_helpers_collect (lintok; plan).
"""Collect recordings, utterances, speakers for flex dataset."""

import json
from pathlib import Path
from typing import Any

from .audio_source import parse_transcript_type_from_recording_id
from .cli_dataset_helpers_copy import load_justice_speaker_ids


def collect_recordings(
    audio_dir: Path,
    terms: list[str] | None,
    transcripts_dir: Path | None = None,
    speakers_dir: Path | None = None,
) -> list[dict[str, str | float | int | None | list[int]]]:
    """Collect recording metadata from processed audio (flex dataset)."""
    records: list[dict[str, str | float | int | None | list[int]]] = []
    term_set = set(terms) if terms else None

    if not audio_dir.exists():
        return records

    justice_ids = load_justice_speaker_ids(speakers_dir) if speakers_dir else set()

    transcript_speakers: dict[tuple[str, str, str], list[int]] = {}
    if transcripts_dir and transcripts_dir.exists():
        for term_dir in transcripts_dir.iterdir():
            if not term_dir.is_dir():
                continue
            if term_set and term_dir.name not in term_set:
                continue

            for docket_dir in term_dir.iterdir():
                if not docket_dir.is_dir():
                    continue

                for transcript_file in docket_dir.glob("*.json"):
                    try:
                        with transcript_file.open() as f:
                            data = json.load(f)

                        term = data.get("term", term_dir.name)
                        docket = data.get("case_docket", docket_dir.name)
                        transcript_type = data.get("type", "unknown")
                        key = (term, docket, transcript_type)

                        speaker_ids: set[int] = set()
                        for turn in data.get("turns", []):
                            if (
                                turn.get("is_valid")
                                and turn.get("speaker_id") is not None
                            ):
                                speaker_ids.add(turn["speaker_id"])

                        if speaker_ids:
                            transcript_speakers[key] = list(speaker_ids)
                    except (json.JSONDecodeError, KeyError):
                        continue

    for term_dir in audio_dir.iterdir():
        if not term_dir.is_dir():
            continue
        if term_set and term_dir.name not in term_set:
            continue

        for docket_dir in term_dir.iterdir():
            if not docket_dir.is_dir():
                continue

            for meta_file in docket_dir.glob("*.metadata.json"):
                try:
                    with meta_file.open() as f:
                        meta = json.load(f)

                    flac_name = meta_file.stem.replace(".metadata", "") + ".flac"
                    flac_path = docket_dir / flac_name
                    recording_id = meta_file.stem.replace(".metadata", "")

                    if not flac_path.exists():
                        continue

                    transcript_type = parse_transcript_type_from_recording_id(
                        recording_id
                    )

                    key = (term_dir.name, docket_dir.name, transcript_type)
                    recording_speaker_ids = transcript_speakers.get(key, [])
                    justice_speakers = [
                        sid for sid in recording_speaker_ids if sid in justice_ids
                    ]
                    other_speakers = [
                        sid for sid in recording_speaker_ids if sid not in justice_ids
                    ]
                    total_speakers = len(recording_speaker_ids)

                    records.append(
                        {
                            "term": term_dir.name,
                            "docket": docket_dir.name,
                            "recording_id": recording_id,
                            "transcript_type": transcript_type,
                            "audio_path": str(flac_path.relative_to(audio_dir)),
                            "duration_sec": meta.get("duration"),
                            "sample_rate": meta.get("sample_rate"),
                            "channels": meta.get("channels"),
                            "source_format": meta.get("source_format"),
                            "source_era": meta.get("source_era"),
                            "justice_speakers": justice_speakers,
                            "other_speakers": other_speakers,
                            "total_speakers": total_speakers,
                        }
                    )
                except (json.JSONDecodeError, KeyError):
                    continue

    return records


def collect_utterances(
    transcripts_dir: Path, terms: list[str] | None, speakers_dir: Path | None = None
) -> list[dict[str, str | float | int | None | bool]]:
    """Collect utterances from processed transcripts."""
    utterances: list[dict[str, str | float | int | None | bool]] = []
    term_set = set(terms) if terms else None

    justice_ids = load_justice_speaker_ids(speakers_dir)

    if not transcripts_dir.exists():
        return utterances

    for term_dir in transcripts_dir.iterdir():
        if not term_dir.is_dir():
            continue
        if term_set and term_dir.name not in term_set:
            continue

        for docket_dir in term_dir.iterdir():
            if not docket_dir.is_dir():
                continue

            for transcript_file in docket_dir.glob("*.json"):
                try:
                    with transcript_file.open() as f:
                        data = json.load(f)

                    term = data.get("term", term_dir.name)
                    docket = data.get("case_docket", docket_dir.name)
                    transcript_type = data.get("type", "")

                    for turn in data.get("turns", []):
                        speaker_id = turn.get("speaker_id")
                        is_justice = (
                            speaker_id is not None and speaker_id in justice_ids
                        )

                        utterances.append(
                            {
                                "term": term,
                                "docket": docket,
                                "transcript_type": transcript_type,
                                "turn_index": turn.get("index"),
                                "start_sec": turn.get("start"),
                                "end_sec": turn.get("stop"),
                                "duration_sec": turn.get("duration"),
                                "speaker_id": speaker_id,
                                "speaker_name": turn.get("speaker_name"),
                                "is_justice": is_justice,
                                "text": turn.get("text"),
                                "word_count": turn.get("word_count"),
                                "valid": turn.get("is_valid", False),
                                "invalid_reason": turn.get("invalid_reason"),
                            }
                        )
                except (json.JSONDecodeError, KeyError):
                    continue

    return utterances


def collect_speakers(
    speakers_dir: Path, terms: list[str] | None
) -> list[dict[str, Any]]:
    """Collect speaker statistics from speaker JSON files."""
    speakers: list[dict[str, Any]] = []
    term_set = set(terms) if terms else None

    if not speakers_dir.exists():
        return speakers

    for subdir_name in ("justices", "other"):
        subdir = speakers_dir / subdir_name
        if not subdir.exists():
            continue

        for speaker_file in subdir.glob("*.json"):
            try:
                with speaker_file.open() as f:
                    data = json.load(f)

                if term_set:
                    by_term = data.get("by_term", {})
                    matching_terms = set(by_term.keys()) & term_set
                    if not matching_terms:
                        continue
                    filtered_recordings = sum(
                        by_term.get(term, {}).get("recordings", 0)
                        for term in matching_terms
                    )
                    filtered_turns = sum(
                        by_term.get(term, {}).get("turns", 0) for term in matching_terms
                    )
                    filtered_duration = sum(
                        by_term.get(term, {}).get("duration_seconds", 0.0)
                        for term in matching_terms
                    )
                    filtered_words = sum(
                        by_term.get(term, {}).get("word_count", 0)
                        for term in matching_terms
                    )
                    filtered_cases = len(
                        {
                            case
                            for case in data.get("cases", [])
                            if any(
                                case.startswith(f"{term}/") for term in matching_terms
                            )
                        }
                    )

                    speaker_data = {
                        "speaker_id": data.get("id"),
                        "name": data.get("name"),
                        "role": data.get("role", "other"),
                        "total_recordings": filtered_recordings,
                        "total_cases": filtered_cases,
                        "total_turns": filtered_turns,
                        "total_duration_sec": round(filtered_duration, 2),
                        "total_word_count": filtered_words,
                        "first_appearance": min(
                            (term for term in matching_terms if term in by_term),
                            default=None,
                        ),
                        "last_appearance": max(
                            (term for term in matching_terms if term in by_term),
                            default=None,
                        ),
                        "by_term": {
                            k: v for k, v in by_term.items() if k in matching_terms
                        },
                    }
                else:
                    totals = data.get("totals", {})
                    speaker_data = {
                        "speaker_id": data.get("id"),
                        "name": data.get("name"),
                        "role": data.get("role", "other"),
                        "total_recordings": totals.get("recordings", 0),
                        "total_cases": totals.get("cases", 0),
                        "total_turns": totals.get("turns", 0),
                        "total_duration_sec": totals.get("duration_seconds", 0.0),
                        "total_word_count": totals.get("word_count", 0),
                        "first_appearance": data.get("first_appearance"),
                        "last_appearance": data.get("last_appearance"),
                        "by_term": data.get("by_term", {}),
                    }

                speakers.append(speaker_data)
            except (json.JSONDecodeError, KeyError):
                continue

    return speakers
