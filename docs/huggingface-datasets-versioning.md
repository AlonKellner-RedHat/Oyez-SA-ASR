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
ds = load_dataset("org/oyez-sa-asr-flex")

# Pinned version
ds = load_dataset("org/oyez-sa-asr-flex", revision="v2023.0")

# Specific terms
ds = load_dataset("org/oyez-sa-asr-flex", "utterances",
                  data_files="data/utterances/202*.parquet")
```

## Term Configs

```python
ds = load_dataset("org/oyez-sa-asr-flex", "all")     # All terms
ds = load_dataset("org/oyez-sa-asr-flex", "modern")  # 2000+
ds = load_dataset("org/oyez-sa-asr-flex", "recent")  # Last 5 terms
ds = load_dataset("org/oyez-sa-asr-flex", "2024")    # Single term
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
oyez scrape cases --term 2025
oyez scrape transcripts --term 2025
oyez scrape audio --term 2025
oyez process cases --term 2025
oyez process transcripts --term 2025
oyez process audio --term 2025

# 2. Create datasets
oyez dataset raw --term 2025
oyez dataset flex --term 2025
oyez dataset simple

# 3. Publish to HuggingFace
oyez publish raw --repo-id org/oyez-sa-asr-raw
oyez publish flex --repo-id org/oyez-sa-asr-flex
oyez publish simple --repo-id org/oyez-sa-asr-simple
```

## CHANGELOG Template

```markdown
## [v2025.0] - 2025-12-01
### Added
- 2025 term: 72 arguments, 4,320 utterances

### Stats
- Recordings: 5,100 (+72)
- Utterances: 510,000 (+4,320)
- Storage: raw 345GB, flex 1.1TB, simple 2.2TB
```
