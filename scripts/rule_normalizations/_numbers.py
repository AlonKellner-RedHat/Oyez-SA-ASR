# Edited by Cursor: extracted from __init__.py for lintok.
"""Number, currency, symbol, and decade normalizers."""

import re

from scripts.rule_normalizations._constants import (
    ABBREV_DECADE_WORDS,
    LETTER_PRONUNCIATION,
    ORDINAL_SUFFIX_RE,
    TITLE_ABBREVIATION_MAP,
)
from scripts.rule_normalizations._digit_letter import normalize_digit_letter_mixed
from scripts.rule_normalizations._number_words import (
    digit_to_word,
    fraction_denominator_word,
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


def normalize_common_acronym(span: str) -> list[str]:
    """Spell common acronym (PhD, Ph.D.) letter-by-letter (pee aych dee)."""
    s = span.strip()
    if not s:
        return [span]
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return [span]
    words = [LETTER_PRONUNCIATION.get(c.lower(), c) for c in letters]
    return [" ".join(words)]


def normalize_short_mixed_acronym(span: str) -> list[str]:
    """Spell short mixed-case acronym (2-5 letters, half+ caps) letter-by-letter."""
    s = span.strip()
    if len(s) < 2 or len(s) > 5 or not s.isalpha():
        return [span]
    caps = sum(1 for c in s if c.isupper())
    if caps < (len(s) + 1) // 2:
        return [span]
    words = [LETTER_PRONUNCIATION.get(c.lower(), c) for c in s]
    return [" ".join(words)]


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


def _raw_currency_to_phrase(n: int) -> str:
    """Integer 0-999999 -> spoken phrase (e.g. 43000 -> forty three thousand)."""
    if n < 0:
        return str(n)
    if n < 1000:
        return number_to_words(n)
    if n < 1_000_000:
        thousands = n // 1000
        rest = n % 1000
        phrase = number_to_words(thousands) + " thousand"
        if rest:
            phrase += " " + number_to_words(rest)
        return phrase
    return str(n)


def _parse_special_currency_phrase(s: str) -> list[str] | None:  # noqa: PLR0911
    """Return [phrase dollars, phrase dollar] if s parses as currency; else None."""
    if not s or (not s.startswith("$") and not s.startswith("[")):
        return None
    if s.lower().startswith("[dollars]"):
        rest = s[9:].strip().replace(",", "")
        if rest.isdigit():
            try:
                n = int(rest)
                if 0 <= n < 1_000_000:
                    phrase = _raw_currency_to_phrase(n)
                    return [f"{phrase} dollars", f"{phrase} dollar"]
            except (ValueError, KeyError):
                pass
        return None
    rest = s.lstrip("[$]").strip()
    if rest.startswith("$"):
        rest = rest[1:].strip()
    if not rest:
        return None
    mults = ("billion", "million", "thousand", "hundred")
    mult = None
    num_part = ""
    for m in mults:
        if m in rest.lower():
            idx = rest.lower().find(m)
            num_part = rest[:idx].strip().replace(",", "")
            mult = m
            break
    if mult and num_part.isdigit():
        try:
            n = int(num_part)
            if 0 <= n < 10000:
                phrase = f"{number_to_words(n)} {mult}"
                return [f"{phrase} dollars", f"{phrase} dollar"]
        except (ValueError, KeyError):
            pass
        return None
    num_only = rest.replace(",", "").strip()
    if num_only.isdigit():
        try:
            n = int(num_only)
            if 0 <= n < 1_000_000:
                phrase = _raw_currency_to_phrase(n)
                return [f"{phrase} dollars", f"{phrase} dollar"]
        except (ValueError, KeyError):
            pass
    return None


def normalize_special_currency(span: str) -> list[str]:
    """[$] N / [dollars] N -> spoken dollars."""
    s = span.strip()
    out = _parse_special_currency_phrase(s)
    return out if out is not None else [span]


def normalize_time_of_day(span: str) -> list[str]:
    """Time of day H:MM -> eight forty; 1:00 -> one / one oh oh."""
    s = span.strip()
    if ":" not in s or s.count(":") != 1:
        return [span]
    parts = s.split(":", 1)
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        return [span]
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        return [span]
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return [span]
    hour_word = number_to_words(hour)
    if minute == 0:
        return [hour_word, f"{hour_word} oh oh"]
    min_word = digit_to_word(minute) if minute <= 9 else number_to_words(minute)
    return [f"{hour_word} {min_word}"]


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


def normalize_bracket_acronym(span: str) -> list[str]:
    """Parenthesized acronym (MPSC), (NRDC) -> letter-by-letter."""
    s = span.strip()
    if len(s) < 4 or s[0] != "(" or s[-1] != ")":
        return [span]
    inner = s[1:-1].strip()
    if len(inner) < 2:
        return [span]
    words = [LETTER_PRONUNCIATION.get(c.lower(), c) for c in inner]
    return [" ".join(words)]


def normalize_letter_roman_clause(span: str) -> list[str]:
    """(C)(iii) -> 'cee three'; letter + Roman clause."""
    s = span.strip()
    m = re.match(
        r"\(\s*([A-Za-z])\s*\)\s*\(\s*(i|ii|iii|iv|v|vi|vii|viii|ix|x|xi|xii)\s*\)",
        s,
        re.IGNORECASE,
    )
    if not m:
        return [span]
    letter = m.group(1).lower()
    roman_part = m.group(2).strip().upper()
    val = roman_to_int(roman_part)
    if val is None:
        return [span]
    letter_word = LETTER_PRONUNCIATION.get(letter, letter)
    num_word = number_to_words(val)
    return [f"{letter_word} {num_word}"]


def normalize_letter_dash_sequence(span: str) -> list[str]:
    """(R-5) or R-5 -> 'ar five'."""
    s = span.strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1].strip()
    m = re.match(r"([A-Za-z])\s*-\s*(\d+)", s)
    if not m:
        return [span]
    letter = m.group(1).lower()
    num_str = m.group(2)
    try:
        n = int(num_str)
    except ValueError:
        return [span]
    letter_word = LETTER_PRONUNCIATION.get(letter, letter)
    num_word = number_to_words(n)
    return [f"{letter_word} {num_word}"]


