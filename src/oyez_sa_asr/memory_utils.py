# Edited by Claude
"""Memory monitoring utilities for detecting OOM conditions."""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Track OOM kills from cgroup
_OOM_EVENTS_PATH = Path("/sys/fs/cgroup/memory.events")


def get_oom_kill_count() -> int:
    """Get current OOM kill count from cgroup."""
    try:
        if _OOM_EVENTS_PATH.exists():
            content = _OOM_EVENTS_PATH.read_text()
            for line in content.splitlines():
                if line.startswith("oom_kill "):
                    return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        pass
    return 0


def get_memory_usage_mb() -> tuple[int, int, int]:
    """Get memory usage (used_mb, available_mb, total_mb)."""
    try:
        result = subprocess.run(
            ["/usr/bin/free", "-m"],
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.splitlines():
            if line.startswith("Mem:"):
                parts = line.split()
                total = int(parts[1])
                used = int(parts[2])
                available = int(parts[6]) if len(parts) > 6 else total - used
                return used, available, total
    except (subprocess.SubprocessError, ValueError, IndexError, FileNotFoundError):
        pass
    return 0, 0, 0


def kill_orphan_forkservers() -> int:
    """Kill any orphaned forkserver processes from previous runs."""
    killed = 0
    try:
        result = subprocess.run(
            ["/usr/bin/pkill", "-f", "multiprocessing.forkserver"],
            capture_output=True,
            check=False,
        )
        # pkill returns 0 if processes were killed
        if result.returncode == 0:
            killed = 1  # At least one was killed
            logger.info("Cleaned up orphaned forkserver processes")
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return killed


def check_oom(initial_oom: int, last_path: Path | None) -> None:
    """Check if OOM kill occurred and log diagnostic info."""
    current_oom = get_oom_kill_count()
    if current_oom > initial_oom:
        new_kills = current_oom - initial_oom
        used, _, total = get_memory_usage_mb()
        logger.error(
            "DETECTED %d OOM KILL(S)! Memory: %d/%d MB. Last: %s",
            new_kills,
            used,
            total,
            last_path or "unknown",
        )
