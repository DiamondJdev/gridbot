# Gridbot agent guide

Gridbot is a warehouse robot simulation project. Phase 0 contains package and build scaffolding.

## Where to work

1. `core/` contains pure Python libraries.
2. `runner/` and `ros/` host the libraries in Python or ROS 2.
3. `gateway/` will relay runtime telemetry to browsers.
4. `ui/` will draw the simulation. `e2e/` will exercise it in a browser.

Read the package README, [architecture](docs/architecture.md) and the active plan in [docs/superpowers/plans](docs/superpowers/plans) before changing a layer. Update this guide in the same commit as any change that makes it inaccurate.

## Commands

| Command                                | Purpose                                            |
| -------------------------------------- | -------------------------------------------------- |
| `uv sync --locked`                     | Install the Python workspace and development tools |
| `pnpm install --frozen-lockfile`       | Install the TypeScript workspace                   |
| `make help`                            | List the Make targets                              |
| `make verify`                          | Run Python, docs and TypeScript checks             |
| `make verify-ros`                      | Build the ROS image and run colcon tests           |
| `make verify-all`                      | Run both checks, then the Compose smoke test       |
| `uv run pre-commit run --all-files`    | Run the local hooks                                |
| `uv run gridbot-run --version`         | Print the runner version                           |
| `pnpm --filter @gridbot/gateway start` | Print the gateway version after building it        |

[Testing](docs/testing.md) lists the individual checks and their logs.

## Core rules

- Keep ROS, networking and runtime imports out of `gridbot_core`. File access belongs in world or scenario loading.
- Pass time and seeded random generators in from the caller. Avoid mutable global state.
- Return new state without mutating inputs. A function may fill a fresh NumPy array before returning it. Document why it does so.
- Type public functions, document units and keep functions under 50 lines and files under 400. Pyright runs in strict mode.
- Watch a test fail before changing behavior. Use conventional commit prefixes.

## Repository boundaries

- Keep Gridbot independent of other projects. Read runtime settings from the environment and keep secrets out of Git.
- Keep the visitor interface read-only. Production must leave `GRIDBOT_TEST_CONTROL` unset.
- Keep docs alongside code. Use the required README sections and the Humanizer skill for prose.
- Run `make verify` after changes. Review the phase diff and run `make verify-all` before a PR.
- Get owner approval before creating a GitHub repo, pushing, changing repository settings or deploying.
