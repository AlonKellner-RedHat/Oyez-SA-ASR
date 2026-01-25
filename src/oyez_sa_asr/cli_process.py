# Edited by Claude
"""Process subcommands for oyez_sa_asr CLI."""

import json
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from tqdm import tqdm

from .cli_process_audio import add_audio_command
from .cli_process_speakers import add_speakers_command
from .scraper import parse_cached_cases
from .scraper.parser_cases import ProcessedCase
from .scraper.parser_transcripts import (
    ProcessedTranscript,
    build_transcript_to_case_map,
)


def _get_term_from_raw(raw_data: dict[str, Any]) -> str | None:
    """Extract term from raw case/transcript data.

    Returns None for missing or empty term values.
    """
    term = raw_data.get("term")
    return term if term else None


process_app = typer.Typer(help="Process cached data into structured files")
console = Console(force_terminal=True)

# Add audio command from separate module
add_audio_command(process_app)

# Add speakers command from separate module
add_speakers_command(process_app)


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
    _terms: Annotated[
        list[str] | None,
        typer.Option(
            "--term", "-T", help="Filter to specific term(s) (ignored for index)"
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-F", help="Regenerate index even if output exists"),
    ] = False,
) -> None:
    """Parse cached case index into a structured JSON file."""
    # Edited by Claude: Add force support
    console.print("[bold]Parsing cached case index[/bold]")
    console.print(f"  Cache dir: {cache_dir}")
    console.print(f"  Output: {output}")
    if force:
        console.print("  [yellow]Force mode: regenerating index[/yellow]")
    console.print()

    # If force and output exists, remove it
    if force and output.exists():
        output.unlink()

    index = parse_cached_cases(cache_dir)

    if index.total_cases == 0:
        console.print("[yellow]Warning:[/yellow] No cached cases found.")
        console.print("Run 'scrape index' first to fetch cases from the API.")
        return

    index.save(output)

    console.print(f"[bold green]Done![/bold green] Parsed {index.total_cases} cases.")
    console.print(f"Index saved to: {output}")


@process_app.command(name="cases")
def process_cases(
    cache_dir: Annotated[
        Path,
        typer.Option("--cache-dir", "-c", help="Directory with cached case responses"),
    ] = Path(".cache/cases"),
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-o", help="Output directory for processed cases"),
    ] = Path("data/cases"),
    terms: Annotated[
        list[str] | None,
        typer.Option("--term", "-T", help="Filter to specific term(s)"),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-F", help="Reprocess existing case files"),
    ] = False,
) -> None:
    """Parse cached case details into structured JSON files.

    Creates one JSON file per case at data/cases/{term}/{docket}.json
    with audio references ready for scrape transcripts/audio commands.
    """
    # Edited by Claude: Add force support
    console.print("[bold]Processing cached case details[/bold]")
    console.print(f"  Cache dir: {cache_dir}")
    console.print(f"  Output dir: {output_dir}")
    if terms:
        console.print(f"  Terms: {', '.join(terms)}")
    if force:
        console.print("  [yellow]Force mode: reprocessing existing files[/yellow]")
    console.print()

    raw_dir = cache_dir / "api.oyez.org" / "raw"

    if not raw_dir.exists():
        console.print("[yellow]Warning:[/yellow] No cached cases found.")
        console.print("Run 'scrape cases' first to fetch case details from the API.")
        return

    processed_count = 0
    skipped_term = 0
    skipped_existing = 0
    error_count = 0

    term_set = set(terms) if terms else None
    raw_files = list(raw_dir.glob("*.json"))
    if not raw_files:
        console.print("[yellow]Warning:[/yellow] No cached cases found.")
        console.print("Run 'scrape cases' first to fetch case details from the API.")
        return

    with tqdm(raw_files, desc="Processing", unit="case") as pbar:
        for raw_file in pbar:
            try:
                with raw_file.open() as f:
                    raw_data = json.load(f)

                if isinstance(raw_data, list) or "ID" not in raw_data:
                    continue

                # Apply term filter
                if term_set:
                    case_term = _get_term_from_raw(raw_data)
                    if case_term not in term_set:
                        skipped_term += 1
                        continue

                case = ProcessedCase.from_raw(raw_data)
                # Check if output file exists
                output_path = output_dir / case.term / f"{case.docket_number}.json"

                if not force and output_path.exists():
                    skipped_existing += 1
                    continue

                case.save(output_dir, source_path=raw_file)
                processed_count += 1

            except (json.JSONDecodeError, KeyError, TypeError):
                error_count += 1
                pbar.set_postfix(errors=error_count)

    console.print()
    console.print(f"[bold green]Done![/bold green] Processed {processed_count} cases.")
    if skipped_term > 0:
        console.print(f"  Skipped (term filter): {skipped_term}")
    if skipped_existing > 0:
        console.print(f"  Skipped (existing): {skipped_existing}")
    if error_count > 0:
        console.print(
            f"[yellow]Warnings:[/yellow] {error_count} files skipped due to errors"
        )
    console.print(f"Output: {output_dir}")


