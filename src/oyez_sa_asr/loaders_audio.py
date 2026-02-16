# Edited by Cursor: split from loaders (lintok; no new exclusions).
"""Audio utilities (play_audio, extract_segment)."""

from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


def play_audio(audio_bytes: bytes, rate: int = 16000) -> Any:
    """Display IPython audio widget for FLAC/audio bytes."""
    from IPython.display import Audio  # noqa: PLC0415

    return Audio(data=audio_bytes, rate=rate)


def extract_segment(
    audio_path: Path,
    start_sec: float,
    end_sec: float,
) -> tuple["NDArray[np.floating[Any]]", int]:
    """Extract audio segment from FLAC file."""
    import av  # noqa: PLC0415

    if start_sec >= end_sec:
        msg = f"start_sec ({start_sec}) must be less than end_sec ({end_sec})"
        raise ValueError(msg)
    container = av.open(str(audio_path))
    stream = container.streams.audio[0]
    sample_rate = stream.rate
    frames = []
    for frame in container.decode(audio=0):
        frames.append(frame.to_ndarray())
    container.close()
    audio = np.concatenate(frames, axis=1).flatten()
    start_sample = int(start_sec * sample_rate)
    end_sample = int(end_sec * sample_rate)
    if end_sample > len(audio):
        msg = f"Segment end ({end_sec}s) exceeds audio length ({len(audio) / sample_rate:.1f}s)"
        raise ValueError(msg)
    return audio[start_sample:end_sample], sample_rate
