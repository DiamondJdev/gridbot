# Runner

## What it does

Provides the `gridbot-run` command. It runs a scenario headless, prints its metrics and can write a per-tick trace.

```bash
uv run gridbot-run scenarios/drive-01.json --json --trace artifacts/drive-01.jsonl
```

It exits with 0 when every threshold passes, 1 when one fails and 2 for invalid input.

`--serve` publishes the run over the Foxglove WebSocket protocol at 20 Hz, on `127.0.0.1:8765` unless `--host` or `--port` says otherwise. It restarts the scenario after the last tick. Each tick sends ROS-shaped JSON on `/scan/<sensor>`, `/odom`, `/tf`, `/sim/ground_truth`, `/cmd_vel` and `/telemetry`, which comes last. `/sim/world` and `/tf_static` repeat every 20 ticks. Lidar beams with no return are `null`.

`--test-control` publishes one frame per step request, so the first request publishes tick 0. Step requests are JSON `{"count": n}` messages on `/test/step`, with `n` from 1 to 1000. Without this flag the runner does not accept client messages.

## How it fits

The runner is the plain Python runtime in [Layer 2](../docs/architecture.md).

## Running its tests

Run `uv run pytest runner/tests` from the repo root.

## Main files

- `src/gridbot_runner/cli.py` handles arguments, output and exit codes.
- `src/gridbot_runner/headless.py` loads a run, steps it and builds reports and traces.
- `src/gridbot_runner/messages.py` turns frames into ROS-shaped JSON messages.
- `src/gridbot_runner/live.py` paces live runs, queues test steps and runs the Foxglove server.
- `tests/test_cli.py` checks the version flag and serve options.
- `tests/test_messages.py` checks message fields, order and JSON safety.
- `tests/test_live.py` checks pacing, test stepping and restarts.
- `tests/test_headless.py` checks `drive-01`, repeatability and input errors.
