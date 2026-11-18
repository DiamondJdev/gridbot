# Phase 1: World, Sim and Live View Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A scripted robot drives `drive-01` through a simulated warehouse, and the browser draws the map, the robot and its lidar from live runner data.

**Architecture:** `gridbot_core` gains pure world, sim, sensor, scenario and metric code. The runner steps it at a fixed 20 Hz, either headless or through a Foxglove WebSocket server. The gateway is the runner's only client and relays allowlisted topics to browsers as JSON. The UI draws complete ticks on a canvas.

**Tech Stack:** Python 3.12, NumPy 1.26.x, Pydantic 2, Pillow, PyYAML, Foxglove SDK; Node 24, `ws`, `@foxglove/ws-protocol`, Vite, Canvas 2D, Playwright.

**Spec:** `docs/superpowers/specs/2026-11-17-gridbot-design.md`

**Done when:** `drive-01` passes in the runner and in Playwright. **Looks right when:** the robot drives smoothly and rays stop at walls.

## Global Constraints

- `gridbot_core` has no ROS, network, `random` or `time` imports. File access stays in world and scenario loading.
- Randomness comes from a seeded `numpy.random.Generator` passed in by the caller.
- Functions return new state. A fresh NumPy array may be filled in place, with a one-line comment saying why.
- Public functions are typed and documented with units. Functions stay under 50 lines, files under 400. Pyright runs in strict mode.
- NumPy is pinned to `>=1.26,<1.27` because the ROS image cannot replace its apt copy.
- The UI draws real algorithm state with no tweening. Visitors can only watch.
- `GRIDBOT_TEST_CONTROL=1` is the only way to enable test commands. Production leaves it unset.
- The runner's Foxglove port is never published outside the Compose network.
- Each package and core subpackage README has the four required headings. Run `humanizer:humanizer` on prose.
- Pushing and opening a PR need the owner's approval.

## Review Focus

1. The gateway starts before the runner, or the runner restarts. Browsers see "runtime offline", then recover without a reload. Test in Task 8.
2. A browser reads slowly. The gateway drops its tick data, keeps serving others and never drops the map. Test in Task 8.
3. A scenario or rig file is malformed, names a missing map or starts the robot in a wall. The CLI exits 2 with a message naming the file and field. Test in Tasks 2, 5 and 6.
4. A ray leaves the map or hits nothing. It reports no return, and the wire value is JSON `null` because `Infinity` breaks `JSON.parse`. Test in Tasks 5 and 7.
5. A visitor sends a WebSocket message or requests `/../` paths. The socket closes with 1008 and the path gets 404. Test in Task 8.

## Deliberately left out

Each arrives with the phase that needs it: run configs and `reference.*` rejection (5), scenario events and dynamic obstacles (3, 4), `loadScenario` in the browser (2, when a second scenario exists), gyro, sonar and the other five rigs (8), compute-time metrics (6), rosbag and CDR decoding (5). Rig and scenario models reject unknown fields, so an unsupported `gyro` block fails loudly.

## Testing

| Layer         | What proves it                                                              | Command                           |
| ------------- | --------------------------------------------------------------------------- | --------------------------------- |
| Core          | Coordinates, motion, collision, odometry noise, ray casting, schema errors  | `uv run pytest core/tests`        |
| Runner        | `drive-01` thresholds, identical trace for one seed, wire format            | `uv run pytest runner/tests`      |
| Scenarios     | Every `scenarios/*.json` passes headless                                    | `make verify`                     |
| Gateway       | Allowlist, replay, slow clients, reconnect, read-only sockets, static files | `pnpm --filter @gridbot/gateway test` |
| UI            | Frame assembly, y-axis flip, ray geometry                                   | `pnpm --filter @gridbot/ui test`  |
| Browser       | Full stack matches headless exactly, no console errors, rays end at walls   | `pnpm --filter @gridbot/e2e e2e`  |
| ROS and Docker | New core dependencies install, Compose stack streams ticks                 | `make verify-all`                 |

Screenshots land in `artifacts/screenshots/drive-01-<tick>.png`. An agent and the owner check them against the "looks right" line.

---

### Task 1: Prove the Foxglove path

**Files:**

- Create: `docs/decisions/0005-foxglove-json-transport.md`
- Modify: `runner/pyproject.toml`, `gateway/package.json`, `uv.lock`, `pnpm-lock.yaml`

