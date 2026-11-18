# Core

## What it does

Exposes the core version and enforces import boundaries. Simulation and navigation code starts in Phase 1.

## How it fits

[Layer 1](../docs/architecture.md) supplies pure Python code to the runner and ROS wrappers.

## Running its tests

Run `uv run pytest core/tests` from the repo root. Run `uv run lint-imports` to check the package itself.

## Main files

- `src/gridbot_core/__init__.py` defines the version.
- `tests/test_boundaries.py` checks the version and exercises the import rules.
