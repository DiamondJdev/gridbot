# UI

## What it does

Exposes a version string. The browser app starts in Phase 1.

## How it fits

[Layer 4](../docs/architecture.md) will draw the simulation from gateway messages.

## Running its tests

Run `pnpm --filter @gridbot/ui test` from the repo root.

## Main files

- `src/index.ts` formats the version line.
- `tests/index.test.ts` checks the version line.
