# Edited by Claude
"""Scrape subcommands for oyez_sa_asr CLI."""

import asyncio
import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from tqdm import tqdm

from .cli_scrape_audio import add_audio_command
from .cli_scrape_transcripts import add_transcripts_command
from .scraper import AdaptiveFetcher, FetchResult, OyezCasesTraverser, RequestMetadata
from .term_filter import filter_by_terms

scrape_app = typer.Typer(help="Scrape data from Oyez API")
console = Console(force_terminal=True)

# Add commands from separate modules
add_transcripts_command(scrape_app)
add_audio_command(scrape_app)


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
    terms: Annotated[
        list[str] | None,
        typer.Option("--term", "-T", help="Filter to specific term(s)"),
    ] = None,
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

    Uses adaptive parallelism with rate-based scaling.
    """
    if not index_file.exists():
        console.print(f"[red]Error:[/red] Index file not found: {index_file}")
        console.print("Run 'process index' first to generate the index.")
        raise typer.Exit(1)

    console.print("[bold]Scraping Oyez case details (adaptive parallelism)[/bold]")
    console.print(f"  Index file: {index_file}")
    console.print(f"  Cache dir: {cache_dir}")
    if terms:
        console.print(f"  Terms: {', '.join(terms)}")
    console.print(f"  Cache TTL: {ttl_days} days")
    console.print(f"  Max parallelism: {max_parallelism}")
    console.print(f"  Min improvement: {min_improvement:.0%}")
    console.print()

    with index_file.open() as f:
        index_data = json.load(f)

    all_cases = index_data.get("cases", [])
    cases = filter_by_terms(all_cases, lambda c: c.get("term", ""), terms)
    hrefs = [case["href"] for case in cases if case.get("href")]

    console.print(f"Found {len(hrefs)} case URLs to fetch")
    console.print()

    requests = [RequestMetadata(url=href) for href in hrefs]

    fetcher = AdaptiveFetcher.create(
        cache_dir,
        ttl_days=ttl_days,
        max_parallelism=max_parallelism,
        min_improvement=min_improvement,
    )

    stats = {"new": 0, "failed": 0}
    pbar: tqdm[None] | None = None

    def on_progress(
        completed: int, total: int, result: FetchResult, parallelism: int
    ) -> None:
        nonlocal pbar
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

    cached = sum(1 for r in all_results if r.from_cache)
    new_fetches = sum(1 for r in all_results if r.success and not r.from_cache)
    failures = sum(1 for r in all_results if not r.success)

    console.print()
    console.print("[bold green]Done![/bold green]")
    console.print(f"  Cached: {cached}")
    console.print(f"  New fetches: {new_fetches}")
    console.print(f"  Failures: {failures}")
