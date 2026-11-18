# 0004 · Ruff for Python lint

## Context

The core, runner and ROS packages use Python.

## Decision

Run Ruff across the repository and omit ament flake8 tests. Keep ROS package tests in colcon.

## Consequences

One configuration covers Python style. Colcon reports runtime and package test results.
