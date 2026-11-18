# gridbot_sim

## What it does

Reserves the ROS package for the simulator node.

## How it fits

This [Layer 2](../../../docs/architecture.md) package will publish the clock, sensor readings and ground truth in Phase 5.

## Running its tests

Run `make verify-ros` from the repo root.

## Main files

- `setup.py` installs the package and its ROS metadata.
- `test/test_package.py` checks that Python can import it.
