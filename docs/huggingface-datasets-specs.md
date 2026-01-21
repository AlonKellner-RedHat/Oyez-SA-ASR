# HuggingFace Dataset Specifications

> Edited by Claude

Detailed specifications for each dataset tier.

## Dataset 1: `oyez-sa-asr-raw`

Archive of original scraped files for reproducibility.

```text
oyez-sa-asr-raw/
├── audio/{term}/{docket}/*.mp3, *.ogg
├── cases/{term}/{docket}.json
├── transcripts/{term}/{docket}.json
└── index/terms.json
```

| Aspect | Detail |
|--------|--------|
| Audio | Original MP3 + OGG (both preserved) |
| Metadata | Raw JSON from Oyez API |
| Size | ~340 GB |
| Updates | Append-only (yearly) |

## Dataset 2: `oyez-sa-asr-flex`

Processed FLAC recordings with parquet metadata references.
CLI: `oyez dataset flex`

```text
oyez-sa-asr-flex/
├── audio/{term}/{docket}/*.flac   # 24-bit FLAC
└── data/
    ├── recordings.parquet         # Full recording metadata
    └── utterances.parquet         # Speaker turn refs (no audio)
```

### Configs

| Config | Description | Audio |
|--------|-------------|-------|
| `recordings` | Full oral arguments | File refs |
| `utterances` | Speaker turns | Sliced on load |

### Utterances Schema

| Column | Type | Description |
|--------|------|-------------|
| term | string | Court term |
| docket | string | Docket number |
| transcript_type | string | argument/opinion |
| start_sec | float | Start timestamp |
| end_sec | float | End timestamp |
| text | string | Transcript |
| speaker_name | string | Speaker name |
| speaker_id | int | Speaker ID |

## Dataset 3: `oyez-sa-asr-simple`

Embedded audio for zero-friction streaming access.
CLI: `oyez dataset simple`

```text
oyez-sa-asr-simple/
├── oyez_sa_asr.py              # HuggingFace loading script
├── README.md                   # Dataset card
├── lt1m/data/utterances/       # < 1 minute utterances
├── lt5m/data/utterances/       # 1-5 minute utterances
└── lt30m/data/utterances/      # 5-30 minute utterances
```

### Usage

```python
from datasets import load_dataset

# Standard HuggingFace pattern
ds = load_dataset("path/to/datasets/simple", split="lt1m")
sample = ds[0]
print(sample["audio"]["array"])  # Decoded numpy array
print(sample["sentence"])        # Transcription
```

### Utterances Schema (HuggingFace-aligned)

| Column | Type | Description |
|--------|------|-------------|
| id | string | Unique utterance ID |
| audio | Audio | Embedded FLAC bytes (auto-decoded) |
| sentence | string | Transcript |
| speaker | string | Speaker name |
| duration | float | Duration in seconds |
| term | string | Court term |
| docket | string | Docket number |
| start_sec | float | Start timestamp |
| end_sec | float | End timestamp |

### Why Larger (~2× FLAC)

- Arrow row metadata per utterance
- Column value duplication
- Less efficient chunking than standalone FLAC
- Parquet index structures

## FLAC Seekability

FLAC supports efficient seeking via SEEKTABLE:

- On-the-fly segment extraction
- HTTP Range requests for cloud storage
- Memory-efficient processing
