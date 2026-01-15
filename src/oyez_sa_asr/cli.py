# Edited by Claude
"""Console script for oyez_sa_asr with scrape/process/clear subcommands."""

import typer
from rich.console import Console

from ._example import example
from .cli_clear import clear_app
from .cli_process import process_app
from .cli_scrape import scrape_app

app = typer.Typer()
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


if __name__ == "__main__":
    app()
