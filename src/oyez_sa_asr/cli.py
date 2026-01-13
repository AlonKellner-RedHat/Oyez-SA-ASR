# Edited by Claude
"""Console script for oyez_sa_asr with scrape/process subcommands."""

import asyncio
import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from tqdm import tqdm

from ._example import example
from .scraper import (
    AdaptiveFetcher,
    FetchResult,
    OyezCasesTraverser,
    RequestMetadata,
    parse_cached_cases,
)

app = typer.Typer()
scrape_app = typer.Typer(help="Scrape data from Oyez API")
process_app = typer.Typer(help="Process cached data into structured files")
console = Console(force_terminal=True)

app.add_typer(scrape_app, name="scrape")
app.add_typer(process_app, name="process")


@app.command()
def main() -> None:
    """Console script for oyez_sa_asr."""
    console.print("Replace this message by putting your code into oyez_sa_asr.cli.main")
    console.print("See Typer documentation at https://typer.tiangolo.com/")
    example()


# === SCRAPE COMMANDS ===


@scrape_app.command(name="index")
def scrape_index(
    cache_dir: Annotated[
        Path,
        typer.Option("--cache-dir", "-c", help="Directory for caching requests"),
    ] = Path(".cache/index"),
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
    """Scrape case index pages from the Oyez API."""
    console.print("[bold]Scraping Oyez case index[/bold]")
    console.print(f"  Cache dir: {cache_dir}")
    console.print(f"  Max pages: {max_pages or 'unlimited'}")
    console.print(f"  Per page: {per_page}")
    console.print(f"  Cache TTL: {ttl_days} days")
    console.print()

    fetcher = AdaptiveFetcher.create(cache_dir, ttl_days=ttl_days)
    traverser = OyezCasesTraverser(fetcher, per_page=per_page, max_pages=max_pages)

    # Traverser already prints progress per page
    cases = asyncio.run(traverser.fetch_all())

    console.print()
    console.print(f"[bold green]Done![/bold green] Fetched {len(cases)} cases total.")


@scrape_app.command(name="cases")
def scrape_cases(
    index_file: Annotated[
        Path,
        typer.Option("--index-file", "-i", help="Path to cases_index.json"),
    ] = Path("data/index/cases_index.json"),
    cache_dir: Annotated[
        Path,
        typer.Option("--cache-dir", "-c", help="Directory for caching requests"),
    ] = Path(".cache/cases"),
    ttl_days: Annotated[
        int,
        typer.Option("--ttl-days", "-t", help="Cache TTL in days"),
    ] = 30,
    max_parallelism: Annotated[
        int,
        typer.Option("--max-parallelism", "-p", help="Maximum parallel requests"),
    ] = 1024,
) -> None:
    """Scrape detailed case information from the Oyez API.

    Uses adaptive parallelism: starts at 1, doubles on success, halves on failure.
    Automatically discovers the optimal parallelism for the API.
    """
    # Check if index file exists
    if not index_file.exists():
        console.print(f"[red]Error:[/red] Index file not found: {index_file}")
        console.print("Run 'process index' first to generate the index.")
        raise typer.Exit(1)

    console.print("[bold]Scraping Oyez case details (adaptive parallelism)[/bold]")
    console.print(f"  Index file: {index_file}")
    console.print(f"  Cache dir: {cache_dir}")
    console.print(f"  Cache TTL: {ttl_days} days")
    console.print(f"  Max parallelism: {max_parallelism}")
    console.print()

    # Load index and extract hrefs
    with index_file.open() as f:
        index_data = json.load(f)

    cases = index_data.get("cases", [])
    hrefs = [case["href"] for case in cases if case.get("href")]

    console.print(f"Found {len(hrefs)} case URLs to fetch")
    console.print()

    # Create requests for all case hrefs
    requests = [RequestMetadata(url=href) for href in hrefs]

    # Fetch with adaptive parallelism
    fetcher = AdaptiveFetcher.create(
        cache_dir, ttl_days=ttl_days, max_parallelism=max_parallelism
    )

    # Stats tracking
    stats = {"cached": 0, "new": 0, "failed": 0, "last_wave_size": 0}

    # Create tqdm progress bar
    pbar = tqdm(total=len(requests), desc="Fetching", unit="case", dynamic_ncols=True)

    def on_progress(
        completed: int, total: int, result: FetchResult, parallelism: int
    ) -> None:
        """Update progress after each wave completes."""
        del total  # Unused - tqdm handles progress display
        # Count results from this wave
        if result.from_cache:
            stats["cached"] += 1
        elif result.success:
            stats["new"] += 1
        else:
            stats["failed"] += 1

        # Update progress bar to completed count
        pbar.n = completed
        pbar.set_postfix(
            parallelism=parallelism,
            cached=stats["cached"],
            new=stats["new"],
            failed=stats["failed"],
        )
        pbar.refresh()

    async def run_fetch() -> list[FetchResult]:
        return await fetcher.fetch_batch_adaptive(requests, on_progress)

    all_results = asyncio.run(run_fetch())
    pbar.close()

    # Report results
    cached = sum(1 for r in all_results if r.from_cache)
    new_fetches = sum(1 for r in all_results if r.success and not r.from_cache)
    failures = sum(1 for r in all_results if not r.success)

    console.print()
    console.print("[bold green]Done![/bold green]")
    console.print(f"  Cached: {cached}")
    console.print(f"  New fetches: {new_fetches}")
    console.print(f"  Failures: {failures}")


# === PROCESS COMMANDS ===


@process_app.command(name="index")
def process_index(
    cache_dir: Annotated[
        Path,
        typer.Option("--cache-dir", "-c", help="Directory with cached responses"),
    ] = Path(".cache/index"),
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output JSON file path"),
    ] = Path("data/index/cases_index.json"),
) -> None:
    """Parse cached case index into a structured JSON file."""
    console.print("[bold]Parsing cached case index[/bold]")
    console.print(f"  Cache dir: {cache_dir}")
    console.print(f"  Output: {output}")
    console.print()

    index = parse_cached_cases(cache_dir)

    if index.total_cases == 0:
        console.print("[yellow]Warning:[/yellow] No cached cases found.")
        console.print("Run 'scrape index' first to fetch cases from the API.")
        return

    index.save(output)

    console.print(f"[bold green]Done![/bold green] Parsed {index.total_cases} cases.")
    console.print(f"Index saved to: {output}")


if __name__ == "__main__":
    app()
