"""Command line entry point for the Python runner."""

import argparse
import json
import sys
from collections.abc import Sequence
from contextlib import ExitStack
from pathlib import Path

from gridbot_core import __version__
from gridbot_core.scenario.loader import ScenarioError

from gridbot_runner.headless import HeadlessResult, load_run, report, run_headless

EXIT_PASSED = 0
EXIT_FAILED = 1
EXIT_INVALID = 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gridbot-run")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument("scenario", type=Path, help="scenario JSON file")
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    parser.add_argument("--trace", type=Path, help="write one JSON line per tick")
    return parser


def _summary(name: str, result: HeadlessResult) -> str:
    metrics = result.metrics
    status = "failed: " + "; ".join(metrics.failures) if metrics.failures else "passed"
    return (
        f"{name}: {status} (ticks {metrics.ticks}, collisions {metrics.collisions},"
        f" path {metrics.path_length_m:.2f} m, end error {metrics.end_error_m:.3f} m,"
        f" odometry error {metrics.odom_error_m:.3f} m)"
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run a scenario headless and return 0 passed, 1 failed or 2 invalid."""
    args = _parser().parse_args(argv)
    try:
        run = load_run(args.scenario)
        with ExitStack() as stack:
            trace = None
            if args.trace is not None:
                trace = stack.enter_context(
                    args.trace.open("w", encoding="utf-8", newline="\n")
                )
            result = run_headless(run, trace)
    except (ScenarioError, OSError) as error:
        print(f"gridbot-run: {error}", file=sys.stderr)
        return EXIT_INVALID
    if args.json:
        print(json.dumps(report(run.scenario, result), allow_nan=False))
    else:
        print(_summary(run.scenario.name, result))
    return EXIT_FAILED if result.metrics.failures else EXIT_PASSED
