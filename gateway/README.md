# Gateway

## What it does

Subscribes once to the runtime and relays allowlisted topics to browsers as JSON. It serves the built UI, `/healthz` and a read-only WebSocket at `/ws`.

Browsers first receive a status message, then the cached `/sim/world` and `/tf_static`, then live topics. A browser that falls more than 1 MiB behind skips tick data but still gets the map. Any message from a browser closes its socket with code 1008, unless `GRIDBOT_TEST_CONTROL=1` is set. In that case `{"op": "step", "count": n}` with `n` from 1 to 1000 is forwarded to the runner. Production must leave that variable unset.

| Variable               | Default               | Purpose                                       |
| ---------------------- | --------------------- | --------------------------------------------- |
| `GRIDBOT_HOST`         | `127.0.0.1`           | Address to listen on (`0.0.0.0` in the image) |
| `GRIDBOT_PORT`         | `8080`                | HTTP and WebSocket port                       |
| `GRIDBOT_RUNTIME_URL`  | `ws://127.0.0.1:8765` | Runtime Foxglove WebSocket                    |
| `GRIDBOT_UI_DIR`       | `../ui/dist`          | Built UI files (`/app/ui` in the image)       |
| `GRIDBOT_TEST_CONTROL` | unset                 | `1` allows test step commands                 |

## How it fits

[Layer 3](../docs/architecture.md) sits between the runtime and browsers. It is the only public entry point. See [decision 0005](../docs/decisions/0005-foxglove-json-transport.md) for the runtime connection.

## Running its tests

Run `pnpm --filter @gridbot/gateway test` from the repo root. Run the `build` script before `start`.

## Main files

- `src/main.ts` reads settings and starts the gateway. `--version` prints the version.
- `src/config.ts` validates environment settings.
- `src/server.ts` serves HTTP and browser sockets and enforces limits.
- `src/relay.ts` caches, filters and fans out runtime messages.
- `src/runtime.ts` subscribes to the runtime and reconnects after it drops.
- `src/static.ts` serves UI files without leaving the UI folder.
- `src/protocol.ts` holds the browser message types and topic allowlist.
