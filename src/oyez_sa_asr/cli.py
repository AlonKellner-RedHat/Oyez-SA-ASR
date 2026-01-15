# Edited by Claude
"""Console script for oyez_sa_asr with scrape/process/clear subcommands."""

import asyncio
import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from tqdm import tqdm

from ._example import example
from .cli_clear import clear_app
from .cli_process import process_app
from .scraper import (
    AdaptiveFetcher,
    FetchResult,
    OyezCasesTraverser,
    RequestMetadata,
)

app = typer.Typer()
scrape_app = typer.Typer(help="Scrape data from Oyez API")
console = Console(force_terminal=True)

app.add_typer(scrape_app, name="scrape")
app.add_typer(process_app, name="process")
app.add_typer(clear_app, name="clear")


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
    min_improvement: Annotated[
        float,
        typer.Option(
            "--min-improvement", "-m", help="Min rate improvement to scale (0.25=25%)"
        ),
    ] = 0.25,
) -> None:
    """Scrape detailed case information from the Oyez API.

    Uses adaptive parallelism with rate-based scaling. Doubles workers when
    throughput improves by more than min-improvement (default 25%).
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
    console.print(f"  Min improvement: {min_improvement:.0%}")
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
        cache_dir,
        ttl_days=ttl_days,
        max_parallelism=max_parallelism,
        min_improvement=min_improvement,
    )

    # Stats tracking
    stats = {"new": 0, "failed": 0}

    # Progress bar created lazily when we know uncached count
    pbar: tqdm[None] | None = None

    def on_progress(
        completed: int, total: int, result: FetchResult, parallelism: int
    ) -> None:
        """Update progress for each uncached request completed."""
        nonlocal pbar
        # Create progress bar on first call (now we know total uncached)
        if pbar is None:
            pbar = tqdm(total=total, desc="Fetching", unit="case", dynamic_ncols=True)

        if result.success:
            stats["new"] += 1
        else:
            stats["failed"] += 1

        pbar.n = completed
        pbar.set_postfix(
            parallelism=parallelism, new=stats["new"], failed=stats["failed"]
        )
        pbar.refresh()

    async def run_fetch() -> list[FetchResult]:
        return await fetcher.fetch_batch_adaptive(requests, on_progress)

    all_results = asyncio.run(run_fetch())
    if pbar is not None:
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


if __name__ == "__main__":
    app()
