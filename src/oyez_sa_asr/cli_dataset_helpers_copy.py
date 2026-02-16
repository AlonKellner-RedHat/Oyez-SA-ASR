# Edited by Cursor: extracted from cli_dataset_helpers for lintok.
"""Copy and justice/speaker helpers for dataset commands."""

import json
import shutil
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from tqdm import tqdm

from .term_filter import filter_dirs

console = Console(force_terminal=True)


def load_justice_speaker_ids(speakers_dir: Path | None = None) -> set[int]:
    """Load set of justice speaker IDs from speaker files."""
    if speakers_dir is None:
        speakers_dir = Path("data/speakers")

    justices_dir = speakers_dir / "justices"
    if not justices_dir.exists():
        return set()

    justice_ids: set[int] = set()
    for speaker_file in justices_dir.glob("*.json"):
        try:
            with speaker_file.open() as f:
                data = json.load(f)
            speaker_id = data.get("id")
            if speaker_id is not None:
                justice_ids.add(speaker_id)
        except (json.JSONDecodeError, KeyError):
            continue

    return justice_ids


def require_pyarrow() -> tuple[Any, Any]:
    """Import and return pyarrow modules, or exit if not installed."""
    try:
        import pyarrow as pa_mod  # noqa: PLC0415
        import pyarrow.parquet as pq_mod  # noqa: PLC0415

        return pa_mod, pq_mod
    except ImportError:
        console.print("[red]Error:[/red] pyarrow not installed.")
        console.print("Run: uv add pyarrow")
        raise typer.Exit(1) from None


def copy_tree(src: Path, dst: Path, desc: str = "Copying") -> int:
    """Copy a directory tree, returning the number of files copied."""
    if not src.exists():
        return 0
    count = 0
    files = [f for f in src.rglob("*") if f.is_file()]
    for file in tqdm(files, desc=desc, unit="file"):
        dest = dst / file.relative_to(src)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, dest)
        count += 1
    return count


def copy_raw_audio(cache_dir: Path, output_dir: Path, terms: list[str] | None) -> int:
    """Copy raw audio files from cache."""
    total = 0
    for fmt in ("mp3", "ogg"):
        audio_cache = cache_dir / "audio" / f"oyez.case-media.{fmt}" / "case_data"
        if not audio_cache.exists():
            continue
        for term_dir in filter_dirs(list(audio_cache.iterdir()), terms):
            if term_dir.is_dir():
                dst = output_dir / "audio" / term_dir.name
                total += copy_tree(term_dir, dst, f"Audio {fmt}/{term_dir.name}")
    return total


def matches_term(json_file: Path, term_set: set[str]) -> bool:
    """Check if a JSON file's term is in the term set."""
    try:
        with json_file.open() as f:
            data = json.load(f)
        return data.get("term") in term_set
    except (json.JSONDecodeError, KeyError):
        return False


def copy_raw_cases(cache_dir: Path, output_dir: Path, term_set: set[str] | None) -> int:
    """Copy raw case JSON files from cache."""
    cases_cache = cache_dir / "cases" / "api.oyez.org" / "raw"
    if not cases_cache.exists():
        return 0
    cases_out = output_dir / "cases"
    cases_out.mkdir(parents=True, exist_ok=True)
    count = 0
    for json_file in tqdm(list(cases_cache.glob("*.json")), desc="Cases", unit="file"):
        if term_set and not matches_term(json_file, term_set):
            continue
        shutil.copy2(json_file, cases_out / json_file.name)
        count += 1
    return count


def copy_raw_transcripts(
    cache_dir: Path, output_dir: Path, term_set: set[str] | None
) -> int:
    """Copy raw transcript JSON files from cache."""
    if term_set:
        console.print(
            "  [yellow]Note:[/yellow] Transcript term filtering not supported; "
            "copying all transcripts"
        )
    transcripts_cache = cache_dir / "transcripts" / "api.oyez.org" / "raw"
    if not transcripts_cache.exists():
        return 0
    transcripts_out = output_dir / "transcripts"
    transcripts_out.mkdir(parents=True, exist_ok=True)
    count = 0
    for json_file in tqdm(
        list(transcripts_cache.glob("*.json")), desc="Transcripts", unit="file"
    ):
        shutil.copy2(json_file, transcripts_out / json_file.name)
        count += 1
    return count
