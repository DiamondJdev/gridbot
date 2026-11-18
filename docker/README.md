# Docker

## What it does

Builds the gateway, Python runner and ROS workspace. Each container runs a short command and exits. No service publishes a port in Phase 0.

## How it fits

Compose groups [Layer 2](../docs/architecture.md) runtimes into `runner` and `ros` profiles. Both include the Layer 3 gateway.

## Running its tests

Run `bash scripts/e2e_compose.sh` from the repo root to build and check both profiles. The script removes its Compose project on exit.

## Main files

- `compose.yaml` defines the services and profiles.
- `runner.Dockerfile` installs the Python workspace without development dependencies.
- `ros.Dockerfile` installs the core and builds the Jazzy workspace.
- `gateway.Dockerfile` builds the gateway and runs it as the `node` user.
