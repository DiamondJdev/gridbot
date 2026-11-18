# Assets

## What it does

Holds map PNG and YAML pairs and their attribution.

## How it fits

The core world loader reads these maps. See the [architecture](../docs/architecture.md).

## Running its tests

Run `uv run pytest core/tests/test_world.py` from the repo root.

## Main files

- `warehouse-01.png` and `warehouse-01.yaml` form a 20 m by 12 m warehouse map.
- [`ATTRIBUTION.md`](ATTRIBUTION.md) records where the maps come from.
