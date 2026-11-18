# End-to-end tests

## What it does

Holds a package smoke test for Phase 0. Browser tests start in Phase 1.

## How it fits

Playwright will test all four [layers](../docs/architecture.md) through the browser. Phase 0 checks the container entry points with `scripts/e2e_compose.sh`.

## Running its tests

Run `pnpm --filter @gridbot/e2e test` from the repo root.

## Main files

- `src/index.ts` formats the version line.
- `tests/index.test.ts` checks the version line.