The spec lists these as assumptions to confirm. SDK call names in later tasks come from this spike, so nothing below hard-codes them.

- [ ] **Step 1:** Run `nvm use 24`, then `git switch -c feat/phase-1-world-sim origin/main`. Local `main` is stale, and PR #1 is already merged.
- [ ] **Step 2:** In a throwaway script outside the repo, serve a JSON-schema channel from the Python SDK with no ROS installed.
- [ ] **Step 3:** Connect from Node with `@foxglove/ws-protocol` and `ws`. Confirm it receives and decodes a small message at 20 Hz and one 300 KB message.
- [ ] **Step 4:** Publish JSON from the Node client to a Python-advertised client channel. Confirm the server sees it only when that capability is turned on.
- [ ] **Step 5:** Install the SDK in `python:3.12-slim` on arm64.
- [ ] **Step 6:** Record the versions and exact calls in the decision record, add the dependencies and commit with `docs: record foxglove transport spike`.

**Stop and ask the owner** if any check fails. The transport choice is theirs.

### Task 2: Core dependencies and shared interfaces

**Files:**

- Modify: `core/pyproject.toml`, root `pyproject.toml` (add `types-PyYAML`), `scripts/check_docs.py` (new READMEs)
- Create: `core/src/gridbot_core/types.py`, `sensors/rig.py`, `scenario/models.py`, `scenario/loader.py`, each subpackage `README.md`
- Create: `config/rigs/lidar-360.yaml`
- Test: `core/tests/test_scenario.py`

**Interfaces (later phases build on these):**

```python
TICK_S = 0.05; TICK_NS = 50_000_000
@dataclass(frozen=True, slots=True)
class Pose2D: x: float; y: float; theta: float  # m, m, rad in (-pi, pi]
class Twist2D: v: float; omega: float           # m/s, rad/s

class LidarSpec(BaseModel): id: str; type: Literal["lidar"]; mount: Mount
    fov_deg: float; beams: int; range_m: float; noise_sigma_m: float
class Rig(BaseModel): sensors: tuple[LidarSpec, ...]; odometry: Odometry  # wheel_noise.trans, .rot
class DriveSegment(BaseModel): ticks: PositiveInt; v: float; omega: float
class Scenario(BaseModel): name; note; map; rig; mode: Literal["drive"]; seed; start
    drive: tuple[DriveSegment, ...]; maxTicks: PositiveInt; expect: DriveExpect
class DriveExpect(BaseModel): collisions: int; minPathLengthM: float
    endWithinM: EndZone; maxOdomErrorM: float     # EndZone: x, y, radiusM

class ScenarioError(ValueError): ...
def load_scenario(path: Path) -> Scenario: ...
def load_rig(path: Path) -> Rig: ...
```

All models are frozen with `extra="forbid"`. `lidar-360`: one lidar `lidar`, mount `{x: 0.10, y: 0, yaw_deg: 0}`, 360 degrees, 360 beams, 10 m, noise 0.02 m, wheel noise `{trans: 0.02, rot: 0.05}`. `trans` is the standard deviation per meter traveled, and `rot` is per radian turned.

- [ ] **Step 1:** Write failing tests: `test_rig_loads_lidar_360`, `test_unknown_field_names_field`, `test_invalid_json_names_file`, `test_drive_shorter_than_max_ticks_is_allowed`. Errors must contain the file path and field name.
- [ ] **Step 2:** Run `uv run pytest core/tests/test_scenario.py` and see them fail on the missing module.
- [ ] **Step 3:** Add dependencies `numpy>=1.26,<1.27`, `pydantic>=2`, `pillow`, `pyyaml`. Implement the types and loaders.
- [ ] **Step 4:** Run the tests, then `make verify-ros`. Expected: both pass, which proves the dependencies install in the ROS image.
- [ ] **Step 5:** Commit with `feat: add scenario and rig interfaces`.

### Task 3: World map

**Files:**

- Create: `core/src/gridbot_core/world/grid.py`, `world/loader.py`, `scripts/generate_map.py`
- Create: `assets/warehouse-01.png`, `assets/warehouse-01.yaml`, `assets/ATTRIBUTION.md`
- Test: `core/tests/test_world.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class GridMap: resolution_m: float; origin_x_m: float; origin_y_m: float
    occupied: NDArray[np.bool_]  # read-only, row 0 is the southern edge
def world_to_cell(world: GridMap, x: float, y: float) -> tuple[int, int] | None: ...  # (row, col)
def cell_center(world: GridMap, row: int, col: int) -> tuple[float, float]: ...
def load_map(yaml_path: Path) -> GridMap: ...
```

