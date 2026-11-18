# gridbot_msgs

## What it does

Defines the stamped `Telemetry` message for named numeric readings.

## How it fits

The [ROS runtime](../../../docs/architecture.md) uses this package for Gridbot-specific messages.

## Running its tests

Run `make verify-ros` from the repo root.

## Main files

- `msg/Telemetry.msg` defines the message fields.
- `test/test_telemetry.py` constructs a generated message.
