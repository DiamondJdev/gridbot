# Runtimes

## Current state

The Python runner runs scenarios headless and serves them over Foxglove with `--serve`. Live runs are paced at 20 Hz and restart after the last tick. With `--test-control`, the runner publishes one tick per step request instead, so browser tests see exact ticks. See the [runner README](../runner/README.md).

ROS 2 Jazzy builds the message package and three Python packages. The launch file returns an empty launch description.

The Compose `runner` profile runs the runner live with the gateway in front of it. Scenarios use the scripted `drive` mode from [decision 0006](decisions/0006-scripted-drive-scenarios.md).

## Planned contract

The Python runner advances a scenario at a fixed 20 Hz without a wall clock. Its headless mode runs as fast as the CPU allows and reports metrics as JSON. ROS wraps the same Python functions in nodes with simulated time.

Both runtimes publish the [same topics and fields](superpowers/specs/2026-11-17-gridbot-design.md#topics-and-messages). During ROS scenario tests, the simulator waits for each Gridbot node to report `/sim/tick_done` before the next tick. Live runs advance without that wait.

Reference algorithms run in ROS. A shadow stack publishes under `/reference`, publishes no transforms and cannot actuate the robot. Comparisons use single-lidar rigs.

A scenario supplies the map, sensor rig, mode and seed. A run config chooses a runtime and algorithms and may override those four scenario values. Scenario thresholds apply when all four values come from the scenario.

## Adding a runtime

Use the existing core types and topic fields, then document the runtime's clock and test behavior. Check that the gateway can read its messages and that shared scenarios produce results within their tolerances.
