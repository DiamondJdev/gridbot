# Testing

| Target            | What it runs                                                                                                                                                                            |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `make help`       | Lists the Make targets                                                                                                                                                                  |
| `make verify`     | Python lint, formatting, types, import boundaries, pytest and every scenario through `gridbot-run`, then docs, TypeScript lint, formatting, types, Vitest and the gateway and UI builds |
| `make verify-ros` | Builds the ROS Compose service and runs `colcon test` and `colcon test-result --verbose` inside it                                                                                      |
| `make verify-all` | Runs both verification targets, then builds both Compose profiles and checks their one-shot services                                                                                    |

## Debugging a failure

1. Open the failed step's log under `artifacts/logs/`. For example, `python types` writes `python-types.log`.
2. Run the command for that step from the repo root. The [Makefile](../Makefile) lists each command.
3. Rerun the same Make target after the fix. Each target stops at its first failed step.

The step script prints the last 40 log lines on failure and returns the command's exit code. ROS tests run in Docker. The host pytest suite collects `core/tests`, `runner/tests` and `scripts/tests`.

`uv run gridbot-run <scenario> --trace out.jsonl` writes one JSON line per tick with the true pose, odometry pose and error, command, collisions and path length. Browser coverage arrives later in Phase 1.