@process_app.command(name="transcripts")
def process_transcripts(
    cache_dir: Annotated[
        Path,
        typer.Option("--cache-dir", "-c", help="Directory with cached transcripts"),
    ] = Path(".cache/transcripts"),
    cases_dir: Annotated[
        Path,
        typer.Option("--cases-dir", help="Directory with processed case files"),
    ] = Path("data/cases"),
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-o", help="Output directory for transcripts"),
    ] = Path("data/transcripts"),
    terms: Annotated[
        list[str] | None,
        typer.Option("--term", "-T", help="Filter to specific term(s)"),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-F", help="Reprocess existing transcript files"),
    ] = False,
) -> None:
    """Parse cached transcripts into structured JSON files.

    Creates transcript files at data/transcripts/{term}/{docket}/{type}.json
    with metadata, per-turn data, and content for audio/utterance processing.
    """
    # Edited by Claude: Add force support
    console.print("[bold]Processing cached transcripts[/bold]")
    console.print(f"  Cache dir: {cache_dir}")
    console.print(f"  Cases dir: {cases_dir}")
    console.print(f"  Output dir: {output_dir}")
    if terms:
        console.print(f"  Terms: {', '.join(terms)}")
    if force:
        console.print("  [yellow]Force mode: reprocessing existing files[/yellow]")
    console.print()

    raw_dir = cache_dir / "api.oyez.org" / "raw"

    if not raw_dir.exists():
        console.print("[yellow]Warning:[/yellow] No cached transcripts found.")
        console.print("Run 'scrape transcripts' first.")
        return

    console.print("Building transcript-to-case mapping...")
    case_map = build_transcript_to_case_map(cases_dir, terms)
    console.print(f"  Found {len(case_map)} transcript-case mappings")
    console.print()

    processed_count = 0
    skipped_no_case = 0
    skipped_existing = 0
    error_count = 0

    raw_files = list(raw_dir.glob("*.json"))
    if not raw_files:
        console.print("[yellow]Warning:[/yellow] No cached transcripts found.")
        return

    with tqdm(raw_files, desc="Processing", unit="transcript") as pbar:
        for raw_file in pbar:
            try:
                with raw_file.open() as f:
                    raw_data = json.load(f)

                if isinstance(raw_data, list):
                    continue

                transcript_id = raw_data.get("id")
                if transcript_id is None:
                    continue

                case_info = case_map.get(transcript_id)
                if case_info is None:
                    skipped_no_case += 1
                    continue

                term, docket = case_info
                transcript = ProcessedTranscript.from_raw(raw_data, term, docket)
                # Check if output file exists
                output_path = (
                    output_dir
                    / transcript.term
                    / transcript.case_docket
                    / transcript.get_filename()
                )

                if not force and output_path.exists():
                    skipped_existing += 1
                    continue

                transcript.save(output_dir, source_path=raw_file)
                processed_count += 1

            except (json.JSONDecodeError, KeyError, TypeError):
                error_count += 1
                pbar.set_postfix(errors=error_count)

    console.print()
    console.print(
        f"[bold green]Done![/bold green] Processed {processed_count} transcripts."
    )
    if skipped_no_case > 0:
        console.print(f"  Skipped (no case mapping): {skipped_no_case}")
    if skipped_existing > 0:
        console.print(f"  Skipped (existing): {skipped_existing}")
    if error_count > 0:
        console.print(f"[yellow]Warnings:[/yellow] {error_count} files had errors")
    console.print(f"Output: {output_dir}")
