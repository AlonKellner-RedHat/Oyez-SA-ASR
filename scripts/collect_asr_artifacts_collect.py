# Edited by Cursor: collection logic for collect_asr_artifacts (lintok split).
"""Collect artifact candidates from transcript text and speakers."""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from scripts.collect_asr_artifacts_text import collect_from_speakers, collect_from_text

_CATEGORIES = frozenset(
    {
        "case_ids",
        "years",
        "abbreviations",
        "versus",
        "ordinals",
        "section_refs",
        "dates_month_year",
        "likely_initials",
        "acronyms",
        "currency",
        "historical_years",
        "unspoken_headers",
        "no_dot_context",
        "no_dot_citation",
        "vote_tally",
        "roman_numerals",
        "percentages",
        "decades",
        "ordinals_word",
        "statute_citation",
        "awareness_non_ascii",
        "awareness_mixed_case",
        "awareness_all_caps_long",
        "awareness_symbols",
        "awareness_brackets_parens",
        "awareness_brackets_square",
        "awareness_brackets_curly",
        "awareness_brackets_numbered",
        "awareness_brackets_angle",
        "awareness_time_like",
        "awareness_leading_decimal",
        "leading_decimal",
        "non_speech_brackets",
        "editorial_square_bracket",
        "dash_range",
        "ellipsis",
        "structural_bracket",
        "numbered_list_marker",
    }
)

_RULE_TO_CATEGORIES: dict[str, tuple[str, ...]] = {
    "case_ids": ("case_ids",),
    "versus": ("versus",),
    "title_mr": ("abbreviations",),
    "years": ("years",),
    "historical_years": ("historical_years",),
    "age": (),
    "currency": ("currency",),
    "section_refs": ("section_refs",),
    "acronyms": ("acronyms",),
    "no_negation": ("no_dot_context",),
    "no_number": ("no_dot_citation",),
    "unspoken_headers": ("unspoken_headers",),
    "vote_tally": ("vote_tally",),
    "roman_numerals": ("roman_numerals",),
    "percentages": ("percentages",),
    "decades": ("decades",),
    "ordinals_word": ("ordinals_word",),
    "statute_citation": ("statute_citation",),
}

_RULE_LABELS: dict[str, str] = {
    "no_number": '"No." (number/citation)',
    "no_negation": '"No." (negation)',
    "title_mr": "Title (Mr. / Ms.)",
    "historical_years": "Historical year (1xxx)",
    "age": "Age / small number",
    "section_refs": "Section number (legal)",
    "unspoken_headers": "Unspoken section headers",
    "vote_tally": "Vote tally (9-0, 7-2)",
    "roman_numerals": "Roman numeral (VII, IV)",
    "percentages": "Percentage (50%, 25 percent)",
    "decades": "Decade (1980s, 1930s)",
    "ordinals_word": "Ordinal (word): Fifth, Seventh",
    "statute_citation": "Statute citation (21 U.S.C., Title 18)",
}


def collect_artifacts(
    transcripts_dir: Path,
    *,
    track_paths: bool = False,
) -> dict[str, dict[str, int]] | tuple[dict[str, dict[str, int]], dict[str, set[str]]]:
    """Walk processed transcripts and collect all artifact candidates."""
    artifacts: dict[str, Counter[str]] = defaultdict(Counter)
    category_to_paths: dict[str, set[str]] = {c: set() for c in _CATEGORIES}
    for path in sorted(transcripts_dir.rglob("*.json")):
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        try:
            rel = path.relative_to(transcripts_dir)
        except ValueError:
            rel = path
        rel_str = str(rel).replace("\\", "/")
        file_artifacts: dict[str, Counter[str]] = defaultdict(Counter)
        for turn in data.get("turns") or []:
            if isinstance(turn, dict):
                collect_from_text(turn.get("text") or "", file_artifacts)
        speakers = (data.get("metadata") or {}).get("speakers") or []
        collect_from_speakers(speakers, file_artifacts)
        for k, c in file_artifacts.items():
            if c:
                artifacts[k].update(c)
                if track_paths and k in category_to_paths:
                    category_to_paths[k].add(rel_str)
    report = {k: dict(v.most_common()) for k, v in sorted(artifacts.items())}
    if track_paths:
        return report, category_to_paths
    return report


def _run_need_verification(
    _transcripts_dir: Path,
    status_path: Path,
    min_instances: int,
    category_to_paths: dict[str, set[str]],
    max_example_paths: int = 15,
) -> None:
    """Print rules with fewer than min_instances verified and example transcripts."""
    try:
        status = json.loads(status_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        status = {}
    need: list[tuple[str, int, set[str]]] = []
    for rule_id, categories in _RULE_TO_CATEGORIES.items():
        current = status.get(rule_id, 0)
        if current >= min_instances:
            continue
        paths: set[str] = set()
        for cat in categories:
            paths |= category_to_paths.get(cat, set())
        label = _RULE_LABELS.get(rule_id, rule_id)
        need.append((label, current, paths))
    if not need:
        print(
            f"All rules have at least {min_instances} verified instances.",
            file=sys.stderr,
        )
        return
    print(
        f"Rules with fewer than {min_instances} verified instances:",
        file=sys.stderr,
    )
    for label, current, paths in sorted(need, key=lambda x: (x[1], x[0])):
        n_more = min_instances - current
        print(f"  {label}: {current} verified (need {n_more} more)", file=sys.stderr)
        sorted_paths = sorted(paths)[:max_example_paths]
        for p in sorted_paths:
            print(f"    {p}", file=sys.stderr)
        if len(paths) > max_example_paths:
            print(f"    ... and {len(paths) - max_example_paths} more", file=sys.stderr)
