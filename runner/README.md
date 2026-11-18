# Runner

## What it does

Provides the `gridbot-run` command. Phase 0 supports `--version`.

## How it fits

The runner is the plain Python runtime in [Layer 2](../docs/architecture.md).

## Running its tests

Run `uv run pytest runner/tests` from the repo root.

## Main files

- `src/gridbot_runner/cli.py` handles command-line arguments.
- `tests/test_cli.py` checks the version flag.
