# Simulation

## What it does

Moves the true robot through the map, detects wall contact and produces noisy wheel odometry.

## How it fits

This package belongs to [Layer 1](../../../../docs/architecture.md). The [algorithm page](../../../../docs/algorithms/differential-drive.md) explains the motion model.

## Running its tests

Run `uv run pytest core/tests/test_sim.py` from the repo root.

## Main files

- `drive.py` handles robot limits, wheel slip, arcs and collisions.
- `odometry.py` turns true motion into a noisy pose estimate.
