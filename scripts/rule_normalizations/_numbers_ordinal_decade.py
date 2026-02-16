# Edited by Cursor: split from _numbers (lintok; no new exclusions).
"""Ordinal, year, vote_tally, roman, decade normalizers."""

from scripts.rule_normalizations._constants import (
    ABBREV_DECADE_WORDS,
    LETTER_PRONUNCIATION,
    ORDINAL_SUFFIX_RE,
    TITLE_ABBREVIATION_MAP,
)
from scripts.rule_normalizations._number_words import (
    digit_to_word,
    number_to_ordinal,
    number_to_words,
    roman_to_int,
)


def normalize_leading_decimal(span: str) -> list[str]:
    """.06 -> point oh six; .31 -> point three one / point thirty one; exclude .YYYY."""
    s = span.strip()
    if not s.startswith(".") or len(s) < 2 or not s[1:].isdigit():
        return [span]
    digits = s[1:]
    if len(digits) == 4 and (digits.startswith("1") or digits.startswith("20")):
        return [span]
    parts = ["oh" if d == "0" else digit_to_word(int(d)) for d in digits]
    primary = "point " + " ".join(parts)
    result: list[str] = [primary]
    if len(digits) == 2 and 10 <= int(digits) <= 99:
        result.append("point " + number_to_words(int(digits)))
    elif len(digits) >= 3:
        tail = int(digits[-2:])
        if 10 <= tail <= 99:
            prefix = " ".join(
                "oh" if d == "0" else digit_to_word(int(d)) for d in digits[:-2]
            )
            result.append("point " + prefix + " " + number_to_words(tail))
    return result


def normalize_ordinal(span: str) -> list[str]:
    """Return spoken ordinal for 37th, 3rd, etc."""
    s = span.strip()
    m = ORDINAL_SUFFIX_RE.fullmatch(s)
    if not m:
        return [span]
    try:
        n = int(m.group(1))
        if 1 <= n <= 99:
            return [number_to_ordinal(n)]
    except (ValueError, KeyError, IndexError):
        pass
    return [span]


def normalize_title_abbreviation(span: str) -> list[str]:
    """Title abbreviation (Mr., Dr., Mrs., Jr., etc.) -> spoken form."""
    s = span.strip().rstrip(".").lower()
    if not s:
        return [span]
    expanded = TITLE_ABBREVIATION_MAP.get(s)
    if expanded is not None:
        return [expanded]
    return [span]


def normalize_vote_tally(span: str) -> list[str]:
    """Normalize vote tally '9-0' -> ['nine to zero']."""
    parts = span.strip().split("-")
    if len(parts) != 2 or len(parts[0]) != 1 or len(parts[1]) != 1:
        return [span]
    try:
        a, b = int(parts[0]), int(parts[1])
        if 0 <= a <= 9 and 0 <= b <= 9:
            return [f"{digit_to_word(a)} to {digit_to_word(b)}"]
    except ValueError:
        pass
    return [span]


def normalize_year(span: str) -> list[str]:
    """Normalize four-digit year -> spoken form (e.g. 1999 -> nineteen ninety nine)."""
    s = span.strip()
    if len(s) != 4 or not s.isdigit():
        return [span]
    try:
        n = int(s)
        if 1900 <= n <= 2099:
            c, d = divmod(n, 100)
            if d == 0:
                return [f"{number_to_words(c)} hundred"]
            return [f"{number_to_words(c)} {number_to_words(d)}"]
    except (ValueError, KeyError):
        pass
    return [span]


def normalize_roman_numeral(span: str) -> list[str]:
    """Normalize Roman numeral (II-XII) -> spoken number."""
    val = roman_to_int(span.strip().upper())
    if val is None:
        return [span]
    return [number_to_words(val)]


def normalize_roman_parens(span: str) -> list[str]:
    """Roman (i)-(xii) -> number word + letter forms."""
    s = span.strip()
    if len(s) < 3 or s[0] != "(" or s[-1] != ")":
        return [span]
    inner = s[1:-1].strip().upper()
    val = roman_to_int(inner)
    if val is None:
        return [span]
    out: list[str] = []
    num_word = number_to_words(val)
    out.append(num_word)
    letter_spell = " ".join(LETTER_PRONUNCIATION.get(c.lower(), c) for c in inner)
    if letter_spell and letter_spell not in out:
        out.append(letter_spell)
    if inner == "II":
        out.append("double eye")
    elif inner == "III":
        out.append("triple eye")
    elif inner == "VII":
        out.append("vee double eye")
    elif inner == "VIII":
        out.append("vee triple eye")
    elif inner == "XII":
        out.append("ex double eye")
    return list(dict.fromkeys(out))


def normalize_decade(span: str) -> list[str]:
    """Normalize decade (1980s, 20s) -> spoken form (nineteen eighties, twenties)."""
    s = span.strip()
    result: list[str] = [span]
    if not s.endswith("s"):
        return result
    base = s[:-1]
    if not base.isdigit():
        return result
    try:
        n = int(base)
        if len(s) == 3:
            if 0 <= n <= 99:
                tens = n // 10
                result = [ABBREV_DECADE_WORDS[tens]]
        elif len(s) == 5 and 1800 <= n <= 2099:
            c, d = divmod(n, 100)
            if d == 0:
                result = [f"{number_to_words(c)} hundreds"]
            else:
                tens = d // 10
                if tens in {0, 1}:
                    result = [f"{number_to_words(c)} {number_to_words(d)}s"]
                else:
                    tens_word = (
                        "twenties",
                        "thirties",
                        "forties",
                        "fifties",
                        "sixties",
                        "seventies",
                        "eighties",
                        "nineties",
                    )[tens - 2]
                    result = [f"{number_to_words(c)} {tens_word}"]
    except (ValueError, KeyError, IndexError):
        pass
    return result
