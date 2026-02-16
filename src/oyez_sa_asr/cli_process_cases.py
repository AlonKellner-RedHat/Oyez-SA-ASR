# Edited by Cursor: split from cli_process (lintok; no new exclusions).
"""Process cases command."""

import json
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from tqdm import tqdm

from oyez_sa_asr.scraper.parser_cases import ProcessedCase

console = Console(force_terminal=True)


def _get_term_from_raw(raw_data: dict[str, Any]) -> str | None:
    term = raw_data.get("term")
    return term if term else None


def add_cases_command(app: typer.Typer) -> None:
    """Register the 'cases' subcommand on the given Typer app."""

    @app.command(name="cases")
    def process_cases(
        cache_dir: Annotated[Path, typer.Option("--cache-dir", "-c")] = Path(
            ".cache/cases"
        ),
        output_dir: Annotated[Path, typer.Option("--output-dir", "-o")] = Path(
            "data/cases"
        ),
        terms: Annotated[list[str] | None, typer.Option("--term", "-T")] = None,
        force: Annotated[bool, typer.Option("--force", "-F")] = False,
    ) -> None:
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
            return
        term_set = set(terms) if terms else None
        raw_files = list(raw_dir.glob("*.json"))
        if not raw_files:
            console.print("[yellow]Warning:[/yellow] No cached cases found.")
            return
        processed_count = 0
        skipped_term = 0
        skipped_existing = 0
        error_count = 0
        with tqdm(raw_files, desc="Processing", unit="case") as pbar:
            for raw_file in pbar:
                try:
                    with raw_file.open() as f:
                        raw_data = json.load(f)
                    if isinstance(raw_data, list) or "ID" not in raw_data:
                        continue
                    if term_set:
                        case_term = _get_term_from_raw(raw_data)
                        if case_term not in term_set:
                            skipped_term += 1
                            continue
                    case = ProcessedCase.from_raw(raw_data)
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
        console.print(
            f"[bold green]Done![/bold green] Processed {processed_count} cases."
        )
        if skipped_term > 0:
            console.print(f"  Skipped (term filter): {skipped_term}")
        if skipped_existing > 0:
            console.print(f"  Skipped (existing): {skipped_existing}")
        if error_count > 0:
            console.print(
                f"[yellow]Warnings:[/yellow] {error_count} files skipped due to errors"
            )
        console.print(f"Output: {output_dir}")
