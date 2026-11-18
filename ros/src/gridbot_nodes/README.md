# gridbot_nodes

## What it does

Reserves the ROS package for algorithm wrappers.

## How it fits

These [Layer 2](../../../docs/architecture.md) wrappers will convert ROS messages to core types and publish the results.

## Running its tests

Run `make verify-ros` from the repo root.

## Main files

- `setup.py` installs the package and its ROS metadata.
- `test/test_core_available.py` checks that the ROS image can import the core library.
