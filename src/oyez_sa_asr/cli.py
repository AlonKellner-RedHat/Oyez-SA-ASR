"""Console script for oyez_sa_asr."""

import typer
from rich.console import Console

from ._example import example

app = typer.Typer()
console = Console()


@app.command()
def main() -> None:
    """Console script for oyez_sa_asr."""
    console.print("Replace this message by putting your code into oyez_sa_asr.cli.main")
    console.print("See Typer documentation at https://typer.tiangolo.com/")
    example()


if __name__ == "__main__":
    app()
