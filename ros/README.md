# ROS 2 workspace

## What it does

Builds four packages with colcon in a ROS 2 Jazzy container.

## How it fits

ROS is the second [Layer 2 runtime](../docs/architecture.md). Its wrappers will use the same core library as the Python runner.

## Running its tests

Run `make verify-ros` from the repo root.

## Main files

- [gridbot_msgs](src/gridbot_msgs/README.md) defines ROS messages.
- [gridbot_sim](src/gridbot_sim/README.md) is the simulator package.
- [gridbot_nodes](src/gridbot_nodes/README.md) is the algorithm wrapper package.
- [gridbot_bringup](src/gridbot_bringup/README.md) contains the launch file.
