# Edited by Claude
"""Scrape transcripts subcommand for oyez_sa_asr CLI."""

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from tqdm import tqdm

from .scraper import AdaptiveFetcher, FetchResult, RequestMetadata
from .scraper.parser_cases import extract_media_urls

console = Console(force_terminal=True)


def add_transcripts_command(scrape_app: typer.Typer) -> None:
    """Add the transcripts command to the scrape app."""

    @scrape_app.command(name="transcripts")
    def scrape_transcripts(
        cases_dir: Annotated[
            Path,
            typer.Option("--cases-dir", "-c", help="Processed cases directory"),
        ] = Path("data/cases"),
        cache_dir: Annotated[
            Path,
            typer.Option("--cache-dir", help="Directory for caching responses"),
        ] = Path(".cache/transcripts"),
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
                "--min-improvement",
                "-m",
                help="Min rate improvement to scale (0.25=25%)",
            ),
        ] = 0.25,
    ) -> None:
        """Scrape transcript data from case_media API endpoints.

        Fetches oral argument and opinion announcement transcripts.
        """
        console.print("[bold]Scraping transcripts (adaptive parallelism)[/bold]")
        console.print(f"  Cases dir: {cases_dir}")
        console.print(f"  Cache dir: {cache_dir}")
        if terms:
            console.print(f"  Terms: {', '.join(terms)}")
        console.print(f"  Cache TTL: {ttl_days} days")
        console.print(f"  Max parallelism: {max_parallelism}")
        console.print(f"  Min improvement: {min_improvement:.0%}")
        console.print()

        urls = extract_media_urls(cases_dir, terms)

        if not urls:
            console.print("[yellow]Warning:[/yellow] No media URLs found.")
            console.print("Run 'process cases' first to generate processed case files.")
            return

        console.print(f"Found {len(urls)} media URLs to fetch")
        console.print()

        requests = [RequestMetadata(url=url) for url in urls]

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
                pbar = tqdm(
                    total=total, desc="Fetching", unit="url", dynamic_ncols=True
                )

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
