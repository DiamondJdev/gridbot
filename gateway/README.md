# Gateway

## What it does

Prints the gateway version in Phase 0.

## How it fits

[Layer 3](../docs/architecture.md) will relay runtime telemetry to browsers in Phase 1.

## Running its tests

Run `pnpm --filter @gridbot/gateway test` from the repo root. Run the `build` script before `start`.

## Main files

- `src/index.ts` formats the version line.
- `src/main.ts` prints it.
- `tsconfig.build.json` compiles the entry point into `dist/`.
