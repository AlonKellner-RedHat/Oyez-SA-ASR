# Edited by Claude
"""Console script for oyez_sa_asr."""

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from ._example import example
from .scraper import AdaptiveFetcher, OyezCasesTraverser, parse_cached_cases

app = typer.Typer()
console = Console()


@app.command()
def main() -> None:
    """Console script for oyez_sa_asr."""
    console.print("Replace this message by putting your code into oyez_sa_asr.cli.main")
    console.print("See Typer documentation at https://typer.tiangolo.com/")
    example()


@app.command()
def scrape_cases(
    cache_dir: Annotated[
        Path,
        typer.Option("--cache-dir", "-c", help="Directory for caching requests"),
    ] = Path(".cache"),
    max_pages: Annotated[
        int | None,
        typer.Option("--max-pages", "-m", help="Max pages to fetch (unlimited)"),
    ] = None,
    per_page: Annotated[
        int,
        typer.Option("--per-page", "-p", help="Number of results per page"),
    ] = 1000,
    ttl_days: Annotated[
        int,
        typer.Option("--ttl-days", "-t", help="Cache TTL in days"),
    ] = 30,
) -> None:
    """Scrape cases from the Oyez API."""
    console.print("[bold]Scraping Oyez cases[/bold]")
    console.print(f"  Cache dir: {cache_dir}")
    console.print(f"  Max pages: {max_pages or 'unlimited'}")
    console.print(f"  Per page: {per_page}")
    console.print(f"  Cache TTL: {ttl_days} days")
    console.print()

    fetcher = AdaptiveFetcher.create(cache_dir, ttl_days=ttl_days)
    traverser = OyezCasesTraverser(fetcher, per_page=per_page, max_pages=max_pages)

    cases = asyncio.run(traverser.fetch_all())

    console.print()
    console.print(f"[bold green]Done![/bold green] Fetched {len(cases)} cases total.")


@app.command()
def parse_cases_index(
    cache_dir: Annotated[
        Path,
        typer.Option("--cache-dir", "-c", help="Directory with cached responses"),
    ] = Path(".cache"),
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output JSON file path"),
    ] = Path("data/cases_index.json"),
) -> None:
    """Parse cached cases into a structured index file."""
    console.print("[bold]Parsing cached cases[/bold]")
    console.print(f"  Cache dir: {cache_dir}")
    console.print(f"  Output: {output}")
    console.print()

    index = parse_cached_cases(cache_dir)

    if index.total_cases == 0:
        console.print("[yellow]Warning:[/yellow] No cached cases found.")
        console.print("Run 'scrape-cases' first to fetch cases from the API.")
        return

    index.save(output)

    console.print(f"[bold green]Done![/bold green] Parsed {index.total_cases} cases.")
    console.print(f"Index saved to: {output}")


if __name__ == "__main__":
    app()
