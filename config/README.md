# Configuration

## What it does

Holds sensor rig YAML. Run settings and playlists arrive in later phases.

## How it fits

Scenarios name a rig from this folder. The runner image copies it, and the runner publishes each sensor mount on `/tf_static`. See the [architecture](../docs/architecture.md).

## Running its tests

Run `uv run pytest core/tests/test_scenario.py` to load the rigs.

## Main files

- `rigs/lidar-360.yaml` is the baseline single-lidar rig.
