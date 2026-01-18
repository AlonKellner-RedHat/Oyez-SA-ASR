# HuggingFace Dataset Architecture

> Edited by Claude

Three-tier dataset architecture for Oyez Supreme Court oral arguments.

## Datasets Overview

| Dataset | CLI Command | Purpose | Size |
|---------|-------------|---------|------|
| `oyez-sa-asr-raw` | `oyez dataset raw` | Archive of original MP3/OGG/JSON | ~340 GB |
| `oyez-sa-asr-flex` | `oyez dataset flex` | Processed FLAC + parquet refs | ~1.1 TB |
| `oyez-sa-asr-simple` | `oyez dataset simple` | Embedded audio for streaming | ~2.2 TB |

See detailed specifications in:

- [Dataset Specifications](huggingface-datasets-specs.md)
- [Versioning & Releases](huggingface-datasets-versioning.md)

## Quick Start

```bash
# Create datasets
oyez dataset raw --term 2024      # Package raw files
oyez dataset flex --term 2024     # Create FLAC + parquets
oyez dataset simple               # Embed audio (uses flex)

# Publish to HuggingFace
oyez publish raw --repo-id org/oyez-sa-asr-raw
oyez publish flex --repo-id org/oyez-sa-asr-flex
oyez publish simple --repo-id org/oyez-sa-asr-simple
```

```python
from datasets import load_dataset

# Streaming - no local storage needed
ds = load_dataset("org/oyez-sa-asr-simple", "utterances", streaming=True)

# Full recordings with on-the-fly slicing
ds = load_dataset("org/oyez-sa-asr-flex", "recordings")

# Specific term
ds = load_dataset("org/oyez-sa-asr-flex", "2024")

# Pinned version
ds = load_dataset("org/oyez-sa-asr-flex", revision="v2024.0")
```

## Choosing the Right Dataset

| Use Case | Dataset | Config |
|----------|---------|--------|
| ASR training (quick start) | `oyez-sa-asr-simple` | `utterances` |
| Custom preprocessing | `oyez-sa-asr-flex` | `utterances` |
| Full recording transcription | `oyez-sa-asr-flex` | `recordings` |
| Reproduce from scratch | `oyez-sa-asr-raw` | - |

## Size & Growth

| Dataset | Current | Annual Growth |
|---------|---------|---------------|
| `oyez-sa-asr-raw` | ~340 GB | +5-7 GB |
| `oyez-sa-asr-flex` | ~1.1 TB | +15-20 GB |
| `oyez-sa-asr-simple` | ~2.2 TB | +30-40 GB |
