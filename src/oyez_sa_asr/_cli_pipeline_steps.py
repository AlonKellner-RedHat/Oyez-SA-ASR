# Edited by Cursor: split from cli_pipeline (lintok; plan).
"""Pipeline step definitions and option delegation helpers."""

import re
from typing import Any

from .term_parser import parse_term_list

SCRAPE_STEPS = [
    ("Scrape Index", "scrape", "index", False),
    ("Process Index", "process", "index", False),
    ("Scrape Cases", "scrape", "cases", True),
    ("Scrape Transcripts", "scrape", "transcripts", True),
    ("Scrape Audio", "scrape", "audio", True),
]

PROCESS_STEPS = [
    ("Process Cases", "process", "cases", True),
    ("Process Transcripts", "process", "transcripts", True),
    ("Process Audio", "process", "audio", True),
    ("Process Speakers", "process", "speakers", True),
]

DATASET_STEPS = [
    ("Dataset Raw", "dataset", "raw", True),
    ("Dataset Flex", "dataset", "flex", True),
    ("Dataset Simple", "dataset", "simple", False),
]

COMMAND_MAP: dict[str, dict[str, list[str]]] = {
    "scrape": {
        "index": ["scrape", "index"],
        "cases": ["scrape", "cases"],
        "transcripts": ["scrape", "transcripts"],
        "audio": ["scrape", "audio"],
    },
    "process": {
        "index": ["process", "index"],
        "cases": ["process", "cases"],
        "transcripts": ["process", "transcripts"],
        "audio": ["process", "audio"],
        "speakers": ["process", "speakers"],
    },
    "dataset": {
        "raw": ["dataset", "raw"],
        "flex": ["dataset", "flex"],
        "simple": ["dataset", "simple"],
    },
}


def parse_delegated_options(
    extra_args: list[str],
) -> dict[tuple[str, str | None], dict[str, Any]]:
    """Parse command-line args for delegated options."""
    delegated: dict[tuple[str, str | None], dict[str, Any]] = {}

    phase_pattern = re.compile(r"^--(scrape|process|dataset)-(.+)$")
    command_pattern = re.compile(
        r"^--(scrape|process|dataset)-(index|cases|transcripts|audio|speakers|raw|flex|simple)-(.+)$"
    )

    i = 0
    while i < len(extra_args):
        arg = extra_args[i]

        match = command_pattern.match(arg)
        if match:
            phase, command, option_name = match.groups()
            if i + 1 < len(extra_args) and not extra_args[i + 1].startswith("--"):
                value = extra_args[i + 1]
                i += 2
            else:
                value = True
                i += 1

            key = (phase, command)
            if key not in delegated:
                delegated[key] = {}
            delegated[key][option_name] = value
            continue

        match = phase_pattern.match(arg)
        if match:
            phase, option_name = match.groups()
            if i + 1 < len(extra_args) and not extra_args[i + 1].startswith("--"):
                value = extra_args[i + 1]
                i += 2
            else:
                value = True
                i += 1

            key = (phase, None)
            if key not in delegated:
                delegated[key] = {}
            delegated[key][option_name] = value
            continue

        i += 1

    return delegated


def build_command_args(
    phase: str,
    command: str,
    delegated_opts: dict[tuple[str, str | None], dict[str, Any]],
    global_terms: list[str] | None,
    use_terms: bool,
) -> list[str]:
    """Build command arguments with delegated options."""
    args: list[str] = []

    cmd_key = (phase, command)
    cmd_opts = delegated_opts.get(cmd_key, {})

    phase_key = (phase, None)
    phase_opts = delegated_opts.get(phase_key, {})

    merged_opts = {**phase_opts, **cmd_opts}

    if use_terms and global_terms:
        for term in global_terms:
            args.extend(["--term", term])

    for opt_name, opt_value in merged_opts.items():
        if isinstance(opt_value, bool):
            if opt_value:
                args.append(f"--{opt_name}")
        elif opt_value is not None:
            if opt_name == "term":
                if isinstance(opt_value, str):
                    expanded = parse_term_list([opt_value])
                    if expanded:
                        for term in expanded:
                            args.extend(["--term", term])
                elif isinstance(opt_value, list):
                    expanded = parse_term_list(opt_value)
                    if expanded:
                        for term in expanded:
                            args.extend(["--term", term])
                else:
                    args.extend([f"--{opt_name}", str(opt_value)])
            else:
                args.extend([f"--{opt_name}", str(opt_value)])

    return args
