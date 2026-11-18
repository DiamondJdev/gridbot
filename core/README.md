# Core

## What it does

Holds the shared state types, sensor rig format and scenario loader. Import rules keep this package free of ROS and networking.

## How it fits

[Layer 1](../docs/architecture.md) supplies pure Python code to the runner and ROS wrappers.

## Running its tests

Run `uv run pytest core/tests` from the repo root. Run `uv run lint-imports` to check the package itself.

## Main files

- `src/gridbot_core/__init__.py` defines the version.
- `src/gridbot_core/types.py` defines poses, velocities and the 20 Hz tick.
- [`sensors`](src/gridbot_core/sensors/README.md) defines rigs.
- [`scenario`](src/gridbot_core/scenario/README.md) defines and loads scenarios.
- `tests/test_boundaries.py` checks the version and exercises the import rules.
- `tests/test_scenario.py` checks config loading and its error messages.
