# HuggingFace Dataset Architecture

> Edited by Claude

Three-tier dataset architecture for Oyez Supreme Court oral arguments.

## Datasets Overview

| Dataset | Purpose | Size |
|---------|---------|------|
| `oyez-sa-asr-raw` | Archive of original MP3/OGG/JSON | ~340 GB |
| `oyez-sa-asr` | Processed FLAC + metadata refs | ~600 GB |
| `oyez-sa-asr-stream` | Embedded audio for streaming | ~1.2 TB |

See detailed specifications in:

- [Dataset Specifications](huggingface-datasets-specs.md)
- [Versioning & Releases](huggingface-datasets-versioning.md)

## Quick Start

```python
from datasets import load_dataset

# Streaming - no local storage needed
ds = load_dataset("org/oyez-sa-asr-stream", "utterances", streaming=True)

# Full recordings with on-the-fly slicing
ds = load_dataset("org/oyez-sa-asr", "recordings")

# Specific term
ds = load_dataset("org/oyez-sa-asr", "2024")

# Pinned version
ds = load_dataset("org/oyez-sa-asr", revision="v2024.0")
```

## Choosing the Right Dataset

| Use Case | Dataset | Config |
|----------|---------|--------|
| ASR training (quick start) | `oyez-sa-asr-stream` | `utterances` |
| Custom preprocessing | `oyez-sa-asr` | `utterances` |
| Full recording transcription | `oyez-sa-asr` | `recordings` |
| Reproduce from scratch | `oyez-sa-asr-raw` | - |

## Size & Growth

| Dataset | Current | Annual Growth |
|---------|---------|---------------|
| `oyez-sa-asr-raw` | ~340 GB | +5-7 GB |
| `oyez-sa-asr` | ~600 GB | +10-12 GB |
| `oyez-sa-asr-stream` | ~1.2 TB | +20-25 GB |
