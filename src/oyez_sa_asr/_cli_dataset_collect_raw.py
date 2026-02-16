# Edited by Cursor: split from cli_dataset_helpers_collect (lintok; plan).
"""Collect raw recording metadata from audio dir."""

from pathlib import Path


def collect_raw_recordings(
    audio_dir: Path, terms: list[str] | None
) -> list[dict[str, str | None]]:
    """Collect raw recording metadata from MP3/OGG files for HuggingFace parquet."""
    records: list[dict[str, str | None]] = []
    term_set = set(terms) if terms else None

    if not audio_dir.exists():
        return records

    seen: set[str] = set()

    for term_dir in audio_dir.iterdir():
        if not term_dir.is_dir():
            continue
        if term_set and term_dir.name not in term_set:
            continue

        for docket_dir in term_dir.iterdir():
            if not docket_dir.is_dir():
                continue

            for audio_file in docket_dir.glob("*"):
                if audio_file.suffix not in (".mp3", ".ogg"):
                    continue

                rec_id = audio_file.stem.split(".")[0]
                if rec_id in seen:
                    continue
                seen.add(rec_id)

                mp3_file = next(docket_dir.glob(f"{rec_id}*.mp3"), None)
                ogg_file = next(docket_dir.glob(f"{rec_id}*.ogg"), None)
                best_file = mp3_file or ogg_file
                if best_file is None:
                    continue

                audio_path = str(best_file.relative_to(audio_dir))

                records.append(
                    {
                        "recording_id": rec_id,
                        "audio_path": audio_path,
                        "term": term_dir.name,
                        "docket": docket_dir.name,
                    }
                )

    return records
