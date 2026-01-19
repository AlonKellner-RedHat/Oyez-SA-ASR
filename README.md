# Oyez SA-ASR

[![CI Status](https://github.com/AlonKellner/oyez_sa_asr/actions/workflows/ci-orchestrator.yml/badge.svg)](https://github.com/AlonKellner/oyez_sa_asr/actions/workflows/ci-orchestrator.yml)
[![Docs Status](https://github.com/AlonKellner/oyez_sa_asr/actions/workflows/docs.yml/badge.svg)](https://github.com/AlonKellner/oyez_sa_asr/actions/workflows/docs.yml)  

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Py Stack: astral.sh](https://img.shields.io/badge/py%20stack-astral.sh-30173d.svg)](https://github.com/astral-sh)
[![Open in Dev Containers](https://img.shields.io/static/v1?label=devcontainer&message=Open&color=blue)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/AlonKellner/oyez_sa_asr)

**Speaker-Attributed ASR dataset from U.S. Supreme Court oral arguments.**

This tool scrapes, processes, and packages audio recordings and transcripts
from [Oyez.org](https://www.oyez.org) into HuggingFace-compatible datasets.

## Quick Start

### Installation

```bash
# Clone and enter the repository
git clone https://github.com/AlonKellner/oyez_sa_asr.git
cd oyez_sa_asr

# Install dependencies (requires uv)
uv sync
```

### Run the Full Pipeline

Process a specific court term (recommended for testing):

```bash
# Process the 2024 term (most recent, smaller dataset)
uv run oyez pipeline run --term 2024
```

Process multiple terms:

```bash
# Process 2023 and 2024 terms
uv run oyez pipeline run --term 2024 --term 2023
```

The pipeline runs these steps automatically:

1. **Scrape** - Download case index, details, transcripts, and audio
2. **Process** - Parse data, convert audio to FLAC, aggregate speakers
3. **Dataset** - Create HuggingFace-compatible datasets

### Use the Datasets

After running the pipeline, explore your datasets:

```bash
# Demo the simple dataset (embedded audio, ready for streaming)
python examples/demo_simple_dataset.py

# Demo the flex dataset (FLAC audio + parquet metadata)
python examples/demo_flex_dataset.py

# Demo the raw dataset (original source files)
python examples/demo_raw_dataset.py
```

View statistics:

```bash
uv run oyez stats audio
uv run oyez stats transcripts
uv run oyez stats speakers
```

## Pipeline Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                        oyez pipeline run                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 1: Scraping                                               │
│  ┌──────────┐   ┌──────────┐   ┌────────────┐   ┌─────────┐     │
│  │  Index   │ → │  Cases   │ → │Transcripts │ → │  Audio  │     │
│  └──────────┘   └──────────┘   └────────────┘   └─────────┘     │
│       ↓              ↓               ↓               ↓          │
│  .cache/index  .cache/cases  .cache/transcripts  .cache/audio   │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 2: Processing                                             │
│  ┌──────────┐   ┌──────────┐   ┌────────────┐   ┌─────────┐     │
│  │  Cases   │ → │Transcripts│ → │   Audio   │ → │Speakers │     │
│  └──────────┘   └──────────┘   └────────────┘   └─────────┘     │
│       ↓              ↓               ↓               ↓          │
│   data/cases   data/transcripts   data/audio    data/speakers   │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 3: Dataset Creation                                       │
│  ┌──────────┐   ┌──────────┐   ┌────────────┐                   │
│  │   Raw    │   │   Flex   │   │   Simple   │                   │
│  └──────────┘   └──────────┘   └────────────┘                   │
│       ↓              ↓               ↓                          │
│  datasets/raw  datasets/flex  datasets/simple                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Dataset Types

| Dataset | Contents | Best For |
|---------|----------|----------|
| **Raw** | Original MP3/OGG audio + JSON metadata | Archival, custom processing |
| **Flex** | FLAC audio + parquet metadata | Training pipelines, random access |
| **Simple** | Audio embedded in parquet shards | Streaming, quick experimentation |

## Individual Commands

### Scraping

```bash
oyez scrape index                    # Fetch case listing
oyez scrape cases --term 2024        # Fetch case details
oyez scrape transcripts --term 2024  # Fetch transcripts
oyez scrape audio --term 2024        # Download audio files
```

### Processing

```bash
oyez process index                   # Parse cached index
oyez process cases --term 2024       # Parse case details
oyez process transcripts --term 2024 # Parse transcripts
oyez process audio --term 2024       # Convert to FLAC
oyez process speakers --term 2024    # Aggregate speaker data
```

### Dataset Creation

```bash
oyez dataset raw --term 2024         # Create raw dataset
oyez dataset flex --term 2024        # Create flex dataset
oyez dataset simple                  # Create simple dataset
```

### Statistics

```bash
oyez stats audio                     # Audio file statistics
oyez stats transcripts               # Transcript statistics
oyez stats speakers                  # Speaker statistics
oyez stats cases                     # Case statistics
```

### Utilities

```bash
oyez clear audio                     # Clear audio cache
oyez clear all                       # Clear everything
oyez publish flex --repo-id org/name # Publish to HuggingFace
```

## Configuration

Pipeline options:

```bash
oyez pipeline run --help

Options:
  --term, -T         Filter to specific court term(s)
  --skip-scrape      Skip scraping (use cached data)
  --skip-process     Skip processing steps
  --skip-dataset     Skip dataset creation
```

## Documentation

- [HuggingFace Dataset Architecture](docs/huggingface-datasets.md)
- [Dataset Specifications](docs/huggingface-datasets-specs.md)
- [Oyez API Overview](docs/oyez_api_overview.md)
- [Audio Format Details](docs/oyez_audio_formats.md)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md).

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Data sourced from [Oyez.org](https://www.oyez.org)
- Built with [astral.sh](https://github.com/astral-sh) Python tooling
- Created with [cookiecutter-pyproject-2025](https://github.com/AlonKellner/cookiecutter-pyproject-2025)

---

Made with love by the Oyez SA-ASR community
