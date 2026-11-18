# Architecture

| Layer       | In Phase 0                                                                            | Planned                                                                         |
| ----------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| 1 · Core    | Python package with a version and import restrictions                                 | Simulation, sensor models, mapping, localization, planning, control and metrics |
| 2 · Runtime | Python version command and ROS 2 Jazzy workspace with a generated `Telemetry` message | Fixed-step Python runtime and ROS wrapper nodes                                 |
| 3 · Gateway | TypeScript version command in a non-root container                                    | Translate runtime messages to JSON and relay allowed telemetry                  |
| 4 · Browser | TypeScript package and a unit test                                                    | Draw the robot and algorithm state from gateway messages                        |

Both runtimes will call the same core Python functions. The runner will publish JSON over Foxglove. ROS will use `foxglove_bridge` and CDR. The gateway will decode both and expose one JSON format to the UI.

The gateway is the planned public entry point. Visitors can only watch. The internal bridge must stay private. Test-only commands require `GRIDBOT_TEST_CONTROL=1` on the gateway, and production leaves it unset.

See the [design](superpowers/specs/2026-11-17-gridbot-design.md) for the full plan and [runtimes](runtimes.md) for each runtime's responsibilities.
