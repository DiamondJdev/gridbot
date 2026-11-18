# Simulation

## What it does

Moves the true robot through the map, detects wall contact, produces noisy wheel odometry and advances complete simulation ticks.

## How it fits

This package belongs to [Layer 1](../../../../docs/architecture.md). The [algorithm page](../../../../docs/algorithms/differential-drive.md) explains the motion model.

## Running its tests

Run `uv run pytest core/tests/test_sim.py core/tests/test_world_step.py` from the repo root.

## Main files

- `drive.py` handles robot limits, wheel slip, arcs and collisions.
- `odometry.py` turns true motion into a noisy pose estimate.
- `world_step.py` follows a scenario script and builds each tick's frame.
