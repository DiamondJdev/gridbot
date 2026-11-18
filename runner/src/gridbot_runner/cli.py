"""Command line entry point for the Python runner."""

import argparse
from collections.abc import Sequence

from gridbot_core import __version__


def main(argv: Sequence[str] | None = None) -> int:
    """Parse runner arguments and return an exit status."""
    parser = argparse.ArgumentParser(prog="gridbot-run")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.parse_args(argv)
    return 0
