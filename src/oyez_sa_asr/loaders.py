# Edited by Claude
"""Dataset loaders for oyez-sa-asr.

Simple API for loading the three dataset tiers:
- raw: Original MP3/OGG audio + JSON metadata
- flex: Processed FLAC audio + parquet metadata
- simple: Embedded audio in parquet

HuggingFace loaders (load_*_hf functions):
- Use parquet auto-discovery (datasets v4.x compatible)
- Best for basic loading without advanced features

Native Python loaders (load_raw, load_flex, load_simple):
- Provide full access to metadata and audio segment extraction
- Recommended for custom processing pipelines
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

# Resolve project root (parent of src/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Default dataset locations (relative to project root)
DEFAULT_RAW_DIR = _PROJECT_ROOT / "datasets" / "raw"
DEFAULT_FLEX_DIR = _PROJECT_ROOT / "datasets" / "flex"
DEFAULT_SIMPLE_DIR = _PROJECT_ROOT / "datasets" / "simple"


# Edited by Claude: Export features schema for v4.x compatibility (no trust_remote_code)
def _get_simple_features() -> Any:
    """Get Features schema for simple dataset.

    Exported as SIMPLE_FEATURES constant for use with generic load_dataset in v4.x.
    """
    from datasets import Audio, Features, Value  # noqa: PLC0415

    return Features(
        {
            "id": Value("string"),
            "audio": Audio(sampling_rate=None, decode=False),
            "sentence": Value("string"),
            "speaker": Value("string"),
            "speaker_id": Value("int64"),
            "is_justice": Value("bool"),
            "duration": Value("float64"),
            "term": Value("string"),
            "docket": Value("string"),
            "recording_type": Value("string"),
            "start_sec": Value("float64"),
            "end_sec": Value("float64"),
        }
    )


# Export as constant for easy import
try:
    SIMPLE_FEATURES = _get_simple_features()
except ImportError:
    SIMPLE_FEATURES = None  # type: ignore[assignment]


def load_simple_hf(
    split: str = "lt1m",
    data_dir: Path | None = None,
    *,
    streaming: bool = False,
) -> Any:
    """Load simple dataset as HuggingFace Dataset with audio decoding.

    This is the recommended way to load the dataset - audio is automatically
    decoded into numpy arrays. The schema is automatically applied, so users
    don't need to specify features manually.

    Args:
        split: One of 'lt1m', 'lt5m', 'lt30m'
        data_dir: Override default datasets/simple directory
        streaming: If True, return IterableDataset for memory-efficient streaming

    Returns
    -------
        HuggingFace Dataset (or IterableDataset if streaming=True)

    Raises
    ------
        FileNotFoundError: If the dataset hasn't been generated yet

    Example:
        # Standard loading (random access)
        ds = load_simple_hf("lt1m")
        sample = ds[0]

        # Streaming mode (memory efficient)
        ds = load_simple_hf("lt1m", streaming=True)
        for sample in ds:
            print(sample["sentence"])
    """
    # Edited by Claude: Include explicit Features schema to avoid CastError
    from datasets import load_dataset  # noqa: PLC0415  # pragma: no cover

    base = data_dir or DEFAULT_SIMPLE_DIR  # pragma: no cover
    split_dir = base / split / "data" / "utterances"  # pragma: no cover
    if not split_dir.exists():  # pragma: no cover
        msg = f"Dataset not found at {split_dir}. Run 'oyez dataset simple' first."
        raise FileNotFoundError(msg)

    # Use exported features schema
    features = _get_simple_features()  # pragma: no cover

    parquet_pattern = str(split_dir / "*.parquet")  # pragma: no cover
    return load_dataset(
        "parquet",
        data_files=parquet_pattern,
        split="train",
        streaming=streaming,
        features=features,
    )  # pragma: no cover


def load_raw_hf(
    data_dir: Path | None = None,
    *,
    streaming: bool = False,
) -> Any:
    """Load raw dataset as HuggingFace Dataset via parquet auto-discovery.

    Uses parquet-based loading (datasets v4.x compatible). For full metadata
    access including transcripts and case info, use load_raw() instead.

    Note: Returns audio_path as a string path, not decoded audio. Use the
    audio_path to load audio files manually.

    Args:
        data_dir: Override default datasets/raw directory
        streaming: If True, return IterableDataset for memory-efficient streaming

    Returns
    -------
        HuggingFace Dataset with recording_id, audio_path, term, docket

    Example:
        ds = load_raw_hf()
        sample = ds["train"][0]
        audio_file = Path("datasets/raw/audio") / sample["audio_path"]
    """
    from datasets import load_dataset  # noqa: PLC0415  # pragma: no cover

    base = data_dir or DEFAULT_RAW_DIR  # pragma: no cover
    return load_dataset(str(base), streaming=streaming)  # pragma: no cover


def load_flex_hf(
    config: str = "recordings",
    data_dir: Path | None = None,
    *,
    streaming: bool = False,
) -> Any:
    """Load flex dataset as HuggingFace Dataset via parquet auto-discovery.

    Uses parquet-based loading (datasets v4.x compatible).

    Args:
        config: One of 'recordings' (full FLAC metadata) or 'utterances' (segments).
                Note: 'utterances' returns metadata only, no audio extraction.
                For audio extraction, use load_flex() + extract_segment().
        data_dir: Override default datasets/flex directory
        streaming: If True, return IterableDataset for memory-efficient streaming

    Returns
    -------
        HuggingFace Dataset

    Example:
        # Load recordings metadata
        ds = load_flex_hf("recordings")

        # Load utterances metadata (no audio)
        ds = load_flex_hf("utterances")
    """
    from datasets import load_dataset  # noqa: PLC0415  # pragma: no cover

    base = data_dir or DEFAULT_FLEX_DIR  # pragma: no cover
    return load_dataset(str(base), config, streaming=streaming)  # pragma: no cover


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


def load_raw(data_dir: Path | None = None) -> list[dict[str, Any]]:
    """Load raw dataset as item-based rows.

    Each row represents a recording with paths to associated metadata files.

    Args:
        data_dir: Override default datasets/raw directory

    Returns
    -------
        List of dicts with keys:
        - recording_id: Unique recording identifier (e.g. "19990303o_96-1793")
        - term: Court term year
        - docket: Case docket number
        - audio_path: Path to MP3 audio file (or None)
        - audio_ogg_path: Path to OGG audio file (or None)
        - transcript_path: Path to transcript JSON (or None)
        - case_path: Path to case JSON (or None)
    """
    import json  # noqa: PLC0415

    base = data_dir or DEFAULT_RAW_DIR
    audio_dir = base / "audio"

    # Build case index: (term, docket) -> case_path
    case_index: dict[tuple[str, str], Path] = {}
    for case_path in (base / "cases").glob("*.json"):
        try:
            with case_path.open() as f:
                case_data = json.load(f)
            term = str(case_data.get("term", ""))
            docket = case_data.get("docket_number", "")
            if term and docket:
                case_index[(term, docket)] = case_path
        except (json.JSONDecodeError, OSError):
            pass

    # Build transcript index: recording_id -> transcript_path
    transcript_index: dict[str, Path] = {}
    for t_path in (base / "transcripts").glob("*.json"):
        try:
            with t_path.open() as f:
                t_data = json.load(f)
            for mf in t_data.get("media_file") or []:
                if not mf:
                    continue
                href = mf.get("href", "")
                # Extract recording_id from URL like ".../19990303o_96-1793.delivery.mp3"
                filename = href.rsplit("/", 1)[-1]
                rec_id = filename.split(".")[0]  # Strip .delivery.mp3 or .ogg
                if rec_id:
                    transcript_index[rec_id] = t_path
        except (json.JSONDecodeError, OSError):
            pass

    # Build items from audio files (prefer MP3 as primary)
    mp3_files = {p.stem.split(".")[0]: p for p in audio_dir.rglob("*.mp3")}
    ogg_files = {p.stem.split(".")[0]: p for p in audio_dir.rglob("*.ogg")}
    all_rec_ids = set(mp3_files.keys()) | set(ogg_files.keys())

    items: list[dict[str, Any]] = []
    for rec_id in sorted(all_rec_ids):
        mp3_path = mp3_files.get(rec_id)
        ogg_path = ogg_files.get(rec_id)
        primary = mp3_path or ogg_path
        assert primary is not None  # At least one must exist

        term = primary.parent.parent.name
        docket = primary.parent.name

        items.append(
            {
                "recording_id": rec_id,
                "term": term,
                "docket": docket,
                "audio_path": mp3_path,
                "audio_ogg_path": ogg_path,
                "transcript_path": transcript_index.get(rec_id),
                "case_path": case_index.get((term, docket)),
            }
        )

    return items


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
    from IPython.display import Audio  # noqa: PLC0415  # pragma: no cover

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