The map is 20 m by 12 m at 0.05 m (400 by 240 cells), with 0.2 m perimeter walls and shelves at x 6 to 14 for y 1.0 to 1.6, y 5 to 7 and y 10.5 to 11.2.

- [ ] **Step 1:** Write failing tests: `test_png_top_row_becomes_north`, using a 2 by 3 asymmetric image; `test_outside_map_has_no_cell`; `test_nonzero_origin_yaw_is_rejected`; `test_occupied_array_is_read_only`; `test_warehouse_has_expected_size_and_clear_loop`.
- [ ] **Step 2:** Run them and see them fail.
- [ ] **Step 3:** Implement the loader using `map_server` fields (`image`, `resolution`, `origin`, `negate`, `occupied_thresh`, `free_thresh`). Generate the assets from the script.
- [ ] **Step 4:** Run `uv run pytest core/tests/test_world.py`. Expected: pass.
- [ ] **Step 5:** Commit with `feat: load warehouse maps`.

### Task 4: Robot motion and odometry

**Files:**

- Create: `core/src/gridbot_core/sim/drive.py`, `sim/odometry.py`
- Create: `docs/algorithms/differential-drive.md`
- Test: `core/tests/test_sim.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class RobotParams: wheel_base_m=0.4; radius_m=0.25; max_v=1.0; max_omega=1.5; slip_sigma=0.0
@dataclass(frozen=True)
class RobotState: pose: Pose2D; collisions: int; in_contact: bool; path_length_m: float
def step_robot(state: RobotState, cmd: Twist2D, world: GridMap, params: RobotParams,
               rng: np.random.Generator, dt_s: float = TICK_S) -> RobotState: ...
def step_odometry(odom: Pose2D, before: Pose2D, after: Pose2D, noise: Odometry,
                  rng: np.random.Generator) -> Pose2D: ...
```

Integrate exact arcs. Commands clamp to the limits. Each wheel speed is multiplied by `1 - min(|N(0, slip_sigma)|, 1)`. A blocked move keeps the old pose and counts one collision when contact begins. Cells outside the map count as occupied.

- [ ] **Step 1:** Write failing tests: `test_straight_line_distance`, `test_quarter_turn_in_place_keeps_position`, `test_arc_matches_closed_form`, `test_command_is_clamped`, `test_wall_blocks_and_counts_contact_once`, `test_inputs_are_not_mutated`, `test_stationary_odometry_does_not_drift`, `test_odometry_noise_scales_with_motion`.
- [ ] **Step 2:** Run them and see them fail.
- [ ] **Step 3:** Implement `drive.py` and `odometry.py`, then write the algorithm page.
- [ ] **Step 4:** Run `uv run pytest core/tests/test_sim.py`. Expected: pass.
- [ ] **Step 5:** Commit with `feat: simulate differential drive and odometry`.

### Task 5: Lidar and the tick function

**Files:**

- Create: `core/src/gridbot_core/sensors/lidar.py`, `sim/world_step.py`, `metrics/run.py`
- Create: `docs/algorithms/lidar-ray-casting.md`
- Test: `core/tests/test_lidar.py`, `core/tests/test_world_step.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class LaserScan: sensor_id: str; angle_min: float; angle_increment: float
    range_min: float; range_max: float; ranges: NDArray[np.float64]  # inf means no return
def cast_scan(world: GridMap, robot: Pose2D, spec: LidarSpec, rng: np.random.Generator) -> LaserScan: ...

@dataclass(frozen=True)
class Frame: tick: int; true_pose: Pose2D; odom_pose: Pose2D; cmd: Twist2D
    scans: tuple[LaserScan, ...]; collisions: int; path_length_m: float
@dataclass(frozen=True)
class SimRngs: slip: Generator; odometry: Generator; sensors: tuple[Generator, ...]
@dataclass(frozen=True)
class SimState: frame: Frame; robot: RobotState
@dataclass(frozen=True)
class RunMetrics: ticks: int; collisions: int; path_length_m: float
    end_error_m: float; odom_error_m: float; failures: tuple[str, ...]
def make_rngs(seed: int, rig: Rig) -> SimRngs: ...   # default_rng([seed, stream_index])
def first_frame(scenario: Scenario, world: GridMap, rig: Rig, rngs: SimRngs) -> SimState: ...
def next_frame(state: SimState, scenario: Scenario, world: GridMap, rig: Rig, rngs: SimRngs) -> SimState: ...
def run_metrics(final: Frame, scenario: Scenario) -> RunMetrics: ...
```

