# Architecture

| Layer       | In Phase 1                                                                                                                            | Planned                                                   |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| 1 · Core    | Maps, differential drive, wheel odometry, 2D lidar, rigs, scenarios, fixed-step ticks and run metrics                                 | Mapping, localization, planning, control and more sensors |
| 2 · Runtime | `gridbot-run` runs scenarios headless or serves them over Foxglove at 20 Hz. ROS 2 Jazzy builds a `Telemetry` message and empty nodes | ROS wrapper nodes that call the same core functions       |
| 3 · Gateway | Relays allowlisted runtime topics to browsers as JSON and serves the UI                                                               | Decode ROS CDR from `foxglove_bridge` into the same JSON  |
| 4 · Browser | Draws the map, the robot's true pose and lidar returns for each complete tick                                                         | Draw algorithm state such as maps, particles and paths    |

Both runtimes call the same core Python functions. The runner publishes JSON over Foxglove ([decision 0005](decisions/0005-foxglove-json-transport.md)). ROS will use `foxglove_bridge` and CDR, and the gateway will decode both into one JSON format for the UI.

The gateway is the public entry point, and visitors can only watch. The runtime port stays private: Compose publishes only the gateway, on the host's loopback address. Test-only commands require `GRIDBOT_TEST_CONTROL=1` on the gateway, and production leaves it unset.

See the [design](superpowers/specs/2026-11-17-gridbot-design.md) for the full plan and [runtimes](runtimes.md) for each runtime's responsibilities.
