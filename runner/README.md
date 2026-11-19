# Runner

## What it does

Provides the `gridbot-run` command. It runs a scenario headless, prints its metrics and can write a per-tick trace.

```bash
uv run gridbot-run scenarios/drive-01.json --json --trace artifacts/drive-01.jsonl
```

It exits with 0 when every threshold passes, 1 when one fails and 2 for invalid input.

## How it fits

The runner is the plain Python runtime in [Layer 2](../docs/architecture.md).

## Running its tests

Run `uv run pytest runner/tests` from the repo root.

## Main files

- `src/gridbot_runner/cli.py` handles arguments, output and exit codes.
- `src/gridbot_runner/headless.py` loads a run, steps it and builds reports and traces.
- `tests/test_cli.py` checks the version flag.
- `tests/test_headless.py` checks `drive-01`, repeatability and input errors.
