# Edited by Cursor: extracted from __init__.py for lintok.
"""Bracket unwrap, accept-identity, and small fix normalizers."""

import re

from scripts.rule_normalizations._constants import (
    LETTER_PRONUNCIATION,
    STANDARD_DASH,
    UNBRACKETED_NON_SPEECH_PHRASES,
)
from scripts.rule_normalizations._non_speech import is_non_speech_content
from scripts.rule_normalizations._number_words import number_to_words


def normalize_double_letter_parens(span: str) -> list[str]:
    """Two letters in parentheses (ph), (ab) -> pee aych, ay bee."""
    s = span.strip()
    if len(s) < 4 or s[0] != "(" or s[-1] != ")":
        return [span]
    inner = s[1:-1].strip()
    if len(inner) != 2 or not inner.isalpha():
        return [span]
    a, b = inner[0].lower(), inner[1].lower()
    if a in LETTER_PRONUNCIATION and b in LETTER_PRONUNCIATION:
        return [f"{LETTER_PRONUNCIATION[a]} {LETTER_PRONUNCIATION[b]}"]
    return [span]


def normalize_single_letter_parens(span: str) -> list[str]:
    """Single letter in parentheses (with optional spaces) -> letter pronunciation."""
    s = span.strip()
    if len(s) < 3 or s[0] != "(" or s[-1] != ")":
        return [span]
    inner = s[1:-1].strip()
    if len(inner) != 1 or not inner.isalpha():
        return [span]
    letter = inner.lower()
    if letter in LETTER_PRONUNCIATION:
        return [LETTER_PRONUNCIATION[letter]]
    return [span]


def normalize_number_parens(span: str) -> list[str]:
    """Return spoken number for number in parentheses (e.g. (32)->thirty two)."""
    s = span.strip()
    if len(s) < 3 or s[0] != "(" or s[-1] != ")":
        return [span]
    inner = s[1:-1].strip()
    if not inner.isdigit():
        return [span]
    try:
        n = int(inner)
        if 0 <= n <= 999:
            return [number_to_words(n)]
    except (ValueError, KeyError):
        pass
    return [span]


def normalize_dash(span: str) -> list[str]:  # noqa: ARG001
    """Return single standard dash for non-standard dash or dash sequence."""
    return [STANDARD_DASH]


def normalize_known_names(span: str) -> list[str]:
    """Known name patterns (McLaughlin, FitzGerald): no correction, mark as handled."""
    return [span]


def normalize_all_caps_accept(span: str) -> list[str]:
    """All-caps 6+ letters (CERCLA, ASARCO, PROMESA): no correction, mark as handled."""
    return [span]


def normalize_known_mixed_case_entities(span: str) -> list[str]:
    """Known mixed-case entities (TikTok, YouTube, LinkedIn): no correction."""
    return [span]


def normalize_pascal_case_accept(span: str) -> list[str]:
    """PascalCase 6+ letters, each segment 3+: accept (identity)."""
    return [span]


def normalize_trailing_dash_accept(span: str) -> list[str]:
    """Word + trailing dash (interruption): accept (identity)."""
    return [span]


def normalize_mixed_case_accept_6plus(span: str) -> list[str]:
    """Mixed case 6+ letters (PowerEx, RadLAX): accept (identity)."""
    return [span]


def normalize_name_pattern_di(span: str) -> list[str]:
    """Di + capitalized word (DiBona, DiMaria): accept (identity)."""
    return [span]


def normalize_bracket_sentence_unwrap(span: str) -> list[str]:
    """Bracket with 4+ words -> inner text only (unwrap)."""
    s = span.strip()
    if len(s) < 3 or s[0] not in "([" or s[-1] not in ")]":
        return [span]
    inner = s[1:-1].strip()
    return [inner]


