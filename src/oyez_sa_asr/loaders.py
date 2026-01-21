# Edited by Claude
"""Dataset loaders for oyez-sa-asr.

Simple API for loading the three dataset tiers:
- raw: Original MP3/OGG audio + JSON metadata
- flex: Processed FLAC audio + parquet metadata
- simple: Embedded audio in parquet (with lt1m/lt5m/lt30m splits)

For HuggingFace-style loading, use load_simple_hf() which returns a
datasets.Dataset with proper Audio feature decoding.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

import av
import numpy as np
import pyarrow.parquet as pq

if TYPE_CHECKING:
    from numpy.typing import NDArray

# Type alias for optional HF datasets dependency
Dataset = Any  # Actually datasets.Dataset when installed

# Default dataset locations (relative to project root)
DEFAULT_RAW_DIR = Path("datasets/raw")
DEFAULT_FLEX_DIR = Path("datasets/flex")
DEFAULT_SIMPLE_DIR = Path("datasets/simple")


def load_simple_hf(
    split: str = "lt1m",
    data_dir: Path | None = None,
) -> Any:
    """Load simple dataset as HuggingFace Dataset with audio decoding.

    This is the recommended way to load the dataset - audio is automatically
    decoded into numpy arrays.

    Args:
        split: One of 'lt1m', 'lt5m', 'lt30m'
        data_dir: Override default datasets/simple directory

    Returns
    -------
        HuggingFace Dataset with decoded audio

    Example:
        ds = load_simple_hf("lt1m")
        sample = ds[0]
        print(sample["audio"]["array"])  # numpy array
        print(sample["sentence"])        # transcription
    """
    from datasets import load_dataset  # noqa: PLC0415  # ty: ignore  # pragma: no cover

    base = data_dir or DEFAULT_SIMPLE_DIR  # pragma: no cover
    return load_dataset(
        str(base), split=split, trust_remote_code=True
    )  # pragma: no cover


def load_simple(
    split: str = "lt1m",
    data_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Load simple dataset split as raw dicts (legacy).

    For HuggingFace-style loading with audio decoding, use load_simple_hf().

    Args:
        split: One of 'lt1m', 'lt5m', 'lt30m', or 'all'
        data_dir: Override default datasets/simple directory

    Returns
    -------
        List of utterance dicts with 'audio', 'sentence', 'speaker', etc.
    """
    base = data_dir or DEFAULT_SIMPLE_DIR
    splits = ["lt1m", "lt5m", "lt30m"] if split == "all" else [split]

    utterances: list[dict[str, Any]] = []
    for s in splits:
        split_dir = base / s / "data" / "utterances"
        if not split_dir.exists():
            continue
        for shard in sorted(split_dir.glob("train-*.parquet")):
            table = pq.read_table(shard)
            for row in table.to_pylist():
                row["_split"] = s
                utterances.append(row)
    return utterances


def load_flex(
    data_dir: Path | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load flex dataset metadata.

    Args:
        data_dir: Override default datasets/flex directory

    Returns
    -------
        Tuple of (recordings, utterances) as lists of dicts
    """
    base = data_dir or DEFAULT_FLEX_DIR
    recordings_pq = base / "data" / "recordings.parquet"
    utterances_pq = base / "data" / "utterances.parquet"

    recordings = (
        pq.read_table(recordings_pq).to_pylist() if recordings_pq.exists() else []
    )
    utterances = (
        pq.read_table(utterances_pq).to_pylist() if utterances_pq.exists() else []
    )
    return recordings, utterances


def load_raw(data_dir: Path | None = None) -> dict[str, list[Path]]:
    """Load raw dataset file paths.

    Args:
        data_dir: Override default datasets/raw directory

    Returns
    -------
        Dict with 'audio_files', 'transcripts', 'cases' as lists of Paths
    """
    base = data_dir or DEFAULT_RAW_DIR

    audio_dir = base / "audio"
    audio_files = list(audio_dir.rglob("*.mp3")) + list(audio_dir.rglob("*.ogg"))

    transcripts = list((base / "transcripts").rglob("*.json"))
    cases = list((base / "cases").rglob("*.json"))

    return {"audio_files": audio_files, "transcripts": transcripts, "cases": cases}


def play_audio(audio_bytes: bytes, rate: int = 16000) -> Any:
    """Display IPython audio widget for FLAC/audio bytes.

    Requires Jupyter environment with IPython installed.

    Args:
        audio_bytes: Raw audio bytes (FLAC format from simple dataset)
        rate: Sample rate (default 16000 for simple dataset)

    Returns
    -------
        IPython Audio widget
    """
    # IPython is optional - only available in Jupyter
    from IPython.display import Audio  # noqa: PLC0415  # ty: ignore  # pragma: no cover

    return Audio(data=audio_bytes, rate=rate)  # pragma: no cover


def extract_segment(
    audio_path: Path,
    start_sec: float,
    end_sec: float,
) -> tuple["NDArray[np.floating[Any]]", int]:
    """Extract audio segment from FLAC file.

    Args:
        audio_path: Path to FLAC file
        start_sec: Start time in seconds
        end_sec: End time in seconds

    Returns
    -------
        Tuple of (numpy array, sample_rate)

    Raises
    ------
        ValueError: If start_sec >= end_sec or segment exceeds audio length
    """
    if start_sec >= end_sec:
        msg = f"start_sec ({start_sec}) must be less than end_sec ({end_sec})"
        raise ValueError(msg)

    container = av.open(str(audio_path))  # pragma: no cover
    stream = container.streams.audio[0]  # pragma: no cover
    sample_rate = stream.rate  # pragma: no cover

    frames = []  # pragma: no cover
    for frame in container.decode(audio=0):  # pragma: no cover
        frames.append(frame.to_ndarray())  # pragma: no cover
    container.close()  # pragma: no cover

    audio = np.concatenate(frames, axis=1).flatten()  # pragma: no cover
    start_sample = int(start_sec * sample_rate)  # pragma: no cover
    end_sample = int(end_sec * sample_rate)  # pragma: no cover

    if end_sample > len(audio):  # pragma: no cover
        msg = f"Segment end ({end_sec}s) exceeds audio length ({len(audio) / sample_rate:.1f}s)"  # pragma: no cover
        raise ValueError(msg)  # pragma: no cover

    return audio[start_sample:end_sample], sample_rate  # pragma: no cover
