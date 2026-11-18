# 0001 · Layered architecture

## Context

Gridbot needs deterministic Python tests and a ROS runtime that can host reference stacks.

## Decision

Put algorithms in a pure Python core shared by both runtimes. Use the same topic names and fields for their output.

## Consequences

The core runs without ROS, and the ROS wrappers can stay small. Each new runtime has to honor the shared interface.
