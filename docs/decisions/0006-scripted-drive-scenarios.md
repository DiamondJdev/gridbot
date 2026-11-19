# 0006 · Scripted drive scenarios

## Context

The [design](../superpowers/specs/2026-11-17-gridbot-design.md) lists three modes: explore, localize and slam. Phase 1 has no algorithms for any of them yet. It still needs a repeatable run that moves the robot past walls and shelves, so the simulator, lidar, odometry, runner, gateway and UI can be tested end to end.

## Decision

Add a fourth mode, `drive`. A drive scenario lists segments under `drive`, and each segment holds a command (`v` in m/s, `omega` in rad/s) for a number of ticks. The robot runs the list open loop and stops when the list ends. The loader rejects a script longer than `maxTicks`.

A drive scenario uses its own thresholds: `collisions`, `minPathLengthM`, `endWithinM` and `maxOdomErrorM`. `mode` is a literal, so a new mode must add its own value and its own threshold model.

`drive-01` is the first scenario. With seed 42 it runs 1128 ticks, drives 40.0 m with no collisions and ends within a micrometre of its start. Its odometry error is 0.78 m against a 1.0 m limit.

## Consequences

The headless runner, the live runner and the browser test all use the same file, so a change to motion, sensing or message fields shows up in all three. True motion depends only on the script, and odometry noise depends only on the seed. Changing the seed changes the odometry error and leaves the true path unchanged.

The robot does not react to what it senses in this mode. Scenario events, such as an obstacle added during the run, do not apply to drive scenarios. When Phase 2 adds explore mode, the scenario model becomes a union keyed by `mode`. Drive scenarios stay as regression tests for the simulator and sensors.
