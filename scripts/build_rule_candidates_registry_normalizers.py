# Edited by Cursor: thin re-export (lintok; no new exclusions).
"""Rule normalizers and labels."""

from scripts.build_rule_candidates_registry_normalizers_labels import (
    ALL_RULE_IDS,
    RULE_LABELS,
)
from scripts.build_rule_candidates_registry_normalizers_map import RULE_NORMALIZER

__all__ = ["ALL_RULE_IDS", "RULE_LABELS", "RULE_NORMALIZER"]
