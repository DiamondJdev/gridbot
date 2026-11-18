# gridbot_bringup

## What it does

Installs the launch file for the ROS workspace. In Phase 0 it starts zero nodes.

## How it fits

The launch file will assemble the [ROS runtime](../../../docs/architecture.md).

## Running its tests

Run `make verify-ros` from the repo root.

## Main files

- `launch/gridbot.launch.py` returns an empty launch description.
- `test/test_launch.py` loads the installed launch file.
