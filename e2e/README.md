# End-to-end tests

## What it does

Runs drive-01 through the real runner, gateway and UI in headless Chromium. One test steps the simulator to ticks 0, 350 and 1128 and checks that every lidar return lands within 0.15 m of an occupied cell and that the robot is drawn at its pose. The other checks that the final pose and collision count match `gridbot-run --json` for the same scenario. Any console error, page error or failed request fails the run.

## How it fits

Playwright tests all four [layers](../docs/architecture.md) through the browser. Before the tests, it starts the runner with `--serve --test-control` on port 18765. It also builds the UI and gateway and starts the gateway with `GRIDBOT_TEST_CONTROL=1` on port 18080. The tests drive the page through `window.__gridbot`, which the UI only installs with `?test=1`. `scripts/e2e_compose.sh` checks the Compose images separately.

## Running its tests

Install the browser once with `pnpm --filter @gridbot/e2e exec playwright install chromium`, then run `pnpm --filter @gridbot/e2e e2e` from the repo root. Screenshots go to `artifacts/e2e/`, and traces of failed tests to `artifacts/playwright/`.

## Main files

- `playwright.config.ts` starts the runner and gateway and sets the base URL.
- `tests/drive-01.spec.ts` holds both browser tests.
