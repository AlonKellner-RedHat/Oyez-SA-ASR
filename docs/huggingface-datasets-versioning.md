# HuggingFace Dataset Versioning

> Edited by Claude

Versioning strategy and annual release workflow.

## Version Naming

```text
v{year}.{patch}

v2024.0  - Initial release with 2024 term
v2024.1  - Bug fix (transcript corrections)
v2025.0  - Add 2025 term
```

## Data Structure

Sharded by term for incremental updates:

```text
data/utterances/
├── 1955.parquet
├── 1956.parquet
├── ...
└── 2024.parquet    # Added in v2024.0
```

## Loading Versions

```python
# Latest
ds = load_dataset("org/oyez-sa-asr")

# Pinned version
ds = load_dataset("org/oyez-sa-asr", revision="v2023.0")

# Specific terms
ds = load_dataset("org/oyez-sa-asr", "utterances",
                  data_files="data/utterances/202*.parquet")
```

## Term Configs

```python
ds = load_dataset("org/oyez-sa-asr", "all")     # All terms
ds = load_dataset("org/oyez-sa-asr", "modern")  # 2000+
ds = load_dataset("org/oyez-sa-asr", "recent")  # Last 5 terms
ds = load_dataset("org/oyez-sa-asr", "2024")    # Single term
```

## Annual Release Workflow

### Timeline

| Month | Activity |
|-------|----------|
| October | Term's oral arguments complete |
| November | Scrape and process |
| December | QA and release |

### Release Commands

```bash
# 1. Scrape & process new term
oyez scrape cases --terms 2025
oyez scrape transcripts --terms 2025
oyez scrape audio --terms 2025
oyez process audio --terms 2025
oyez process transcripts --terms 2025

# 2. Upload and tag each dataset
huggingface-cli upload org/oyez-sa-asr-raw audio/2025 audio/2025
git tag v2025.0 && git push --tags

huggingface-cli upload org/oyez-sa-asr audio/2025 audio/2025
git tag v2025.0 && git push --tags

# 3. Update streaming dataset
git tag v2025.0 && git push --tags
```

## CHANGELOG Template

```markdown
## [v2025.0] - 2025-12-01
### Added
- 2025 term: 72 arguments, 4,320 utterances

### Stats
- Recordings: 5,100 (+72)
- Utterances: 510,000 (+4,320)
- Storage: raw 345GB, flac 620GB, stream 1.25TB
```
