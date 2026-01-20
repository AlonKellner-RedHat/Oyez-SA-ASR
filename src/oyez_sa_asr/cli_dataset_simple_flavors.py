# Edited by Claude
"""Duration-based simple dataset flavors.

Three splits by utterance length:
- lt1m: [0, 60s) - 8 workers default
- lt5m: [60s, 300s) - 4 workers default
- lt30m: [300s, 1800s) - 1 worker default
"""

from pathlib import Path
from typing import Annotated

import typer

from .cli_dataset_simple_core import run_simple_dataset


def dataset_simple_lt1m(
    flex_dir: Annotated[
        Path, typer.Option("--flex-dir", "-f", help="Flex dataset directory")
    ] = Path("datasets/flex"),
    output_dir: Annotated[
        Path, typer.Option("--output-dir", "-o", help="Dataset output directory")
    ] = Path("datasets/simple-lt1m"),
    terms: Annotated[
        list[str] | None, typer.Option("--term", "-T", help="Filter to term(s)")
    ] = None,
    shard_size_mb: Annotated[
        int, typer.Option("--shard-size", "-s", help="Shard size in MB")
    ] = 100,
    workers: Annotated[int, typer.Option("--workers", "-w", help="Workers")] = 8,
    force: Annotated[bool, typer.Option("--force", "-F", help="Force regen")] = False,
    include_invalid: Annotated[
        bool, typer.Option("--include-invalid", help="Include invalid")
    ] = False,
) -> None:
    """Create simple dataset with utterances < 1 minute (safe for many workers)."""
    run_simple_dataset(
        flex_dir,
        output_dir,
        terms,
        shard_size_mb,
        workers,
        force,
        include_invalid,
        0,
        60,
        "oyez dataset simple-lt1m",
    )


def dataset_simple_lt5m(
    flex_dir: Annotated[
        Path, typer.Option("--flex-dir", "-f", help="Flex dataset directory")
    ] = Path("datasets/flex"),
    output_dir: Annotated[
        Path, typer.Option("--output-dir", "-o", help="Dataset output directory")
    ] = Path("datasets/simple-lt5m"),
    terms: Annotated[
        list[str] | None, typer.Option("--term", "-T", help="Filter to term(s)")
    ] = None,
    shard_size_mb: Annotated[
        int, typer.Option("--shard-size", "-s", help="Shard size in MB")
    ] = 100,
    workers: Annotated[int, typer.Option("--workers", "-w", help="Workers")] = 4,
    force: Annotated[bool, typer.Option("--force", "-F", help="Force regen")] = False,
    include_invalid: Annotated[
        bool, typer.Option("--include-invalid", help="Include invalid")
    ] = False,
) -> None:
    """Create simple dataset with utterances 1-5 minutes."""
    run_simple_dataset(
        flex_dir,
        output_dir,
        terms,
        shard_size_mb,
        workers,
        force,
        include_invalid,
        60,
        300,
        "oyez dataset simple-lt5m",
    )


def dataset_simple_lt30m(
    flex_dir: Annotated[
        Path, typer.Option("--flex-dir", "-f", help="Flex dataset directory")
    ] = Path("datasets/flex"),
    output_dir: Annotated[
        Path, typer.Option("--output-dir", "-o", help="Dataset output directory")
    ] = Path("datasets/simple-lt30m"),
    terms: Annotated[
        list[str] | None, typer.Option("--term", "-T", help="Filter to term(s)")
    ] = None,
    shard_size_mb: Annotated[
        int, typer.Option("--shard-size", "-s", help="Shard size in MB")
    ] = 100,
    workers: Annotated[int, typer.Option("--workers", "-w", help="Workers")] = 1,
    force: Annotated[bool, typer.Option("--force", "-F", help="Force regen")] = False,
    include_invalid: Annotated[
        bool, typer.Option("--include-invalid", help="Include invalid")
    ] = False,
) -> None:
    """Create simple dataset with utterances 5-30 minutes (use 1 worker)."""
    run_simple_dataset(
        flex_dir,
        output_dir,
        terms,
        shard_size_mb,
        workers,
        force,
        include_invalid,
        300,
        1800,
        "oyez dataset simple-lt30m",
    )