Use vectorized DDA, stepping all active beams together, because a Python loop per cell would use up the 50 ms tick. A 360-degree scan uses `fov/beams` spacing. Narrower scans use `fov/(beams-1)`, so 270 degrees with 541 beams gives 0.5 degrees. `range_min` is 0.05 m. Noise applies to hits only and is clamped to the valid range. A frame describes the state at its tick and the command about to be applied.

- [ ] **Step 1:** Write failing tests: `test_ray_hits_wall_at_known_distance` for axis-aligned and 45-degree rays, `test_ray_leaving_map_is_inf`, `test_beyond_range_is_inf`, `test_origin_in_wall_returns_range_min`, `test_mount_offset_and_yaw_are_applied`, `test_270_degree_spacing`, `test_noise_never_turns_miss_into_hit`.
- [ ] **Step 2:** Write failing tick tests: `test_scan_is_from_pose_at_same_tick`, `test_script_then_stop`, `test_new_sensor_does_not_change_odometry_noise`, `test_start_in_wall_raises_scenario_error`.
- [ ] **Step 3:** Run them and see them fail.
- [ ] **Step 4:** Implement the code and the algorithm page. Run `uv run pytest core/tests`. Expected: pass.
- [ ] **Step 5:** Commit with `feat: add lidar and simulation ticks`.

### Task 6: Headless runner and `drive-01`

**Files:**

- Create: `runner/src/gridbot_runner/headless.py`, `scenarios/drive-01.json`
- Modify: `runner/src/gridbot_runner/cli.py`, `Makefile`
- Test: `runner/tests/test_headless.py`

**Interfaces:**

```text
gridbot-run SCENARIO [--json] [--trace PATH]
exit 0: thresholds met; 1: thresholds missed; 2: invalid input
--json keys: scenario, passed, ticks, collisions, pathLengthM, endErrorM, odomErrorM, endPose, failures
```

`drive-01`: `map: warehouse-01`, `rig: lidar-360`, `mode: drive`, `seed: 42`, start `(3, 3, 0)`, `maxTicks: 1128`. The script repeats 350 ticks and 150 ticks of straight driving at 0.8 m/s, with a 32-tick left turn at `omega: 0.9817477` after each straight. Thresholds: `collisions: 0`, `minPathLengthM: 39.9`, `endWithinM: {x: 3, y: 3, radiusM: 0.05}`, `maxOdomErrorM: 1.0`.

- [ ] **Step 1:** Write failing tests: `test_drive_01_passes`, `test_same_seed_gives_identical_trace_bytes`, `test_other_seed_changes_odometry_not_truth`, `test_pose_step_never_exceeds_max_speed` over the trace, `test_missed_threshold_exits_1`, `test_bad_file_exits_2_with_field`.
- [ ] **Step 2:** Run `uv run pytest runner/tests/test_headless.py` and see them fail.
- [ ] **Step 3:** Implement the runner. Resolve `assets/` and `config/rigs/` from the scenario file's parent's parent.
- [ ] **Step 4:** Add a `scenarios (runner)` step to `make verify` that loops over `scenarios/*.json`, with every path quoted.
- [ ] **Step 5:** Run the tests and `make verify`. Expected: pass.
- [ ] **Step 6:** Commit with `feat: run scenarios headless`.

### Task 7: Live runner

**Files:**

- Create: `runner/src/gridbot_runner/messages.py`, `runner/src/gridbot_runner/live.py`
- Modify: `runner/src/gridbot_runner/cli.py`
- Test: `runner/tests/test_messages.py`, `runner/tests/test_live.py`

**Interfaces:**

```text
gridbot-run SCENARIO --serve [--host 127.0.0.1] [--port 8765] [--test-control]
```

```python
def frame_messages(frame: Frame, scenario: Scenario, world: GridMap, rig: Rig) -> list[tuple[str, dict[str, object]]]: ...
```

