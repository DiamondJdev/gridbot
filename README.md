# Gridbot

Gridbot is a warehouse robot simulation project. The robot will explore, map and navigate a warehouse while a browser shows what its algorithms see and do.

Phase 0 sets up the packages, checks and container images. The robot and browser app start in Phase 1.

## Quick start

Install Python 3.12, uv 0.9.5, Node 24, pnpm 12.21.0 and Docker with Compose. From the repo root, run:

```sh
uv sync --locked
pnpm install --frozen-lockfile
make verify-all
```

Use `make verify` for checks that run without Docker.

## Layers

```text
Browser UI
    ↑  planned JSON over WebSocket
Gateway
    ↑  planned Foxglove protocol
Python runner or ROS 2
    ↓  Python calls
Gridbot core
```

## Repository map

| Path                                                                                                                 | What lives there                                 |
| -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| [core](core/README.md)                                                                                               | Pure Python libraries and their import checks    |
| [runner](runner/README.md), [ros](ros/README.md)                                                                     | Python and ROS 2 runtimes                        |
| [gateway](gateway/README.md), [ui](ui/README.md), [e2e](e2e/README.md)                                               | Gateway, browser app and browser test packages   |
| [docker](docker/README.md), [scripts](scripts/README.md)                                                             | Container builds and local checks                |
| [config](config/README.md), [assets](assets/README.md), [scenarios](scenarios/README.md), [deploy](deploy/README.md) | Reserved directories for later phases            |
| [docs](docs/README.md)                                                                                               | Architecture, testing, decisions and phase notes |

See [testing](docs/testing.md) for commands and log locations.
