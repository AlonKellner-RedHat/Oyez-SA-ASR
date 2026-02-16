# Edited by Cursor: split from cli_process (lintok; no new exclusions).
"""Process index command."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from oyez_sa_asr.scraper import parse_cached_cases

console = Console(force_terminal=True)


def add_index_command(app: typer.Typer) -> None:
    """Register 'index' command on the given Typer app."""

    @app.command(name="index")
    def process_index(
        cache_dir: Annotated[
            Path,
            typer.Option("--cache-dir", "-c", help="Directory with cached responses"),
        ] = Path(".cache/index"),
        output: Annotated[
            Path,
            typer.Option("--output", "-o", help="Output JSON file path"),
        ] = Path("data/index/cases_index.json"),
        _terms: Annotated[
            list[str] | None,
            typer.Option(
                "--term", "-T", help="Filter to specific term(s) (ignored for index)"
            ),
        ] = None,
        force: Annotated[
            bool,
            typer.Option(
                "--force", "-F", help="Regenerate index even if output exists"
            ),
        ] = False,
    ) -> None:
        """Parse cached case index into a structured JSON file."""
        console.print("[bold]Parsing cached case index[/bold]")
        console.print(f"  Cache dir: {cache_dir}")
        console.print(f"  Output: {output}")
        if force:
            console.print("  [yellow]Force mode: regenerating index[/yellow]")
        console.print()
        if force and output.exists():
            output.unlink()
        index = parse_cached_cases(cache_dir)
        if index.total_cases == 0:
            console.print("[yellow]Warning:[/yellow] No cached cases found.")
            console.print("Run 'scrape index' first to fetch cases from the API.")
            return
        index.save(output)
        console.print(
            f"[bold green]Done![/bold green] Parsed {index.total_cases} cases."
        )
        console.print(f"Index saved to: {output}")