Each tick publishes `/scan/lidar`, `/odom`, `/tf`, `/sim/ground_truth`, `/cmd_vel`, then `/telemetry` last. Telemetry has `source: "sim"` and keys `tick`, `collisions`, `pathLengthM`. Every 20 ticks it also publishes `/sim/world` and `/tf_static` with a fixed zero stamp. Stamps come from `tick * TICK_NS`. A run publishes its frame, then advances. Live mode paces with absolute `time.monotonic` deadlines, logs overruns and restarts at tick 0 after the last frame. With `--test-control`, it advances only on `/test/step` messages `{count}` from 1 to 1000.

- [ ] **Step 1:** Write failing tests: `test_no_return_serializes_as_null`, `test_payloads_are_strict_json` using `allow_nan=False`, `test_telemetry_is_last_in_tick`, `test_world_uses_ros_fields_and_south_first_rows`, `test_stamps_are_exact_integers`, `test_step_channel_absent_without_test_control`, `test_test_mode_waits_for_step`.
- [ ] **Step 2:** Run them and see them fail.
- [ ] **Step 3:** Implement the code with the calls recorded in Task 1. Keep the SDK behind `live.py`.
- [ ] **Step 4:** Run `uv run pytest runner/tests`. Expected: pass.
- [ ] **Step 5:** Commit with `feat: publish simulation over foxglove`.

### Task 8: Gateway

**Files:**

- Create: `gateway/src/protocol.ts`, `relay.ts`, `server.ts`, `static.ts`
- Modify: `gateway/src/main.ts`, `gateway/package.json`
- Delete: `gateway/src/index.ts` and its placeholder test
- Test: `gateway/tests/relay.test.ts`, `gateway/tests/server.test.ts`

**Interfaces:**

```ts
export type ServerMessage =
  | { type: "message"; topic: string; message: unknown }
  | { type: "status"; runtime: "connected" | "offline"; testControl: boolean };
export type TestCommand = { op: "step"; count: number }; // integer, 1 to 1000
```

Settings: `GRIDBOT_RUNTIME_URL` (default `ws://127.0.0.1:8765`), `GRIDBOT_PORT` (8080), `GRIDBOT_UI_DIR`, `GRIDBOT_TEST_CONTROL`. The runtime socket offers both subprotocols listed in decision 0005. Browsers connect at `/ws`. `/healthz` returns `{ runtimeConnected, lastStamp }`. Limits: 100 clients, 1 KiB inbound frames, 1 MiB outbound buffer per client. The allowlist has the Task 7 topics, with `/scan/` as the only prefix.

- [ ] **Step 1:** Write failing tests with a fake runtime: `forwards only allowlisted topics`, `replays world and tf_static to a new browser`, `suppresses an unchanged world`, `drops tick data but not world for a slow client`, `reports offline and reconnects`, `closes visitor sockets that send data with 1008`, `forwards a valid step only with GRIDBOT_TEST_CONTROL=1`, `rejects a step count of 0 and 1001`, `refuses a connection over the client limit`, `returns 404 for traversal paths`, `sets a same-origin CSP`.
- [ ] **Step 2:** Run `pnpm --filter @gridbot/gateway test` and see them fail.
- [ ] **Step 3:** Implement the relay, server and static handler. Subscribe once at startup, so runtime load does not depend on visitors.
- [ ] **Step 4:** Run the tests and `pnpm --filter @gridbot/gateway build`. Expected: pass.
- [ ] **Step 5:** Commit with `feat: relay runtime topics to browsers`.

### Task 9: Browser view

**Files:**

- Create: `ui/index.html`, `ui/vite.config.ts`, `ui/src/main.ts`, `frames.ts`, `view.ts`, `render.ts`, `testApi.ts`, `styles.css`
- Modify: `ui/package.json`, `pnpm-workspace.yaml` only if the build requires it
- Delete: `ui/src/index.ts` and its placeholder test
- Test: `ui/tests/frames.test.ts`, `ui/tests/view.test.ts`, `ui/tests/render.test.ts`

**Interfaces:**

```ts
export type DrawnFrame = {
  tick: number;
  robot: Pose2D;
  lidarOrigin: { x: number; y: number };
  rayHits: { x: number; y: number }[];
  robotPx: { x: number; y: number };
};
window.__gridbot = { getState, waitForTick, step }; // only with ?test=1
```

`/telemetry` closes a frame. The frame is drawn only if the pose and every scan carry its stamp, so rays never attach to an older robot pose. `requestAnimationFrame` draws the newest complete frame with no interpolation. The map is cached on an offscreen canvas. The header shows tick, collisions, connection state and pose source "simulator". Use `design-taste-frontend` for the visual pass, and meet contrast and `prefers-reduced-motion` basics.

