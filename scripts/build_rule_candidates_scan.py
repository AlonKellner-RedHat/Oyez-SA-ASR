# Edited by Cursor: extracted from build_rule_candidates for lintok.
"""Run scan loop over transcripts and build (rule_id, span) groups."""

import json
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

from scripts.build_rule_candidates_registry import (
    SCANNER_REGISTRY,
)
from scripts.dictionary_loader import get_english_dictionary
from scripts.rule_normalizations.global_repeated_word_accept_scan import (
    build_global_counts_chunk,
)

_word_re = re.compile(r"\w+")


def run_global_counts_first_pass(paths_list: list[Path]) -> Counter[str]:
    """First pass: build global_counts for global_repeated_word_accept."""
    global_counts: Counter[str] = Counter()
    dic_global = get_english_dictionary()
    for path in paths_list:
        try:
            data_first = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        turns_raw_first = data_first.get("turns") or []
        valid_turns_first: list[tuple[int, str]] = []
        for turn in turns_raw_first:
            if not isinstance(turn, dict):
                continue
            text = turn.get("text") or ""
            turn_index = turn.get("index", -1)
            if turn_index < 0:
                continue
            valid_turns_first.append((turn_index, text))
        full_text_first = "\n".join(t for _, t in valid_turns_first)
        turn_boundaries_first: list[tuple[int, int, str, int]] = []
        pos_first = 0
        for turn_index, text in valid_turns_first:
            start = pos_first
            turn_boundaries_first.append((start, start + len(text), "", turn_index))
            pos_first += len(text) + 1
        global_counts += build_global_counts_chunk(
            full_text_first, turn_boundaries_first, dic_global
        )
    return global_counts


def run_scan(
    transcripts_dir: Path,
    paths_list: list[Path],
    profile_n: int,
    global_counts: Counter[str],
) -> tuple[dict, dict, dict]:
    """Scan all transcripts; return (groups, typo_corrections, profile_times)."""
    groups: dict[tuple[str, str], list[tuple[str, int, int]]] = defaultdict(list)
    typo_corrections: dict[tuple[str, int, int], str] = {}
    profile_times: dict[str, float] = defaultdict(float)

    for path in paths_list:
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        try:
            rel = path.relative_to(transcripts_dir)
        except ValueError:
            rel = path
        path_str = str(rel).replace("\\", "/")
        transcript_words: set[str] = set()
        turns_raw = data.get("turns") or []
        for turn in turns_raw:
            ttext = (turn.get("text") or "") if isinstance(turn, dict) else ""
            transcript_words.update(_word_re.findall(ttext))

        valid_turns: list[tuple[int, str]] = []
        for turn in turns_raw:
            if not isinstance(turn, dict):
                continue
            text = turn.get("text") or ""
            turn_index = turn.get("index", -1)
            if turn_index < 0:
                continue
            valid_turns.append((turn_index, text))

        full_text = "\n".join(t for _, t in valid_turns)
        turn_boundaries: list[tuple[int, int, str, int]] = []
        pos = 0
        for turn_index, text in valid_turns:
            start = pos
            turn_boundaries.append((start, start + len(text), path_str, turn_index))
            pos += len(text) + 1

        for entry in SCANNER_REGISTRY:
            if profile_n:
                t0 = time.perf_counter()
            if entry.get("scan_batch_global"):
                batch_fn = entry["scan_batch_global"]
                results = batch_fn(full_text, path_str, turn_boundaries, global_counts)
                filter_fn = entry.get("filter_result")
                for r in results:
                    rule_id, turn_index, start_index, span, _pstr = r
                    if filter_fn and not filter_fn(rule_id, span):
                        continue
                    groups[(rule_id, span)].append((path_str, turn_index, start_index))
            elif entry.get("scan_batch"):
                batch_fn = entry["scan_batch"]
                results = batch_fn(full_text, path_str, turn_boundaries)
                filter_fn = entry.get("filter_result")
                for r in results:
                    rule_id, turn_index, start_index, span, _pstr = r
                    if filter_fn and not filter_fn(rule_id, span):
                        continue
                    groups[(rule_id, span)].append((path_str, turn_index, start_index))
            else:
                scan_fn = entry["scan"]
                filter_fn = entry.get("filter_result")
                for turn_index, text in valid_turns:
                    if entry.get("transcript_words"):
                        results = scan_fn(
                            text, path_str, transcript_words=transcript_words
                        )
                    else:
                        results = scan_fn(text, path_str)
                    for r in results:
                        if len(r) == 5:
                            rule_id, start_index, span, _path_str, correction = r
                            if filter_fn and not filter_fn(rule_id, span):
                                continue
                            groups[(rule_id, span)].append(
                                (path_str, turn_index, start_index)
                            )
                            typo_corrections[(path_str, turn_index, start_index)] = (
                                correction
                            )
                        else:
                            rule_id, start_index, span, _ = r
                            if filter_fn and not filter_fn(rule_id, span):
                                continue
                            groups[(rule_id, span)].append(
                                (path_str, turn_index, start_index)
                            )
            if profile_n:
                profile_times[entry["name"]] += time.perf_counter() - t0

    return groups, typo_corrections, profile_times
