# Sensors

## What it does

Defines the sensor rig format. A rig lists each sensor's mount and settings, plus wheel odometry noise.

## How it fits

This package belongs to [Layer 1](../../../../docs/architecture.md). The [sensor guide](../../../../docs/sensors.md) describes the rig format, and rig files live in [`config/rigs`](../../../../config/rigs/lidar-360.yaml).

## Running its tests

Run `uv run pytest core/tests/test_scenario.py` from the repo root.

## Main files

- `rig.py` defines the rig, lidar and odometry models.
