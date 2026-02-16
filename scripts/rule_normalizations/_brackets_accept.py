# Edited by Cursor: split from _brackets_accept (lintok; no new exclusions).
"""Split-word merge normalizer (other fixes in _brackets_fixes)."""

import re


def normalize_split_word_merge(span: str) -> list[dict]:
    """Full span -> corrected text (apply only valid merges)."""
    from scripts.dictionary_loader import get_english_dictionary  # noqa: PLC0415
    from scripts.rule_normalizations.split_word_merge_scan import (  # noqa: PLC0415
        is_token_invalid_for_merge,
    )

    _word_re = re.compile(r"\S+")
    _remove_delimiters_re = re.compile(r"[^a-zA-Z0-9']")

    def _word_after_remove_delimiters(s: str) -> str:
        return _remove_delimiters_re.sub("", s)

    dic = get_english_dictionary()
    tokens_list: list[tuple[int, int, str]] = [
        (m.start(), m.end(), m.group(0)) for m in _word_re.finditer(span)
    ]
    if len(tokens_list) <= 1:
        merged = _word_after_remove_delimiters(span)
        return [{"text": merged}] if merged else [{"text": span}]
    if len(tokens_list) == 2:
        left_core = _word_after_remove_delimiters(tokens_list[0][2])
        right_core = _word_after_remove_delimiters(tokens_list[1][2])
        merged = _word_after_remove_delimiters(span)
        merged_apostrophe = (
            left_core + "'" + right_core if left_core and right_core else ""
        )
        if merged_apostrophe and merged_apostrophe.lower() in dic:
            return [{"text": merged_apostrophe}]
        if merged and merged.lower() in dic:
            return [{"text": merged}]
    n = len(tokens_list)
    out_pieces: list[str | None] = [None] * n
    for i in range(n):
        if out_pieces[i] == "":
            continue
        start_i, end_i, tok = tokens_list[i]
        if not is_token_invalid_for_merge(tok, dic):
            out_pieces[i] = tok
            continue
        if i > 0:
            prev_core = _word_after_remove_delimiters(tokens_list[i - 1][2])
            curr_core_n = _word_after_remove_delimiters(tok)
            span_a = span[tokens_list[i - 1][0] : end_i]
            word_a = _word_after_remove_delimiters(span_a)
            word_a_apostrophe = (
                prev_core + "'" + curr_core_n if prev_core and curr_core_n else ""
            )
            if word_a_apostrophe and word_a_apostrophe.lower() in dic:
                out_pieces[i - 1] = word_a_apostrophe
                out_pieces[i] = ""
                continue
            if word_a and word_a.lower() in dic:
                out_pieces[i - 1] = word_a
                out_pieces[i] = ""
                continue
        if i < n - 1:
            curr_core_n = _word_after_remove_delimiters(tok)
            next_core = _word_after_remove_delimiters(tokens_list[i + 1][2])
            span_b = span[start_i : tokens_list[i + 1][1]]
            word_b = _word_after_remove_delimiters(span_b)
            word_b_apostrophe = (
                curr_core_n + "'" + next_core if curr_core_n and next_core else ""
            )
            if word_b_apostrophe and word_b_apostrophe.lower() in dic:
                out_pieces[i] = word_b_apostrophe
                out_pieces[i + 1] = ""
                continue
            if word_b and word_b.lower() in dic:
                out_pieces[i] = word_b
                out_pieces[i + 1] = ""
                continue
        out_pieces[i] = tok
    result_tokens = [
        (out_pieces[j] or tokens_list[j][2]) for j in range(n) if out_pieces[j] != ""
    ]
    if not result_tokens:
        return [{"text": span}]
    return [{"text": " ".join(result_tokens)}]
