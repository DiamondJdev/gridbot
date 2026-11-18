# Scripts

## What it does

Holds the scripts used by local checks and CI.

## How it fits

These tools check the repository across all [layers](../docs/architecture.md).

## Running its tests

Run `uv run pytest scripts/tests` from the repo root.

## Main files

- `check_docs.py` checks required READMEs and local Markdown links.
- `step.sh` logs a command and prints its result.
- `e2e_compose.sh` builds and checks both Compose profiles.
