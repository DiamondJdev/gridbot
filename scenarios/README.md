# Scenarios

## What it does

Holds scenario files. Each one names a map, rig, mode, seed, start pose, drive script and pass thresholds.

## How it fits

The headless runner checks every scenario here, and the Playwright test runs `drive-01` through the browser. ROS tests will use the same files. [Decision 0006](../docs/decisions/0006-scripted-drive-scenarios.md) explains the `drive` mode. See the [architecture](../docs/architecture.md).

## Running its tests

Run `uv run gridbot-run scenarios/drive-01.json`. `make verify` runs every scenario.

## Main files

- `drive-01.json` drives a scripted loop around the center shelves.
