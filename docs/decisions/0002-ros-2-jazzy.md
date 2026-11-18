# 0002 · ROS 2 Jazzy

## Context

Gridbot needs ROS 2 for tooling and reference implementations. Development and planned hosting both use Arm hardware.

## Decision

Build and test ROS 2 Jazzy in the official Docker image. Keep the core and runner on Python 3.12.

## Consequences

ROS tests require Docker. The plain Python workspace can run on its own.
