# Edited by Cursor
"""Process normrules command: run legal dict, rule and awareness scripts; write only under output dir (e.g. data/normrules)."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

console = Console(force_terminal=True)

_LEGAL_DICT_SCRIPT = "scripts.build_legal_dict"
_RULE_SCRIPT = "scripts.build_rule_candidates"
_AWARENESS_SCRIPT = "scripts.build_awareness_candidates"


def _project_root() -> Path:
    """Return project root (directory containing scripts/). Used for subprocess cwd and PYTHONPATH."""
    return Path.cwd()


def _scripts_available(root: Path) -> bool:
    """Return True if all required scripts exist under root."""
    return (
        (root / "scripts" / "build_legal_dict.py").is_file()
        and (root / "scripts" / "build_rule_candidates.py").is_file()
        and (root / "scripts" / "build_awareness_candidates.py").is_file()
    )


def _run_legal_dict(project_root: Path, output_path: Path) -> int:
    """Run build_legal_dict script; writes legal words to output_path. Returns exit code."""
    output_path = output_path.resolve()
    cmd: list[str] = [
        sys.executable,
        "-m",
        _LEGAL_DICT_SCRIPT,
        "-o",
        str(output_path),
    ]
    env = {**os.environ, "PYTHONPATH": str(project_root)}
    result = subprocess.run(  # noqa: S603
        cmd,
        cwd=project_root,
        env=env,
        check=False,
    )
    return result.returncode


def _run_normrules_script(
    project_root: Path,
    module: str,
    input_dir: Path,
    output_dir: Path,
    allow_no_enchant: bool,
    *,
    env_extra: dict[str, str] | None = None,
) -> int:
    """Run a normrules script as a subprocess with PYTHONPATH set to project root.

    Args:
        project_root: Root directory added to PYTHONPATH for module resolution.
        module: Python module name to execute (e.g. scripts.build_rule_candidates).
        input_dir: Directory containing transcript JSON files.
        output_dir: Directory where candidate JSON files will be written.
        allow_no_enchant: If True, pass --allow-no-enchant for spell checker fallback.
        env_extra: Optional extra env vars (e.g. LEGAL_WORDS_PATH for subprocess).

    Returns
    -------
        Exit code from subprocess (0 for success, non-zero for failure).
    """
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    cmd: list[str] = [
        sys.executable,
        "-m",
        module,
        "-i",
        str(input_dir),
        "-o",
        str(output_dir),
    ]
    if allow_no_enchant:
        cmd.append("--allow-no-enchant")
    env = {**os.environ, "PYTHONPATH": str(project_root)}
    if env_extra:
        env = {**env, **env_extra}
    result = subprocess.run(  # noqa: S603
        cmd,
        cwd=project_root,
        env=env,
        check=False,
    )
    return result.returncode


def add_normrules_command(app: typer.Typer) -> None:
    """Register the 'normrules' subcommand on the given Typer app."""

    @app.command(name="normrules")
    def process_normrules(
        input_dir: Annotated[
            Path,
            typer.Option(
                "--input-dir", "-i", help="Transcripts directory (recursive *.json)"
            ),
        ] = Path("data/transcripts"),
        output_dir: Annotated[
            Path,
            typer.Option(
                "--output-dir", "-o", help="Output directory for candidate JSON files"
            ),
        ] = Path("data/normrules"),
        allow_no_enchant: Annotated[
            bool,
            typer.Option("--allow-no-enchant", help="Allow spell checker fallback"),
        ] = False,
    ) -> None:
        """Run legal dict, normalization rules and awareness logic; write only under output dir (e.g. data/normrules)."""
        root = _project_root()
        if not _scripts_available(root):
            console.print(
                "[red]Run this command from the project root (directory containing scripts/).[/red]"
            )
            raise typer.Exit(1)
        output_dir = output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        legal_words_path = output_dir / "legal_words.txt"
        code = _run_legal_dict(root, legal_words_path)
        if code != 0:
            raise typer.Exit(code)
        env_extra = {"LEGAL_WORDS_PATH": str(legal_words_path)}
        code = _run_normrules_script(
            root,
            _RULE_SCRIPT,
            input_dir,
            output_dir,
            allow_no_enchant,
            env_extra=env_extra,
        )
        if code != 0:
            raise typer.Exit(code)
        code = _run_normrules_script(
            root,
            _AWARENESS_SCRIPT,
            input_dir,
            output_dir,
            allow_no_enchant,
            env_extra=env_extra,
        )
        if code != 0:
            raise typer.Exit(code)
        console.print(
            f"[bold green]Wrote legal words and rule/awareness candidates to {output_dir}[/bold green]"
        )
