# Edited by Claude
"""Clear commands for oyez_sa_asr CLI."""

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

console = Console(force_terminal=True)
clear_app = typer.Typer(help="Clear cached and processed data")


@dataclass
class ClearTarget:
    """Configuration for a clearable data type."""

    name: str
    cache_dir: Path
    data_dir: Path | None  # None if no data directory (audio is cache-only)


# Define all clearable targets with their default paths
CLEAR_TARGETS: dict[str, ClearTarget] = {
    "index": ClearTarget("index", Path(".cache/index"), Path("data/index")),
    "cases": ClearTarget("cases", Path(".cache/cases"), Path("data/cases")),
    "transcripts": ClearTarget(
        "transcripts", Path(".cache/transcripts"), Path("data/transcripts")
    ),
    "audio": ClearTarget("audio", Path(".cache/audio"), None),  # Cache-only
}

# Data-only targets (no cache directory)
DATA_ONLY_TARGETS: dict[str, Path] = {
    "speakers": Path("data/speakers"),
}


def _clear_directory(path: Path, name: str) -> int:
    """Delete a directory and return the count of items removed."""
    if not path.exists():
        console.print(f"[yellow]{name}:[/yellow] {path} does not exist")
        return 0

    count = sum(1 for _ in path.rglob("*") if _.is_file())
    shutil.rmtree(path)
    console.print(f"[green]{name}:[/green] Removed {path} ({count} files)")
    return count


def _make_clear_with_data(name: str, default_cache: Path, default_data: Path) -> None:
    """Create a clear command with both cache and data directories."""

    @clear_app.command(name=name)
    def cmd(
        cache_dir: Annotated[
            Path,
            typer.Option("--cache-dir", "-c", help="Cache directory to clear"),
        ] = default_cache,
        data_dir: Annotated[
            Path,
            typer.Option("--data-dir", "-d", help="Data directory to clear"),
        ] = default_data,
        force: Annotated[
            bool,
            typer.Option("--force", "-f", help="Skip confirmation prompt"),
        ] = False,
    ) -> None:
        console.print(f"[bold]Clearing {name} data[/bold]")
        console.print(f"  Cache dir: {cache_dir}")
        console.print(f"  Data dir: {data_dir}")
        console.print()

        if not force:
            confirm = typer.confirm("Are you sure you want to delete this data?")
            if not confirm:
                console.print("[yellow]Cancelled[/yellow]")
                raise typer.Exit(0)

        total = 0
        total += _clear_directory(cache_dir, "Cache")
        total += _clear_directory(data_dir, "Data")

        console.print()
        console.print(f"[bold green]Done![/bold green] Removed {total} files.")

    cmd.__doc__ = f"Clear all {name}-related cache and data."


def _make_clear_cache_only(name: str, default_cache: Path) -> None:
    """Create a clear command for cache-only targets."""

    @clear_app.command(name=name)
    def cmd(
        cache_dir: Annotated[
            Path,
            typer.Option("--cache-dir", "-c", help="Cache directory to clear"),
        ] = default_cache,
        force: Annotated[
            bool,
            typer.Option("--force", "-f", help="Skip confirmation prompt"),
        ] = False,
    ) -> None:
        console.print(f"[bold]Clearing {name} cache[/bold]")
        console.print(f"  Cache dir: {cache_dir}")
        console.print()

        if not force:
            confirm = typer.confirm("Are you sure you want to delete this data?")
            if not confirm:
                console.print("[yellow]Cancelled[/yellow]")
                raise typer.Exit(0)

        total = _clear_directory(cache_dir, "Cache")

        console.print()
        console.print(f"[bold green]Done![/bold green] Removed {total} files.")

    cmd.__doc__ = f"Clear {name} cache."


def _create_clear_command(target: ClearTarget) -> None:
    """Create and register a clear command for a target."""
    if target.data_dir is not None:
        _make_clear_with_data(target.name, target.cache_dir, target.data_dir)
    else:
        _make_clear_cache_only(target.name, target.cache_dir)


def _make_clear_data_only(name: str, default_data: Path) -> None:
    """Create a clear command for data-only targets (no cache)."""

    @clear_app.command(name=name)
    def cmd(
        data_dir: Annotated[
            Path,
            typer.Option("--data-dir", "-d", help="Data directory to clear"),
        ] = default_data,
        force: Annotated[
            bool,
            typer.Option("--force", "-f", help="Skip confirmation prompt"),
        ] = False,
    ) -> None:
        console.print(f"[bold]Clearing {name} data[/bold]")
        console.print(f"  Data dir: {data_dir}")
        console.print()

        if not force:
            confirm = typer.confirm("Are you sure you want to delete this data?")
            if not confirm:
                console.print("[yellow]Cancelled[/yellow]")
                raise typer.Exit(0)

        total = _clear_directory(data_dir, "Data")

        console.print()
        console.print(f"[bold green]Done![/bold green] Removed {total} files.")

    cmd.__doc__ = f"Clear {name} data."


# Register all clear commands
for _target in CLEAR_TARGETS.values():
    _create_clear_command(_target)

# Register data-only clear commands
for _name, _path in DATA_ONLY_TARGETS.items():
    _make_clear_data_only(_name, _path)
