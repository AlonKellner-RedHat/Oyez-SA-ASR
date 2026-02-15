# Edited by Cursor (merge rule: invalid token; full span when at least one merge valid).
# awareness_single_letter: single letters invalid for merge except a,i,v,x.
"""Scan for invalid token with at least one valid merge (prev+curr or curr+next); emit full span.

Performance note: This rule is the bottleneck (≈40% of total scan time per docs/rule_timing_report.md).
Consider optimizing dictionary lookups if performance becomes critical. Edited by Cursor.
"""

import re

from scripts.dictionary_loader import get_english_dictionary

# Single letters valid for merge (same allowlist as build_awareness_candidates). Edited by Cursor.
SINGLE_LETTER_MERGE_ALLOWED = frozenset({"a", "i", "v", "x"})

# Same tokenization as awareness: non-whitespace runs.
WORD_RE = re.compile(r"\S+")

# Remove delimiters (space, comma, period, etc.) to get candidate word. Edited by Cursor.
_REMOVE_DELIMITERS_RE = re.compile(r"[^a-zA-Z0-9']")


def _word_after_remove_delimiters(span: str) -> str:
    """Return span with delimiters removed (letters, digits, apostrophe only)."""
    return _REMOVE_DELIMITERS_RE.sub("", span)


def is_token_invalid_for_merge(
    token: str, dictionary: set[str] | frozenset[str]
) -> bool:
    """Return True if token should be considered invalid for split-word-merge (so merge is attempted).

    Lowercase single letters except a,i,v,x are always invalid. Edited by Cursor.
    """
    if len(token) == 1 and token.islower() and token.isalpha():
        return token not in SINGLE_LETTER_MERGE_ALLOWED
    return token.lower() not in dictionary


def scan_turn_split_word_merge(
    text: str,
    path_str: str = "",
) -> list[tuple[str, int, str, str]]:
    """Emit (split_word_merge, start_index, full_span, path_str) for invalid tokens with at least one valid merge."""
    result: list[tuple[str, int, str, str]] = []
    dic = get_english_dictionary()
    tokens: list[tuple[int, int, str]] = []
    for m in WORD_RE.finditer(text):
        tokens.append((m.start(), m.end(), m.group(0)))
    # start_full -> span_full (keep longest span per start for dedupe). Edited by Cursor.
    seen: dict[int, str] = {}
    for i in range(len(tokens)):
        start_i, end_i, tok = tokens[i]
        if not is_token_invalid_for_merge(tok, dic):
            continue
        # Current token is invalid; consider merge with previous and with next (concatenated or apostrophe). Edited by Cursor.
        curr_core = _word_after_remove_delimiters(tok)
        valid_prev = False
        valid_next = False
        if i > 0:
            span_a = text[tokens[i - 1][0] : end_i]
            word_a = _word_after_remove_delimiters(span_a)
            prev_core = _word_after_remove_delimiters(tokens[i - 1][2])
            word_apostrophe_prev = (
                prev_core + "'" + curr_core if prev_core and curr_core else ""
            )
            if (word_a and word_a.lower() in dic) or (
                word_apostrophe_prev and word_apostrophe_prev.lower() in dic
            ):
                valid_prev = True
        if i < len(tokens) - 1:
            span_b = text[start_i : tokens[i + 1][1]]
            word_b = _word_after_remove_delimiters(span_b)
            next_core = _word_after_remove_delimiters(tokens[i + 1][2])
            word_apostrophe_next = (
                curr_core + "'" + next_core if curr_core and next_core else ""
            )
            if (word_b and word_b.lower() in dic) or (
                word_apostrophe_next and word_apostrophe_next.lower() in dic
            ):
                valid_next = True
        if not valid_prev and not valid_next:
            continue
        # Full span: from start of previous token to end of next token (when both exist).
        start_full = tokens[i - 1][0] if i > 0 else start_i
        end_full = tokens[i + 1][1] if i < len(tokens) - 1 else end_i
        span_full = text[start_full:end_full]
        # Keep longest span per start_index (avoid emitting both "thank s" and "thank s man").
        if start_full not in seen or len(span_full) > len(seen[start_full]):
            seen[start_full] = span_full
    # Build result; seen is now start_full -> span_full (longest per start).
    for start_full, span_full in seen.items():
        result.append(("split_word_merge", start_full, span_full, path_str))
    return result
