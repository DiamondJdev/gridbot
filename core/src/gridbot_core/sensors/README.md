# Sensors

## What it does

Defines the sensor rig format and simulates 2D lidar scans. A rig lists each sensor's mount and settings, plus wheel odometry noise.

## How it fits

This package belongs to [Layer 1](../../../../docs/architecture.md). The [sensor guide](../../../../docs/sensors.md) describes the rig format, the [lidar page](../../../../docs/algorithms/lidar-ray-casting.md) explains ray casting, and rig files live in [`config/rigs`](../../../../config/rigs/lidar-360.yaml).

## Running its tests

Run `uv run pytest core/tests/test_scenario.py core/tests/test_lidar.py` from the repo root.

## Main files

- `rig.py` defines the rig, lidar and odometry models.
- `lidar.py` casts beams through the map and adds range noise.