def normalize_website_dot(span: str) -> list[str]:
    """[xxxDOTyyy] -> xxx dot yyy."""
    m = re.search(r"\[([^\]]*?)DOT([^\]]*)\]", span, re.IGNORECASE)
    if not m:
        return [span]
    left = m.group(1).strip()
    right = m.group(2).strip()
    return [f"{left} dot {right}"]


def normalize_invalid_question_mark_fix(span: str) -> list[str]:
    """\ufffd? -> ?."""
    if "\ufffd" in span and "?" in span:
        return ["?"]
    return [span]


def normalize_repeated_word_accept(span: str) -> list[str]:
    """Word that appears 2+ times in same transcript: accept (no correction)."""
    return [span]


def normalize_global_repeated_word_accept(span: str) -> list[str]:
    """Invalid 3+ letter word appearing globally 3+ times: accept (no correction)."""
    return [span]


def normalize_replacement_char_fix(span: str) -> list[str]:
    """Known U+FFFD patterns (Condé Nast) -> fixed string."""
    from scripts.rule_normalizations.replacement_char_fix_scan import (  # noqa: PLC0415
        get_replacement_char_fix,
    )

    out = get_replacement_char_fix(span.strip())
    return [out] if out is not None else [span]


def normalize_concatenated_word_split(span: str) -> list[str]:
    """Token that splits into two valid words -> 'left right'."""
    from scripts.rule_normalizations.concatenated_word_scan import (  # noqa: PLC0415
        get_concatenated_word_split_form,
    )

    out = get_concatenated_word_split_form(span.strip())
    return [out] if out else [span]


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


def normalize_single_digit_valid_word(span: str) -> list[str]:
    """Token with one digit: if remainder is in word list, return [remainder]."""
    from scripts.rule_normalizations.single_digit_valid_word_scan import (  # noqa: PLC0415
        _single_digit_remainder,
        get_single_digit_valid_words,
    )

    remainder = _single_digit_remainder(span)
    if remainder is None:
        return [span]
    words = get_single_digit_valid_words()
    if remainder.lower() in words:
        return [remainder]
    return [span]


def normalize_typo_levenshtein(span: str) -> list[str]:
    """Return span unchanged; corrections come from typo_corrections in build_rule_candidates."""
    return [span]


def normalize_inline_typo(span: str) -> list[str]:
    """word[: correction] or word, [: correction] or , [: correction] -> [correction]."""
    m = re.search(r"\w+,\s*\[\s*:\s*([^\]]+)\]", span)
    if m:
        return [m.group(1).strip() + ","]
    m = re.search(r",\s*\[\s*:\s*([^\]]+)\]", span)
    if m:
        return [", " + m.group(1).strip()]
    m = re.search(r"\w+\s*\[\s*:\s*([^\]]+)\]", span)
    if m:
        return [m.group(1).strip()]
    return [span]


def normalize_section_header(span: str) -> list[str]:  # noqa: ARG001
    """Section header (all-caps at start/end of turn): remove."""
    return [""]


def normalize_numbered_list_marker(span: str) -> list[str]:
    """Numbered list marker 1) -> one, 5) -> five."""
    s = span.strip()
    if not s.endswith(")"):
        return [span]
    num_part = s[:-1].strip()
    if not num_part.isdigit():
        return [span]
    try:
        n = int(num_part)
        if 1 <= n <= 99:
            return [number_to_words(n)]
    except (ValueError, KeyError):
        pass
    return [span]


def normalize_non_speech_brackets(span: str) -> list[str]:
    """Return empty string for (Inaudible), [Laughter], etc.; else identity."""
    s = span.strip().rstrip(".").strip()
    phrase_norm = " ".join(s.lower().split())
    if phrase_norm in UNBRACKETED_NON_SPEECH_PHRASES:
        return [""]
    if len(s) < 3 or s[0] not in "([{" or s[-1] not in ")]}":
        return [span]
    content = s[1:-1].strip().rstrip(".").strip()
    content_norm = " ".join(content.lower().split())
    if is_non_speech_content(content_norm):
        return [""]
    return [span]
