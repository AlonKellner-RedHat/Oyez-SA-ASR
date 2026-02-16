# Edited by Cursor: split from _numbers (lintok; no new exclusions).
"""Fraction, half-number, dual-notation normalizers."""

from scripts.rule_normalizations._constants import LETTER_PRONUNCIATION
from scripts.rule_normalizations._digit_letter import normalize_digit_letter_mixed
from scripts.rule_normalizations._number_words import (
    fraction_denominator_word,
    number_to_words,
)


def _normalize_dual_token(token: str, citation: str) -> list[str]:
    """Normalize a single token from dual notation content."""
    t = token.strip()
    if not t:
        return [""]
    if t.lower() == "e@l":
        return ["ee"]
    if t.lower() == "v@l" and citation.strip().rstrip(".").lower() == "v":
        return ["versus", "vee"]
    if len(t) == 1 and t.isalpha():
        return [LETTER_PRONUNCIATION.get(t.lower(), t)]
    if t.replace("@", "").replace("-", "").isdigit() or (
        any(c.isdigit() for c in t) and any(c.isalpha() for c in t)
    ):
        out = normalize_digit_letter_mixed(t.replace("@", ""))
        if out and out != [t]:
            return out
    return [t]


def normalize_half_number(span: str) -> list[str]:
    """Return N and a half percent/years/unit for N½%, N ½ years, or N ½ times."""
    s = span.strip()
    half = "\u00bd"
    if half not in s:
        return [span]
    idx = s.find(half)
    num_part = s[:idx].strip()
    rest = s[idx + 1 :].strip().lstrip("%")
    if not num_part.isdigit():
        return [span]
    try:
        n = int(num_part)
        if n < 0 or n > 999:
            return [span]
    except ValueError:
        return [span]
    word = number_to_words(n)
    if "years" in rest.lower():
        suffix = "years"
    elif rest.lower().strip() == "" or "%" in rest:
        suffix = "percent"
    else:
        suffix = rest.strip()
    return [f"{word} and a half {suffix}"]


def normalize_fraction(span: str) -> list[str]:  # noqa: PLR0911
    """Slash fraction (1/3, 2/5) and standalone ½, ¼, ¾ -> spoken form."""
    s = span.strip()
    half = "\u00bd"
    quarter = "\u00bc"
    three_quarters = "\u00be"
    if s == half:
        return ["one half", "a half"]
    if s == quarter:
        return ["one fourth", "one quarter"]
    if s == three_quarters:
        return ["three fourths", "three quarters"]
    if "/" not in s:
        return [span]
    parts = s.split("/", 1)
    if len(parts) != 2:
        return [span]
    try:
        num, denom = int(parts[0].strip()), int(parts[1].strip())
    except ValueError:
        return [span]
    if denom == 0:
        return [span]
    denom_word = fraction_denominator_word(denom, num)
    if denom_word is None:
        return [span]
    if num < 1:
        return [span]
    base = f"{number_to_words(num)} {denom_word}"
    result = [base]
    if num == 1:
        singular = fraction_denominator_word(denom, 1)
        if singular:
            result.append(f"a {singular}")
    return result


def normalize_dual_notation(span: str) -> list[str]:
    """<X> [= Y], <X> [citation], [<X>]: normalize angle content X."""
    s = span.strip()
    if s.startswith("[") and "<" in s and ">" in s:
        start_angle = s.index("<")
        end_angle = s.index(">")
        content = s[start_angle + 1 : end_angle].strip()
        if content:
            tokens = content.split()
            option_lists: list[list[str]] = [[]]
            for token in tokens:
                opts = _normalize_dual_token(token, "")
                if len(opts) == 1:
                    for o in option_lists:
                        o.append(opts[0])
                else:
                    new_option_lists = []
                    for existing in option_lists:
                        for opt in opts:
                            new_option_lists.append([*existing, opt])
                    option_lists = new_option_lists
            result = [" ".join(o).strip() for o in option_lists if any(o)]
            return result if result else [span]
        return [span]
    if not s.startswith("<") or ">" not in s or "]" not in s:
        return [span]
    end_angle = s.index(">")
    content = s[1:end_angle].strip()
    bracket_start = s.find("[", end_angle)
    if bracket_start == -1:
        return [span]
    bracket_content = s[bracket_start + 1 : s.index("]", bracket_start)].strip()
    citation = ""
    if "=" in bracket_content:
        eq = bracket_content.find("=")
        citation = bracket_content[eq + 1 :].strip()
    if not content:
        return [span]
    tokens = content.split()
    option_lists = [[]]
    for token in tokens:
        opts = _normalize_dual_token(token, citation)
        if len(opts) == 1:
            for o in option_lists:
                o.append(opts[0])
        else:
            new_option_lists = []
            for existing in option_lists:
                for opt in opts:
                    new_option_lists.append([*existing, opt])
            option_lists = new_option_lists
    result = [" ".join(o).strip() for o in option_lists if any(o)]
    return result if result else [span]
