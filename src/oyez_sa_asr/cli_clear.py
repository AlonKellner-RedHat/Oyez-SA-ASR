# Edited by Claude
"""Clear commands for oyez_sa_asr CLI."""

import shutil
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

console = Console(force_terminal=True)
clear_app = typer.Typer(help="Clear cached and processed data")


def _clear_directory(path: Path, name: str) -> int:
    """Delete a directory and return the count of items removed."""
    if not path.exists():
        console.print(f"[yellow]{name}:[/yellow] {path} does not exist")
        return 0

    count = sum(1 for _ in path.rglob("*") if _.is_file())
    shutil.rmtree(path)
    console.print(f"[green]{name}:[/green] Removed {path} ({count} files)")
    return count


@clear_app.command(name="index")
def clear_index(
    cache_dir: Annotated[
        Path,
        typer.Option("--cache-dir", "-c", help="Cache directory to clear"),
    ] = Path(".cache/index"),
    data_dir: Annotated[
        Path,
        typer.Option("--data-dir", "-d", help="Data directory to clear"),
    ] = Path("data/index"),
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation prompt"),
    ] = False,
) -> None:
    """Clear all index-related cache and data."""
    console.print("[bold]Clearing index data[/bold]")
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
    console.print(f"[bold green]Done![/bold green] Removed {total} files total.")


@clear_app.command(name="cases")
def clear_cases(
    cache_dir: Annotated[
        Path,
        typer.Option("--cache-dir", "-c", help="Cache directory to clear"),
    ] = Path(".cache/cases"),
    data_dir: Annotated[
        Path,
        typer.Option("--data-dir", "-d", help="Data directory to clear"),
    ] = Path("data/cases"),
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation prompt"),
    ] = False,
) -> None:
    """Clear all cases-related cache and data."""
    console.print("[bold]Clearing cases data[/bold]")
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
    console.print(f"[bold green]Done![/bold green] Removed {total} files total.")
