# Gridbot

Gridbot is a warehouse robot simulation project. The robot will explore, map and navigate a warehouse while a browser shows what its algorithms see and do.

In Phase 1 a scripted robot drives the `drive-01` scenario through a simulated warehouse, and the browser draws the map, the robot and its lidar from live runner data. The robot does not map, localize, plan or avoid obstacles yet.

## Quick start

Install Python 3.12, uv 0.9.5, Node 24, pnpm 12.21.0 and Docker with Compose. From the repo root, run:

```sh
uv sync --locked
pnpm install --frozen-lockfile
make verify-all
```

Use `make verify` for checks that run without Docker. Install the browser for the Playwright test once with `pnpm --filter @gridbot/e2e exec playwright install chromium`.

To watch the simulation, start the stack and open http://localhost:8080:

```sh
docker compose -f docker/compose.yaml --profile runner up
```

To run a scenario headless with metrics and a per-tick trace:

```sh
uv run gridbot-run scenarios/drive-01.json --json --trace artifacts/drive-01.jsonl
```

## Layers

```text
Browser UI
    ↑  JSON over WebSocket
Gateway
    ↑  Foxglove protocol
Python runner or ROS 2
    ↓  Python calls
Gridbot core
```

## Repository map

| Path                                                                                     | What lives there                                 |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------ |
| [core](core/README.md)                                                                   | Pure Python libraries and their import checks    |
| [runner](runner/README.md), [ros](ros/README.md)                                         | Python and ROS 2 runtimes                        |
| [gateway](gateway/README.md), [ui](ui/README.md), [e2e](e2e/README.md)                   | Gateway, browser app and browser test packages   |
| [docker](docker/README.md), [scripts](scripts/README.md)                                 | Container builds and local checks                |
| [config](config/README.md), [assets](assets/README.md), [scenarios](scenarios/README.md) | Sensor rigs, maps and scenario files             |
| [deploy](deploy/README.md)                                                               | Reserved for a later phase                       |
| [docs](docs/README.md)                                                                   | Architecture, testing, decisions and phase notes |

See [testing](docs/testing.md) for commands and log locations.
