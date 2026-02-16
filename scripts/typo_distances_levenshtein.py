# Edited by Cursor: split from typo_distances (lintok; plan).
"""Levenshtein distance: pure Python fallback and rapidfuzz when available."""


def _levenshtein_pure(typo: str, correction: str) -> int:
    """Pure Python Levenshtein. Fallback when rapidfuzz unavailable."""
    s, t = typo, correction
    n, m = len(s), len(t)
    dp: list[list[int]] = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sub = 0 if s[i - 1] == t[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + sub,
            )
    return dp[n][m]


def levenshtein_distance(
    typo: str, correction: str, *, score_cutoff: int | None = None
) -> int:
    """Return standard edit distance. Uses rapidfuzz when available."""
    try:
        from rapidfuzz.distance import Levenshtein  # noqa: PLC0415

        return Levenshtein.distance(typo, correction, score_cutoff=score_cutoff)
    except ImportError:
        d = _levenshtein_pure(typo, correction)
        if score_cutoff is not None and d > score_cutoff:
            return score_cutoff + 1
        return d
