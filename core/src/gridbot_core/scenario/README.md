# Scenario

## What it does

Defines scenario files and loads scenarios and sensor rigs. Invalid files raise `ScenarioError` with the path and field.

## How it fits

This package belongs to [Layer 1](../../../../docs/architecture.md). Runtimes use it to start the same repeatable run.

## Running its tests

Run `uv run pytest core/tests/test_scenario.py` from the repo root.

## Main files

- `models.py` defines the scenario format, including the scripted `drive` list.
- `loader.py` reads JSON scenarios and YAML rigs.
