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

## Dataset 2: `oyez-sa-asr`

Processed FLAC recordings with metadata references.

```text
oyez-sa-asr/
├── audio/{term}/{docket}.flac   # 24-bit FLAC
└── data/
    ├── recordings.parquet       # Full recording metadata
    ├── utterances.parquet       # Speaker turn refs (no audio)
    ├── segments.parquet         # Fixed-length chunk refs
    └── words.parquet            # Word-level alignments
```

### Configs

| Config | Description | Audio |
|--------|-------------|-------|
| `recordings` | Full oral arguments | File refs |
| `utterances` | Speaker turns | Sliced on load |
| `segments` | 30-sec chunks | Sliced on load |
| `words` | Word alignments | None |

### Utterances Schema

| Column | Type | Description |
|--------|------|-------------|
| audio_path | string | Reference to FLAC |
| start_sec | float | Start timestamp |
| end_sec | float | End timestamp |
| text | string | Transcript |
| speaker | string | Speaker name |
| speaker_role | string | justice/advocate/other |

## Dataset 3: `oyez-sa-asr-stream`

Embedded audio for zero-friction streaming access.

```text
oyez-sa-asr-stream/
└── data/
    ├── utterances/train-*.parquet   # Audio embedded
    ├── segments_30s/train-*.parquet
    └── segments_10s/train-*.parquet
```

### Utterances Schema

| Column | Type | Description |
|--------|------|-------------|
| audio | Audio | Embedded FLAC bytes |
| text | string | Transcript |
| speaker | string | Speaker name |
| speaker_role | string | Role category |
| case_id | string | Docket number |
| term | string | Court term |

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
