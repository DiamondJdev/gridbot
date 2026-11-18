# World

## What it does

Loads occupancy maps and converts between world coordinates in meters and grid cells.

## How it fits

This package belongs to [Layer 1](../../../../docs/architecture.md). The simulator and sensors read the immutable `GridMap` it returns.

## Running its tests

Run `uv run pytest core/tests/test_world.py` from the repo root.

## Main files

- `grid.py` defines `GridMap` and its coordinate helpers.
- `loader.py` reads the ROS `map_server` PNG and YAML format.
