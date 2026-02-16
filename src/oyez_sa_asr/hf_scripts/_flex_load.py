# Edited by Cursor: split from flex (lintok; plan).
"""Heavy load/transform logic for flex dataset: recordings, utterances, speakers."""

import io
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import av
import numpy as np
import pyarrow.parquet as pq


def generate_recordings(
    data_dir: Path, audio_dir: Path
) -> Iterator[tuple[int, dict[str, Any]]]:
    """Yield full recording examples."""
    recordings_pq = data_dir / "recordings.parquet"
    if not recordings_pq.exists():
        return

    table = pq.read_table(recordings_pq)
    for idx, row in enumerate(table.to_pylist()):
        audio_path = audio_dir / row["audio_path"]
        if not audio_path.exists():
            continue

        yield (
            idx,
            {
                "recording_id": row["recording_id"],
                "audio": str(audio_path),
                "term": row["term"],
                "docket": row["docket"],
                "recording_type": row.get(
                    "transcript_type", row.get("recording_type", "unknown")
                ),
                "duration_sec": row["duration_sec"],
                "sample_rate": row["sample_rate"],
                "channels": row["channels"],
                "source_format": row["source_format"],
                "source_era": row["source_era"],
                "justice_speakers": row.get("justice_speakers", []),
                "other_speakers": row.get("other_speakers", []),
                "total_speakers": row.get("total_speakers", 0),
            },
        )


def generate_utterances(
    data_dir: Path, audio_dir: Path
) -> Iterator[tuple[int, dict[str, Any]]]:
    """Yield utterance examples with on-the-fly segment extraction."""
    recordings_pq = data_dir / "recordings.parquet"
    utterances_pq = data_dir / "utterances.parquet"

    if not recordings_pq.exists() or not utterances_pq.exists():
        return

    rec_table = pq.read_table(recordings_pq)
    rec_lookup: dict[tuple[str, str, str], list[dict]] = {}
    for row in rec_table.to_pylist():
        transcript_type = row.get(
            "transcript_type", row.get("recording_type", "unknown")
        )
        key = (row["term"], row["docket"], transcript_type)
        if key not in rec_lookup:
            rec_lookup[key] = []
        rec_lookup[key].append(row)

    audio_cache: dict[str, tuple[np.ndarray, int]] = {}

    utt_table = pq.read_table(utterances_pq)
    idx = 0

    for row in utt_table.to_pylist():
        if not row.get("valid", True):
            continue

        transcript_type = row.get("transcript_type", "unknown")
        key = (row["term"], row["docket"], transcript_type)
        recs = rec_lookup.get(key, [])
        if not recs:
            continue

        rec = recs[0]
        audio_path = audio_dir / rec["audio_path"]
        if not audio_path.exists():
            continue

        cache_key = str(audio_path)
        if cache_key not in audio_cache:
            try:
                container = av.open(str(audio_path))
                stream = container.streams.audio[0]
                sample_rate = stream.rate
                frames = []
                for frame in container.decode(audio=0):
                    frames.append(frame.to_ndarray())
                container.close()
                audio_data = np.concatenate(frames, axis=1).flatten()
                audio_cache[cache_key] = (audio_data, sample_rate)
            except Exception:  # noqa: S112
                continue

        audio_data, sample_rate = audio_cache[cache_key]

        start_sample = int(row["start_sec"] * sample_rate)
        end_sample = int(row["end_sec"] * sample_rate)
        end_sample = min(end_sample, len(audio_data))
        if start_sample >= end_sample:
            continue

        segment = audio_data[start_sample:end_sample]

        output = io.BytesIO()
        out_container = av.open(output, mode="w", format="wav")
        out_stream: av.AudioStream = out_container.add_stream(  # type: ignore[assignment]
            "pcm_f32le", rate=sample_rate
        )
        out_stream.layout = "mono"
        frame = av.AudioFrame.from_ndarray(
            segment.reshape(1, -1).astype(np.float32), format="flt", layout="mono"
        )
        frame.rate = sample_rate
        for packet in out_stream.encode(frame):
            out_container.mux(packet)
        for packet in out_stream.encode():
            out_container.mux(packet)
        out_container.close()

        transcript_type = row.get("transcript_type", "unknown")
        utt_id = f"{row['term']}_{row['docket']}_{transcript_type}_{row['turn_index']}"

        yield (
            idx,
            {
                "id": utt_id,
                "audio": {"bytes": output.getvalue(), "path": f"{utt_id}.wav"},
                "text": row.get("text", ""),
                "speaker_name": row.get("speaker_name", ""),
                "speaker_id": row.get("speaker_id") or 0,
                "is_justice": row.get("is_justice", False),
                "start_sec": row["start_sec"],
                "end_sec": row["end_sec"],
                "duration_sec": row["duration_sec"],
                "term": row["term"],
                "docket": row["docket"],
                "recording_type": transcript_type,
            },
        )
        idx += 1


def generate_speakers(data_dir: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    """Yield speaker examples from parquet."""
    speakers_pq = data_dir / "speakers.parquet"
    if not speakers_pq.exists():
        return

    table = pq.read_table(speakers_pq)
    for idx, row in enumerate(table.to_pylist()):
        by_term_list = [
            {"term": term, **stats} for term, stats in row.get("by_term", {}).items()
        ]

        yield (
            idx,
            {
                "speaker_id": row["speaker_id"],
                "name": row["name"],
                "role": row["role"],
                "total_recordings": row["total_recordings"],
                "total_cases": row["total_cases"],
                "total_turns": row["total_turns"],
                "total_duration_sec": row["total_duration_sec"],
                "total_word_count": row["total_word_count"],
                "first_appearance": row.get("first_appearance") or "",
                "last_appearance": row.get("last_appearance") or "",
                "by_term": by_term_list,
            },
        )