- [ ] **Step 1:** Write failing tests: `commits only complete ticks`, `skips a tick with a mismatched scan stamp`, `north appears at the top of the canvas`, `null ranges draw no hit`, `rays start at the mounted lidar`, `test API is absent without test=1`.
- [ ] **Step 2:** Run `pnpm --filter @gridbot/ui test` and see them fail.
- [ ] **Step 3:** Implement the app, importing message types from the gateway with `import type`.
- [ ] **Step 4:** Run the tests and `pnpm --filter @gridbot/ui build`. Confirm the build works with `allowBuilds: esbuild: false`.
- [ ] **Step 5:** Commit with `feat: draw the live simulation`.

### Task 10: Browser test and full-stack wiring

**Files:**

- Create: `e2e/playwright.config.ts`, `e2e/tests/drive-01.spec.ts`
- Modify: `e2e/package.json`, `Makefile`, `.github/workflows/verify.yml`, `.gitignore` if needed
- Modify: `docker/gateway.Dockerfile`, `docker/runner.Dockerfile`, `docker/compose.yaml`, `scripts/e2e_compose.sh`
- Delete: `e2e/src/index.ts` and its placeholder test

Playwright starts the runner with `--serve --test-control --port 18765` and the gateway with `GRIDBOT_TEST_CONTROL=1` on port 18080. Compose runs the runner live and publishes only the gateway, at `127.0.0.1:8080`. The gateway image builds the UI and includes production dependencies.

- [ ] **Step 1:** Write a failing `drive-01.spec.ts`:
  - `matches the headless run`: step to tick 1128, then expect the true pose and collisions to equal `gridbot-run --json` output exactly.
  - `draws rays that end at walls`: at ticks 0, 350 and 1128, every drawn hit is within 0.15 m of an occupied cell, and the canvas pixel at `robotPx` is not background.
  - Every test fails on a console error or failed request.
  - Save screenshots at those ticks.
- [ ] **Step 2:** Run `pnpm --filter @gridbot/e2e exec playwright install chromium`, then `pnpm --filter @gridbot/e2e e2e`. Expected: it fails until the config starts the stack, then passes.
- [ ] **Step 3:** Add `ui build` and `e2e` steps to `make verify`. Install Chromium with system dependencies in `verify.yml`, and upload `artifacts/` on failure.
- [ ] **Step 4:** Change `e2e_compose.sh` to start the runner and gateway, poll `/healthz` from inside the gateway container, require `runtimeConnected` and two different `lastStamp` values, and keep the runner version and ROS package checks by passing explicit commands.
- [ ] **Step 5:** Run `make verify-all`. Expected: every step passes and no containers remain.
- [ ] **Step 6:** Commit with `test: cover drive-01 in the browser`.

### Task 11: Docs and phase close

**Files:**

- Modify: `AGENTS.md`, `README.md`, `docs/architecture.md`, `docs/runtimes.md`, `docs/sensors.md`, `docs/testing.md`, and the READMEs for `core`, `runner`, `gateway`, `ui`, `e2e`, `assets`, `config`, `scenarios`, `docker`
- Create: `docs/decisions/0006-scripted-drive-scenarios.md`, `docs/journal/phase-01-world-sim-view.md`

- [ ] **Step 1:** Update commands and phase status. `AGENTS.md` must cover the gateway server, Playwright install and how to run the stack.
- [ ] **Step 2:** Open the three screenshots and check them against "robot drives smoothly, rays stop at walls".
- [ ] **Step 3:** Run the `code-review` skill on the branch diff and fix its findings.
- [ ] **Step 4:** Run `make verify-all` and record the summary lines in the journal.
- [ ] **Step 5:** Commit with `docs: record phase 1`. Ask the owner before pushing or opening the PR.

## What exists after Phase 1

- `docker compose --profile runner up` serves the app at `localhost:8080`. The robot loops around the center shelves at 20 Hz, and lidar rays stop at the walls and shelves.
- `uv run gridbot-run scenarios/drive-01.json --json --trace out.jsonl` gives repeatable metrics and a per-tick debug trace.
- State types, the rig format, the scenario format and topic names are stable enough for Phase 2 mapping, planning and UI work to proceed in parallel.
- The robot still follows a fixed script. It does not map, localize, plan or react to obstacles yet.
