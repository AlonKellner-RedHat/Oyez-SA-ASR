"""The first tests of the repository."""

from oyez_sa_asr import __version__, example


def test_version_exists() -> None:
    """Ensure that there is a version."""
    assert __version__ is not None


def test_example() -> None:
    """Ensure that the example function works."""
    example()
