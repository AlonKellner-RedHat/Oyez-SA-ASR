# Edited by Cursor: split from cli_process (lintok; no new exclusions).
"""Process transcripts command."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from tqdm import tqdm

from oyez_sa_asr.scraper.parser_transcripts import (
    ProcessedTranscript,
    build_transcript_to_case_map,
)

console = Console(force_terminal=True)


def add_transcripts_command(app: typer.Typer) -> None:
    """Register 'transcripts' command on the given Typer app."""

    @app.command(name="transcripts")
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
        """Parse cached transcripts into structured JSON files."""
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
