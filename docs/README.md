# Documentation

## What it does

Describes the code, planned contracts and decisions for each phase.

## How it fits

The [architecture](architecture.md) page maps packages to layers and records which interfaces exist today.

## Running its tests

Run `uv run python scripts/check_docs.py` from the repo root.

## Main files

- [Architecture](architecture.md) describes the package boundaries.
- [Runtimes](runtimes.md) and [sensors](sensors.md) document planned contracts.
- [Differential drive](algorithms/differential-drive.md) and [lidar ray casting](algorithms/lidar-ray-casting.md) explain the implemented methods.
- [Testing](testing.md) lists the checks and logs.
- [Decisions](decisions/) and the [phase journal](journal/) record changes.
