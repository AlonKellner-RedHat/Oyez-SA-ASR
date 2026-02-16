# Edited by Cursor: split from loaders (lintok; no new exclusions).
"""Path constants for dataset loaders."""

from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_RAW_DIR = _PROJECT_ROOT / "datasets" / "raw"
DEFAULT_FLEX_DIR = _PROJECT_ROOT / "datasets" / "flex"
DEFAULT_SIMPLE_DIR = _PROJECT_ROOT / "datasets" / "simple"
