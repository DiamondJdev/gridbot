# Metrics

## What it does

Scores a finished scripted drive and names every missed scenario threshold.

## How it fits

This package belongs to [Layer 1](../../../../docs/architecture.md). Runtimes use the same scoring code, so their results can be compared.

## Running its tests

Run `uv run pytest core/tests/test_world_step.py` from the repo root.

## Main files

- `run.py` calculates path length, end error, odometry error and threshold failures.
