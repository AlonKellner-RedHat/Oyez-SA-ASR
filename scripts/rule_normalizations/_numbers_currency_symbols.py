# Edited by Cursor: split from _numbers (lintok; no new exclusions).
"""Currency and symbol normalizers."""

from scripts.rule_normalizations._number_words import number_to_words


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
