"""Get the claude-pre-commit config from the pyproject.toml file."""

import json
import sys
from pathlib import Path

import tomllib


def main() -> None:
    """Get the claude-pre-commit config from the pyproject.toml file."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found", file=sys.stderr)
        sys.exit(1)

    try:
        with pyproject_path.open("rb") as f:
            pyproject = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        print(f"Error: Invalid TOML in pyproject.toml: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        claude_pre_commit = pyproject["tool"]["claude-pre-commit"]
    except KeyError:
        print(
            "Error: [tool.claude-pre-commit] section not found in pyproject.toml",
            file=sys.stderr,
        )
        sys.exit(1)

    print(json.dumps(claude_pre_commit, indent=2))


if __name__ == "__main__":
    main()