def normalize_percentage(span: str) -> list[str]:
    """Normalize percentage (50% or 25 percent) -> spoken form."""
    s = span.strip().replace(" ", "")
    num_str = s.rstrip("%").replace("percent", "").strip()
    if not num_str.isdigit():
        return [span]
    try:
        n = int(num_str)
        return [f"{number_to_words(n)} percent"]
    except (ValueError, KeyError):
        return [span]


def normalize_double_quote(span: str) -> list[str]:  # noqa: ARG001
    """Double-quote (open/close): same 10 spoken options for both. Span ignored."""
    return [
        "",
        "quote",
        "start quote",
        "open quote",
        "open the quote",
        "I quote",
        "and I quote",
        "end quote",
        "close quote",
        "close the quote",
    ]


def normalize_symbol_section(span: str) -> list[str]:
    """Standalone § -> section."""
    if span.strip() == "\u00a7":
        return ["section"]
    return [span]


def normalize_symbol_section_ref(span: str) -> list[str]:
    """§1519 -> section fifteen nineteen (digit pairs)."""
    s = span.strip()
    if not s.startswith("\u00a7") or len(s) < 2:
        return [span]
    digits = s[1:].strip()
    if not digits.isdigit():
        return [span]
    parts: list[str] = []
    i = 0
    while i < len(digits):
        if i + 1 < len(digits):
            two = int(digits[i : i + 2])
            if 0 <= two <= 99:
                parts.append(number_to_words(two))
                i += 2
                continue
        one = int(digits[i])
        parts.append(number_to_words(one))
        i += 1
    if not parts:
        return [span]
    return ["section " + " ".join(parts)]


def normalize_symbol_copyright(span: str) -> list[str]:
    """© -> copyright."""
    if span.strip() == "\u00a9":
        return ["copyright"]
    return [span]


def normalize_symbol_pound(span: str) -> list[str]:
    """Standalone £ -> pound."""
    if span.strip() == "\u00a3":
        return ["pound"]
    return [span]


def _currency_amount_to_words(n: int) -> str:
    """Integer amount 0-999999 -> spoken form for currency."""
    if n < 0:
        return str(n)
    if n < 1000:
        return number_to_words(n)
    if n < 1_000_000:
        thousands = n // 1000
        rest = n % 1000
        base = f"{number_to_words(thousands)} thousand"
        return base if rest == 0 else f"{base} {number_to_words(rest)}"
    return str(n)


def normalize_editorial_dollar(span: str) -> list[str]:
    """$<X> [= N] or £<X> [= N] -> X dollars/dollar or X pounds/pound."""
    s = span.strip()
    if not s.startswith(("$<", "£<")) or "> [=" not in s or "]" not in s:
        return [span]
    sym = s[0]
    end_angle = s.find(">")
    if end_angle == -1:
        return [span]
    inner = s[2:end_angle].strip()
    if not inner:
        return [span]
    if sym == "$":
        return [f"{inner} dollars", f"{inner} dollar"]
    if sym == "\u00a3":
        return [f"{inner} pounds", f"{inner} pound"]
    return [span]


def normalize_currency(span: str) -> list[str]:
    """Currency £40 / $50 -> both plural and singular."""
    s = span.strip()
    if len(s) < 2:
        return [span]
    sym = s[0]
    num_str = s[1:].replace(",", "").strip()
    if not num_str.isdigit():
        dot = num_str.find(".")
        if (
            dot != -1
            and num_str[:dot].isdigit()
            and (dot + 1 >= len(num_str) or num_str[dot + 1 :].isdigit())
        ):
            num_str = num_str[:dot]
        else:
            return [span]
    try:
        n = int(num_str)
        if n < 0 or n >= 1_000_000:
            return [span]
        words = _currency_amount_to_words(n)
        if sym == "\u00a3":
            return [f"{words} pounds", f"{words} pound"]
        if sym == "$":
            return [f"{words} dollars", f"{words} dollar"]
    except ValueError:
        pass
    return [span]


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
