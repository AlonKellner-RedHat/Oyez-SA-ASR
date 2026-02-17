# Edited by Cursor: thin re-export from cli_process_* (lintok; no new exclusions).
"""Process subcommands for oyez_sa_asr CLI."""

import typer

from oyez_sa_asr.cli_process_audio import add_audio_command
from oyez_sa_asr.cli_process_cases import add_cases_command
from oyez_sa_asr.cli_process_index import add_index_command
from oyez_sa_asr.cli_process_normrules import add_normrules_command
from oyez_sa_asr.cli_process_speakers import add_speakers_command
from oyez_sa_asr.cli_process_transcripts import add_transcripts_command

process_app = typer.Typer(help="Process cached data into structured files")

add_audio_command(process_app)
add_speakers_command(process_app)
add_index_command(process_app)
add_cases_command(process_app)
add_transcripts_command(process_app)
add_normrules_command(process_app)
