# Scenarios

## What it does

Holds scenario files. Each one names a map, rig, mode, seed, start pose, drive script and pass thresholds.

## How it fits

The headless runner checks every scenario here. ROS and browser tests will use the same files. See the [architecture](../docs/architecture.md).

## Running its tests

Run `uv run gridbot-run scenarios/drive-01.json`. `make verify` runs every scenario.

## Main files

- `drive-01.json` drives a scripted loop around the center shelves.
