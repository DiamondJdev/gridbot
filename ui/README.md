# UI

## What it does

Draws the live simulation in the browser: the occupancy map with north up, the robot's true pose and the lidar returns, plus a header with the tick, sim time, collisions, path length and connection state. Visitors only watch. The page sends nothing unless it was opened with `?test=1` against a gateway that has test control.

## How it fits

[Layer 4](../docs/architecture.md). The gateway serves the built files from `ui/dist` and relays runtime messages over `/ws`. The page groups them into ticks: `/telemetry` closes a tick, and the tick is drawn only when the ground-truth pose and every scan carry its stamp, so rays never attach to an older pose. Each animation frame draws the newest complete tick with no interpolation. The map is drawn once onto an offscreen canvas and reused.

With `?test=1` the page adds `window.__gridbot` with `getState()`, `waitForTick(tick)` and `step(count)`. `step` splits large counts into gateway-sized commands. End-to-end tests use it; production gateways leave `GRIDBOT_TEST_CONTROL` unset, so the gateway closes any socket that sends a step.

## Running its tests

Run `pnpm --filter @gridbot/ui test` from the repo root. `pnpm --filter @gridbot/ui build` writes `ui/dist`. For development, `pnpm --filter @gridbot/ui dev` serves the page and proxies `/ws` to a gateway on `GRIDBOT_PORT` (8080 by default).

## Main files

- `src/parse.ts` checks gateway JSON and pulls out the fields the view draws.
- `src/frames.ts` groups messages into complete ticks without mutating state.
- `src/view.ts` maps metres to canvas pixels with north at the top.
- `src/render.ts` computes ray geometry from the lidar mount and paints the canvas.
- `src/testApi.ts` installs the `?test=1` hooks.
- `src/main.ts` connects, reconnects and runs the draw loop.
