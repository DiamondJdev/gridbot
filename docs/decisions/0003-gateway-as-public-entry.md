# 0003 · Gateway as public entry point

## Context

The runtime bridge can accept topic publications. Visitors only need to see telemetry.

## Decision

Keep the runtime bridge private. Give the gateway one upstream connection and relay only allowed telemetry as browser JSON.

## Consequences

Both runtimes can serve the same UI. The gateway handles browser fan-out, so visitors do not add runtime connections.
