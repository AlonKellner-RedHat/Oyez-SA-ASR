# Edited by Cursor: extracted from __init__.py for lintok.
"""Latin extended: simple_map + uroman romanization."""

import os
import subprocess
import unicodedata
from functools import lru_cache

from scripts.rule_normalizations._constants import LATIN_UROMAN_LANGS


def latin_simple_map(span: str) -> str:
    """Map Latin accented characters to ASCII (e.g. à->a, é->e) via NFD + strip combining."""
    s = span.strip()
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def _uroman_romanize_impl(text: str, lang: str | None = None) -> str | None:
    """Romanize text via uroman (Python package or CLI). Returns None if uroman unavailable or fails."""
    try:
        import uroman  # noqa: PLC0415

        if lang is not None:
            return uroman.romanize(text, lang=lang)
        return uroman.romanize(text)
    except Exception:  # noqa: S110
        pass
    try:
        cmd = ["uroman", "-l", lang] if lang else ["uroman"]
        result = subprocess.run(  # noqa: S603
            cmd,
            input=text,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):  # noqa: S110
        pass
    return None


_UROMAN_CACHE_MAX = 65536


@lru_cache(maxsize=_UROMAN_CACHE_MAX)
def _uroman_romanize(text: str, lang: str | None = None) -> str | None:
    """Return cached uroman result; use (text, lang) as cache key."""
    return _uroman_romanize_impl(text, lang)


def _latin_uroman_langs() -> tuple[str, ...]:
    """Allow skipping per-language uroman (only default) for faster pipeline. Set UROMAN_FAST=1."""
    if os.environ.get("UROMAN_FAST"):
        return ()
    return LATIN_UROMAN_LANGS


def normalize_latin_batch(spans: list[str]) -> list[list[dict]]:
    r"""Run uroman once per language over \"\\n\".join(spans); return same shape as [normalize_latin(s) for s in spans]."""
    if not spans:
        return []
    by_simple = [latin_simple_map(s) for s in spans]
    unified = "\n".join(spans)
    lang_list: tuple[str | None, ...] = (None, *_latin_uroman_langs())
    by_lang_lines: list[list[str]] = []
    for lang in lang_list:
        out = _uroman_romanize_impl(unified, lang)
        if out is None:
            by_lang_lines.append([])
            continue
        lines = out.split("\n")
        if len(lines) != len(spans):
            lines = []
            for s in spans:
                r = _uroman_romanize_impl(s, lang)
                lines.append(r.strip() if r else "")
        by_lang_lines.append(lines)
    result: list[list[dict]] = []
    for i in range(len(spans)):
        out: list[dict] = []
        simple = by_simple[i]
        out.append({"text": simple, "method": "simple_map"})
        seen: set[str] = {simple}
        method_names = ["uroman"] + [f"uroman_{lc}" for lc in _latin_uroman_langs()]
        for lang_idx, method in enumerate(method_names):
            if lang_idx >= len(by_lang_lines) or not by_lang_lines[lang_idx]:
                continue
            line = by_lang_lines[lang_idx][i].strip()
            if line and line not in seen:
                seen.add(line)
                out.append({"text": line, "method": method})
        result.append(out)
    return result


def normalize_latin(span: str) -> list[dict]:
    """Latin extended: multiple corrections (simple_map, uroman, uroman_<lcode>). Returns list of {text, method}."""
    return normalize_latin_batch([span])[0]
