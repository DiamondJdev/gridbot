# Gridbot agent guide

Gridbot is a warehouse robot simulation project. In Phase 1 a scripted robot drives `drive-01`, and the browser draws the map, robot and lidar from live runner data.

## Where to work

1. `core/` contains pure Python libraries.
2. `runner/` and `ros/` host the libraries in Python or ROS 2.
3. `gateway/` relays runtime telemetry to browsers and serves the UI.
4. `ui/` draws the simulation from gateway messages. `e2e/` runs drive-01 through all of them in Playwright.

Read the package README, [architecture](docs/architecture.md) and the active plan in [docs/superpowers/plans](docs/superpowers/plans) before changing a layer. Update this guide in the same commit as any change that makes it inaccurate.

## Commands

| Command                                                       | Purpose                                                 |
| ------------------------------------------------------------- | ------------------------------------------------------- |
| `uv sync --locked`                                            | Install the Python workspace and development tools      |
| `pnpm install --frozen-lockfile`                              | Install the TypeScript workspace                        |
| `make help`                                                   | List the Make targets                                   |
| `make verify`                                                 | Run Python, docs and TypeScript checks                  |
| `make verify-ros`                                             | Build the ROS image and run colcon tests                |
| `make verify-all`                                             | Run both checks, then the Compose smoke test            |
| `uv run pre-commit run --all-files`                           | Run the local hooks                                     |
| `uv run gridbot-run --version`                                | Print the runner version                                |
| `uv run gridbot-run scenarios/drive-01.json --json`           | Run a scenario headless and print metrics               |
| `pnpm --filter @gridbot/gateway start`                        | Start the gateway after building it                     |
| `pnpm --filter @gridbot/ui dev`                               | Serve the UI with `/ws` proxied to the gateway          |
| `pnpm --filter @gridbot/e2e exec playwright install chromium` | Install the browser for the Playwright test once        |
| `pnpm --filter @gridbot/e2e e2e`                              | Run the browser test against a fresh runner and gateway |
| `docker compose -f docker/compose.yaml --profile runner up`   | Serve the live app at http://localhost:8080             |

[Testing](docs/testing.md) lists the individual checks and their logs.

## Run the stack

With Docker, `docker compose -f docker/compose.yaml --profile runner up` serves the app at http://localhost:8080.

Without Docker, run `pnpm -r build`, then start `uv run gridbot-run scenarios/drive-01.json --serve` and `pnpm --filter @gridbot/gateway start` in two terminals and open http://127.0.0.1:8080. If Python imports fail with "No module named gridbot_core", macOS has hidden the `.venv` files. Run `chflags -R nohidden .venv` and try again.

Browser tests need test control. Playwright starts its own runner with `--test-control` and a gateway with `GRIDBOT_TEST_CONTROL=1`, on ports 18765 and 18080.

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
