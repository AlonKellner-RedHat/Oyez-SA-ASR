# Edited by Cursor: split from loaders (lintok; no new exclusions).
"""HuggingFace dataset loaders."""

from pathlib import Path
from typing import Any

from oyez_sa_asr._loaders_constants import (
    DEFAULT_FLEX_DIR,
    DEFAULT_RAW_DIR,
    DEFAULT_SIMPLE_DIR,
)


def _get_simple_features() -> Any:
    """Get Features schema for simple dataset."""
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


try:
    SIMPLE_FEATURES = _get_simple_features()
except ImportError:
    SIMPLE_FEATURES = None


def load_simple_hf(
    split: str = "lt1m",
    data_dir: Path | None = None,
    *,
    streaming: bool = False,
) -> Any:
    """Load simple dataset as HuggingFace Dataset with audio decoding."""
    from datasets import load_dataset  # noqa: PLC0415

    base = data_dir or DEFAULT_SIMPLE_DIR
    split_dir = base / split / "data" / "utterances"
    if not split_dir.exists():
        raise FileNotFoundError(
            f"Dataset not found at {split_dir}. Run 'oyez dataset simple' first."
        )
    features = _get_simple_features()
    parquet_pattern = str(split_dir / "*.parquet")
    return load_dataset(
        "parquet",
        data_files=parquet_pattern,
        split="train",
        streaming=streaming,
        features=features,
    )


def load_raw_hf(
    data_dir: Path | None = None,
    *,
    streaming: bool = False,
) -> Any:
    """Load raw dataset as HuggingFace Dataset via parquet auto-discovery."""
    from datasets import load_dataset  # noqa: PLC0415

    base = data_dir or DEFAULT_RAW_DIR
    return load_dataset(str(base), streaming=streaming)


def load_flex_hf(
    config: str = "recordings",
    data_dir: Path | None = None,
    *,
    streaming: bool = False,
) -> Any:
    """Load flex dataset as HuggingFace Dataset via parquet auto-discovery."""
    from datasets import load_dataset  # noqa: PLC0415

    base = data_dir or DEFAULT_FLEX_DIR
    return load_dataset(str(base), config, streaming=streaming)
