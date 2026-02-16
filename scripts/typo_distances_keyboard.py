# Edited by Cursor: split from typo_distances (lintok; plan).
"""Keyboard distance: QWERTY graph, substitute cost, min steps."""

from collections import deque

QWERTY = [
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm",
]


def _build_keyboard_graph() -> tuple[dict[str, set[str]], dict[str, dict[str, int]]]:
    """Adjacency sets and pairwise shortest path lengths (BFS)."""
    pos: dict[str, tuple[int, int]] = {}
    for r, row in enumerate(QWERTY):
        for c, ch in enumerate(row):
            pos[ch] = (r, c)
    adj: dict[str, set[str]] = {}
    for ch, (r, c) in pos.items():
        adj[ch] = set()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            r2, c2 = r + dr, c + dc
            if 0 <= r2 < len(QWERTY) and 0 <= c2 < len(QWERTY[r2]):
                adj[ch].add(QWERTY[r2][c2])
    dist: dict[str, dict[str, int]] = {}
    for ch in pos:
        dist[ch] = {ch: 0}
        q: deque[tuple[str, int]] = deque([(ch, 0)])
        while q:
            u, d = q.popleft()
            for v in adj[u]:
                if v not in dist[ch]:
                    dist[ch][v] = d + 1
                    q.append((v, d + 1))
    return adj, dist


_ADJ, _KEY_DIST = _build_keyboard_graph()


def _key_sub_cost(a: str, b: str) -> int:
    """Cost to substitute a with b on keyboard."""
    a, b = a.lower(), b.lower()
    if a == b:
        return 0
    if a not in _ADJ or b not in _ADJ:
        return 1
    return _KEY_DIST[a].get(b, 5)


def keyboard_distance(typo: str, correction: str) -> int:
    """Min keyboard steps to transform typo into correction."""
    s, t = typo, correction
    n, m = len(s), len(t)
    dp: list[list[int]] = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + _key_sub_cost(s[i - 1], t[j - 1]),
            )
            if i >= 2 and j >= 2 and s[i - 2] == t[j - 1] and s[i - 1] == t[j - 2]:
                dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + 1)
    return dp[n][m]
