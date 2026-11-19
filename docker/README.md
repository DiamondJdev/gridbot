# Docker

## What it does

Builds the gateway, Python runner and ROS workspace. `docker compose -f docker/compose.yaml --profile runner up` runs drive-01 live and serves the app at http://localhost:8080. The gateway is the only published port, and only on the host's loopback address. The runner's port stays inside the Compose network.

## How it fits

Compose groups [Layer 2](../docs/architecture.md) runtimes into `runner` and `ros` profiles. Both include the Layer 3 gateway, which serves the built UI. In the `runner` profile the gateway connects to `ws://runner:8765`. Test control stays off in Compose.

## Running its tests

Run `bash scripts/e2e_compose.sh` from the repo root. It builds both profiles and checks the runner, gateway and ROS entry points. Then it starts the runner and gateway and passes once the gateway reports a connected runtime with an advancing stamp. The script removes its Compose project on exit.

## Main files

- `compose.yaml` defines the services, profiles and the gateway's port.
- `runner.Dockerfile` installs the Python workspace without development dependencies, adds the scenarios, maps and rigs, and serves drive-01 as `nobody`.
- `ros.Dockerfile` installs the core and builds the Jazzy workspace.
- `gateway.Dockerfile` builds the UI and gateway, keeps only production dependencies and runs as the `node` user.
