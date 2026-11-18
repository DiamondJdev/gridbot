# Gridbot design

Status: draft for approval, 2026-11-17. "Gridbot" is a working name.

## What it is and why

Gridbot is a simulated warehouse robot that explores, maps, localizes and navigates, with every layer of its thinking drawn live in a browser: lidar returns, the map being built, the particle cloud of position guesses, the SLAM pose graph, the planner's search and the controller's commands. The look borrows from Tesla's FSD debug view, in 2D.

The owner wants it to be as close to real robotics work as a virtual project can get, and to show it off in a portfolio. That sets three priorities:

1. Real algorithms, written by hand and documented well enough that a reviewer can follow each one.
2. Real industry tooling: ROS 2, its transform system, launch files, rosbag, and side-by-side comparison with the reference implementations robotics companies ship (Nav2, `slam_toolbox`).
3. Best practice at every step, so any file a reviewer opens holds up.

Agents write every line of code. The repo is laid out so an agent can find its way around, change one piece, and prove the whole project still works with one command.

Gridbot is its own git repository and does not depend on Phoenix Firefly. It can be deployed to Firefly the same way Firefly's own apps are (an arm64 image and a k3s manifest), but nothing in the repo requires Firefly.

## Goals

- Three navigation modes: Explore (mapping with a known pose), Localize (finding the pose on a known map) and SLAM (both at once).
- Swappable sensor setups, chosen by config file, so their effect on each mode can be measured.
- Each algorithm can be swapped between Gridbot's own version and an industry reference, and the two compared on the same scenario with the same metrics.
- Start simple and grow: a plain-Python runtime first, ROS 2 added on top later, with nothing thrown away.
- One command tells an agent whether the project works end to end.
- Documentation that lets someone new to the repo understand what every part does without reading the code first.

## Non-goals

- 3D simulation or a physics engine. Gazebo can come later on the Firefly desktops if a phase calls for it.
- Several robots at once.
- Real hardware. The layering keeps that path open, but no phase plans for it.
- Visitor accounts, stored visitor data or visitor control of the simulation.

## Anti-goals

These would make the project a failure even if it technically works:

- A library doing Gridbot's own algorithms. Reference implementations are there to compare against, never to stand in for Gridbot's versions.
- A Codebase that technically works, but is not maintainable or extendable.
- Visuals that are faked or tweened instead of drawn from real algorithm state.
- Tests that pass while the demo looks broken, or tests that fail at random.
- Load on the hosting machine that grows with the number of visitors
- Code or docs that only make sense to the person or agent who wrote them.

## Approaches considered

1. **Browser-only TypeScript.** Everything runs in the visitor's tab. It's the simplest to host, but it shows no real robotics tooling. (This lowers the total number of people who can experience the website, so it is rejected.)
2. **ROS 2 on a server, with a browser view (chosen).** Algorithms run as ROS 2 nodes on the server, and the browser draws what they publish. This matches how robotics companies build robots and allows comparison with Nav2 and `slam_toolbox`.
3. **ROS 2 plus recorded replays.** The same as 2, with the browser falling back to recorded runs when the live robot is offline. It can be added to 2 later without changes, so it is listed under presentation options instead of being a separate approach.

Within approach 2, the owner chose a layered design: algorithms live in plain Python libraries with no ROS imports, and two interchangeable runtimes host them. This is also standard practice in robotics codebases, because it keeps the algorithms testable without ROS.

## Architecture

```
Layer 4  Browser UI            TypeScript, draws everything, one JSON protocol
             |  WebSocket (public)
Layer 3  Gateway               fans data out to visitors, read-only
             |  Foxglove WebSocket protocol (internal only)
Layer 2  Runtime, pick one at start
             a) runner: one Python process, fixed-step and deterministic
             b) ros: ROS 2 Jazzy nodes, each wrapping one library
             |  plain Python calls
Layer 1  gridbot_core          plain Python libraries, no ROS, no I/O
             sim, sensors, mapping, localization, slam, planning, control, metrics
```

The rule that makes every layer swappable: each layer talks to the next through one documented interface, and the interface does not change when the layer below is swapped.

- Layer 1 to 2: Python function calls on immutable data (dataclasses and NumPy arrays).
- Layer 2 to 3: the Foxglove WebSocket protocol, with the topic names and message shapes in [Topics and messages](#topics-and-messages). The runner serves it with the Foxglove SDK. ROS serves it with `foxglove_bridge`. Messages use ROS field names in both, so they decode to the same shape.
- Layer 3 to 4: JSON over a WebSocket. The gateway decodes whatever the runtime sends (JSON from the runner, CDR from ROS) and sends browsers plain JSON. The UI only knows one format.

### Why there is a gateway

- Load stays fixed. The runtime has one client, the gateway, however many people are watching. The gateway fans out the data, which costs bandwidth but little CPU.
- Visitors can't reach the runtime. `foxglove_bridge` lets clients publish to any topic, so it must never face the internet. The gateway forwards only an allowlist of topics outward and accepts no commands from visitors.
- It hides which runtime is running, so the UI is the same for both.

The gateway is written in TypeScript with the `@foxglove/ws-protocol` client, shares message types with the UI, and lives in its own small package.

### Layer 1: `gridbot_core`

A Python package (Python 3.12, managed with `uv`). Each subpackage holds one capability and has a README that explains the algorithm in plain language, links to the source it follows, and shows its inputs and outputs.

| Subpackage | What it does | Methods (Gridbot's own versions) |
|---|---|---|
| `world` | Loads maps, converts between grid and world coordinates, places dynamic obstacles | ROS `map_server` format: PNG plus YAML |
| `sim` | Moves the robot and produces sensor readings | Differential drive with configurable wheel slip; footprint collision |
| `sensors` | Sensor models, built from a sensor rig config | 2D lidar (DDA ray cast), sonar (wide cone, nearest return), wheel encoders, gyro |
| `mapping` | Builds an occupancy grid from known poses | Log-odds inverse sensor model |
| `localization` | Finds the pose on a known map | Monte Carlo localization, likelihood field, low-variance resampling, recovery from a kidnapped robot by injecting random particles |
| `slam` | Maps and localizes at once | v1: Rao-Blackwellized particle filter with grid maps (the GMapping family). v2: pose graph with scan matching, loop closure and Gauss-Newton optimization (the family `slam_toolbox` belongs to) |
| `planning` | Finds a route | A* on an inflated grid; frontier detection for exploring without a goal |
| `control` | Follows the route | Pure pursuit, then regulated pure pursuit |
| `metrics` | Scores a run | Absolute trajectory error, map agreement with ground truth, convergence time, path length, collisions, compute time per step |
| `scenario` | Loads a scenario and a run config | Pydantic models, validated on load |

Rules for `gridbot_core`:

- No ROS imports, no network or file I/O outside `world` and `scenario` loading, no global state.
- No unseeded randomness. Every random draw comes from a `numpy.random.Generator` passed in by the caller.
- Functions take state and return new state. Inside a function, a freshly allocated NumPy array may be filled in place before it is returned; that is the only exception to the owner's immutability rule, and each such place has a one-line comment.
- Public functions have type hints and docstrings. `pyright` runs in strict mode.
- Files stay under 400 lines and functions under 50, following the owner's coding style rules.

Import-linter rules enforce the first point, and a Ruff rule bans `random` and `time` imports inside the package.

### Layer 2a: the runner

`runner/` is one Python process. It loads a run config, steps the sim and the chosen algorithms at a fixed 20 Hz with no wall clock involved, and publishes every topic through the Foxglove SDK. It also has a headless mode that runs a scenario as fast as the CPU allows and prints metrics as JSON.

Because nothing in it depends on time, the same seed always gives the same run. That makes it the main test harness: most of `make verify` runs through it.

### Layer 2b: ROS 2

`ros/` is a colcon workspace for ROS 2 Jazzy, built and run only inside Docker (the official `ros:jazzy` images support arm64 and amd64, so the same image works on an Apple silicon Mac and on Firefly's Pis).

| Package | Contents |
|---|---|
| `gridbot_msgs` | Custom messages for debug data that has no standard type: planner search, particle weights, pose graph, telemetry, plus the `TickDone` message used for lockstep |
| `gridbot_sim` | Sim node. Publishes `/clock`, `/scan`, `/odom`, `/tf`, and ground truth on `/sim/*` |
| `gridbot_nodes` | One thin wrapper node per library (mapping, localization, slam, planning, control). Each converts messages to core types, calls the library, and converts back. Target size: under 100 lines each |
| `gridbot_bringup` | Launch files, parameter files, Foxglove and RViz layouts |

The sim node owns the clock and every node runs with `use_sim_time`. During scenario tests the sim runs in lockstep: it starts the next tick only after every Gridbot node in the run has published `/sim/tick_done` for the current one. A node that misses the timeout fails the test, and the failure names it. Callback order can still vary, so ROS runs are close to repeatable but not exact, and ROS tests use tolerances. Live runs don't wait and stay at 20 Hz.

Reference nodes can't report ticks, so lockstep covers Gridbot's nodes only. Test runs that include a reference node also slow the sim clock to give it time to keep up.

Wrapper nodes start as plain nodes. Phase 9 converts the swappable algorithm nodes to lifecycle nodes, so it can switch algorithms during a run (deactivate one, activate another) without restarting.

### Swapping things

| What | How | When |
|---|---|---|
| Runtime | `docker compose --profile runner up` or `--profile ros up` | At start |
| Mode (explore, localize, slam) | Scenario, or an override in `run.yaml` | At start |
| Algorithm (Gridbot's or the reference) | `run.yaml`; ROS runtime only for references | At start; live switching in phase 9 |
| Sensor rig | `config/rigs/*.yaml` named by the scenario, or an override in `run.yaml` | At start |
| Scenario | `run.yaml` | At start |
| Map | Scenario, or an override in `run.yaml` | At start |

A run config:

```yaml
# config/runs/slam-dual-lidar.yaml
runtime: ros
scenario: slam-loop-01
rig: dual-lidar                # optional override
algorithms:
  slam: gridbot.pose_graph     # or gridbot.rbpf, or reference.slam_toolbox
  planning: gridbot.astar      # or reference.nav2_smac
  control: gridbot.rpp         # or reference.nav2_rpp
shadow:                        # optional, ROS only, runs beside the active stack
  slam: reference.slam_toolbox
```

The scenario supplies the map, rig, mode and seed. A run config names the scenario, picks the runtime and algorithms, and may override any of those four values. Phase 8 uses overrides to run every mode against every rig. A scenario's `expect` thresholds apply only when nothing is overridden; overridden runs report their metrics.

The runner rejects any `reference.*` algorithm with a clear error, since references exist only in ROS.

### Sensor rigs

A rig file lists sensors and where each sits on the robot. In ROS each mount becomes a static transform, so every algorithm sees readings in the right place without code changes.

```yaml
# config/rigs/dual-lidar.yaml
sensors:
  - id: lidar_front
    type: lidar
    mount: { x: 0.20, y: 0.0, yaw_deg: 0 }
    fov_deg: 270
    beams: 541
    range_m: 10
    noise_sigma_m: 0.02
  - id: lidar_rear
    type: lidar
    mount: { x: -0.20, y: 0.0, yaw_deg: 180 }
    fov_deg: 270
    beams: 541
    range_m: 10
    noise_sigma_m: 0.02
odometry:
  wheel_noise: { trans: 0.02, rot: 0.05 }
gyro: { bias_deg_s: 0.1, noise_deg_s: 0.5 }
```

Starter rigs: `lidar-360` (baseline), `front-lidar-270`, `dual-lidar`, `sonar-ring-16`, `cheap-lidar` (low beam count, high noise), and `lidar-no-gyro` to show odometry drift. Phase 8 runs every mode against every rig and publishes the results table.

### Topics and messages

ROS standard types wherever one fits. The runner publishes the same names and field layouts as JSON.

| Topic | Type | From |
|---|---|---|
| `/scan/<sensor_id>` | `sensor_msgs/LaserScan` (sonar uses `sensor_msgs/Range`) | sim |
| `/odom` | `nav_msgs/Odometry` | sim |
| `/tf`, `/tf_static` | `tf2_msgs/TFMessage` | sim, localization, slam |
| `/sim/ground_truth` | `geometry_msgs/PoseStamped` | sim |
| `/sim/world` | `nav_msgs/OccupancyGrid` | sim |
| `/map` | `nav_msgs/OccupancyGrid` | mapping, slam |
| `/particles` | `geometry_msgs/PoseArray` plus `gridbot_msgs/ParticleWeights` | localization, slam v1 |
| `/slam/graph` | `gridbot_msgs/PoseGraph` | slam v2 |
| `/plan` | `nav_msgs/Path` | planning |
| `/planner/search` | `gridbot_msgs/SearchTrace` | planning |
| `/cmd_vel` | `geometry_msgs/Twist` | control |
| `/telemetry` | `gridbot_msgs/Telemetry` | every algorithm |
| `/goal` | `geometry_msgs/PoseStamped` | sim (from the scenario) |
| `/sim/tick_done` | `gridbot_msgs/TickDone` | every Gridbot node, during scenario tests |

### Reference stacks

An algorithm under `algorithms` in the run config is active: it uses the standard topics and drives the robot. An algorithm under `shadow` runs beside it for comparison, in the `/reference` namespace, so its outputs appear as `/reference/particles`, `/reference/plan` and so on. Shadow stacks publish no transforms (`tf_broadcast: false` for AMCL, `transform_publish_period: 0` for `slam_toolbox`), and nothing subscribes to `/reference/cmd_vel`, so they can't move the robot.

Nav2 and `slam_toolbox` each take one laser scan, so comparisons use the single-lidar rigs: `lidar-360`, `front-lidar-270`, `cheap-lidar` and `lidar-no-gyro`. `dual-lidar` and `sonar-ring-16` run Gridbot's algorithms only.

## Behavior of each mode

- **Explore:** the robot uses its true pose from the simulator and builds the map. The UI labels the pose source "simulator" so nobody mistakes this for SLAM. Without a goal it drives to the nearest frontier (the edge between known and unknown space). With a goal, A* treats unknown cells as free and replans when a wall appears in the way.
- **Localize:** the robot has the map but not its pose. Particles start spread over all free space. The robot wanders until the particle spread falls under 0.5 m, then plans to the goal. The UI shows the true error, which the robot itself can't see.
- **SLAM:** the robot has neither. It explores to frontiers, closes loops when it revisits places, and the UI shows the map correcting itself when a loop closes. This is the headline demo.

In every mode, an obstacle from a scenario event is added to the true world, and the robot only learns about it through its sensors.

## Hosting and visitors

One shared live robot runs on the server and cycles through a playlist of run configs from `config/playlists/`. Everyone watching sees the same robot. Visitors can only watch: they can't set goals, add obstacles, change the run or affect the simulation in any other way.

Viewers of the codebase can run everything on their own machine with `docker compose --profile ros up` and open the UI at `localhost`. That is also how the full ROS stack gets demoed if the server is down.

## Presentation

The owner wants to stay open on how the finished project is shown. The design supports all of these, and the choice can be made around phase 10:

- The live shared robot on a public URL.
- Recorded runs replayed in the browser (rosbag converted to the gateway's JSON), for when the live robot is offline or to show a specific moment.
- A comparison report per phase: a static page with charts and screenshots, generated from scenario runs by `make report`.
- Foxglove layouts in the repo, so a robotics reviewer can open a run in a tool they already know.
- A short screen recording and GIFs in the README.
- A write-up per phase in `docs/journal/`, covering what was built, what was measured and what went wrong.

## Repository layout

```
gridbot/
  README.md            what it is, a GIF, run it in three commands, map of the repo
  AGENTS.md            for coding agents: commands, rules, where things live
  CLAUDE.md            @AGENTS.md plus Claude-only notes
  LICENSE              MIT
  Makefile             every command, listed by `make help`
  .github/             CI/CD for PR testing and pushing to `firefly`
  core/                gridbot_core (Layer 1), with tests/
  runner/              Layer 2a, with tests/
  ros/src/             Layer 2b colcon packages, each with tests/
  gateway/             Layer 3, TypeScript, with tests/
  ui/                  Layer 4, TypeScript + Vite, with tests/
  e2e/                 Playwright tests across the whole stack
  config/              rigs/, runs/, playlists/
  assets/              PNG + YAML pairs, ATTRIBUTION.md
  scenarios/           scenario JSON files shared by every test layer
  docker/              Dockerfiles, compose.yaml
  deploy/              k3s manifests, ship.sh
  docs/
    architecture.md    this design, kept current as the code changes
    algorithms/        one page per algorithm: idea, diagram, math, link to code
    sensors.md         rig format and what each sensor model simulates
    runtimes.md        runner versus ROS, and how to add a runtime
    testing.md         the test layers and how to debug a failure
    decisions/         numbered decision records (ADRs)
    journal/           per-phase write-ups
    superpowers/       specs/ and plans/ for agent work
```

## Documentation standard

The aim: someone who has never seen the repo can open any folder and know what it does within a minute.

- Every top-level folder and every package has a README with the same sections: what it does, how it fits the layers (with a link to `docs/architecture.md`), how to run its tests, and its main files with one line each.
- Every algorithm has a page in `docs/algorithms/` with the intuition first, then a Mermaid diagram, then the math, then the parameters and what changing each one does, then a link to the code and the source paper or book chapter.
- Every lasting decision (a library choice, a format, a rule) gets a short decision record in `docs/decisions/`. The choices in this doc become the first ones.
- Code comments explain why, not what. Public functions have docstrings with units (meters, radians, seconds).
- Docs change in the same PR as the code they describe. CI checks that every package has a README and that internal Markdown links resolve.
- Prose follows the owner's writing rules (the `humanizer` skill) before it is committed.

## Engineering practices

- Conventional commit messages using the owner's types (feat, fix, refactor, docs, test, chore, ci).
- One phase per PR. Branch protection on `main`: CI must pass without overriding tests.
- Test first for every change to logic.
- Python: `uv`, Ruff (lint and format), pyright strict, pytest, import-linter.
- TypeScript: pnpm, strict `tsc`, ESLint, Prettier, Vitest, Playwright.
- ROS: `ament_python` packages, `colcon test`, `launch_testing`. Ruff replaces `ament_flake8` so Python style is the same across the repo; that choice gets a decision record.
- pre-commit hooks run the fast checks locally.
- Dependencies pinned through lockfiles. Renovate opens update PRs.
- No secrets in the repo. Deploy settings come from environment variables.
- GitHub Actions runs `make verify` on every PR and `make verify-ros` on every PR that touches `ros/`, `core/` or `scenarios/`, using GitHub's arm64 Linux runners so CI matches the deploy target.

## Testing

### Commands

| Command | What it runs | Rough time |
|---|---|---|
| `make verify` | Lint, type checks and unit tests for every package; every scenario through the headless runner; UI and gateway builds; Playwright against the runner stack | 3 to 5 minutes |
| `make verify-ros` | Inside Docker: `colcon build`, `colcon test`, then the ROS scenario suite and rosbag regression tests | 10 to 15 minutes |
| `make verify-all` | Both of the above, then Playwright against the full ROS stack started with Docker Compose | 20 minutes |

Each command exits non-zero at the first failure and ends with one summary line per step, for example `scenarios (runner): 14 passed, 0 failed`. An agent runs `make verify` after every task and `make verify-all` before a phase is called done.

### Scenarios

One scenario file feeds every test layer:

```json
{
  "name": "localize-kidnap-01",
  "note": "Robot is teleported mid-run; the filter must recover.",
  "map": "warehouse-01",
  "rig": "lidar-360",
  "mode": "localize",
  "seed": 42,
  "start": { "x": 2.0, "y": 3.0, "theta": 0.0 },
  "goal": { "x": 17.5, "y": 11.0 },
  "events": [{ "tick": 600, "type": "kidnap", "to": { "x": 10.0, "y": 4.0, "theta": 1.57 } }],
  "maxTicks": 4000,
  "expect": {
    "reachedGoal": true,
    "collisions": 0,
    "ateMaxM": 0.25,
    "convergedByTick": 400
  }
}
```

Thresholds are ranges, not exact values. The runner meets them exactly every time; ROS runs must meet the same thresholds, which tolerate the small differences in callback order.

The headless runner can run any scenario directly, with Gridbot's default algorithms and no overrides:

```bash
uv run gridbot-run scenarios/localize-kidnap-01.json --json --trace out.jsonl
```

`--trace` writes one JSON line per tick (true pose, estimate, error, planner state), which an agent can read to debug a failure without a browser.

### Browser tests

With `?test=1`, the UI exposes `window.__gridbot` with `getState()`, `waitForTick(n)` and `loadScenario(name)`. Scenario loading and step requests work only when the gateway starts with `GRIDBOT_TEST_CONTROL=1`. Production never sets that variable, and `?test=1` can't turn it on. In test mode the runner steps only when the gateway forwards a step request, so browser tests against the runner are exact as well. Playwright uses this to:

- run scenarios through the full stack and compare metrics with the headless result
- fail on any console error or failed request
- save screenshots at fixed ticks to `artifacts/screenshots/<scenario>-<tick>.png`

Screenshots are not compared pixel by pixel, since that breaks across machines. Agents open them and check the screen against the phase's "looks right" line, and the owner reviews them in each PR.

### Rosbag regression

Phase 5 onward, a short rosbag of each ROS scenario is recorded and checked in under `ros/test/bags/` (kept small: under 5 MB each, using Git LFS if needed). Replaying a bag through an algorithm node must produce output within tolerance of the recorded output. This catches changes in a node's behavior without running the sim.

## Agentic development pipeline

### What agents read first

1. `AGENTS.md`: what the project is, the layer map, every command, the rules above, and a "what not to do" list. Any change that makes it wrong updates it in the same commit, following the pattern in the owner's other repos.
2. The README of the package being changed.
3. `docs/architecture.md` and the relevant `docs/algorithms/` page.
4. The current phase plan in `docs/superpowers/plans/`.

### Flow for each phase

1. An agent writes the phase plan from this doc, with tasks under about 200 changed lines each. Every task names the test or scenario it starts with. It should use the `ponytail` skill to reduce overengineering in the plan. The owner approves the plan.
3. For each task: write the failing test or scenario, watch it fail, write the code, write or update the docs, run `make verify`.
4. Open the screenshots and check them against the phase's "looks right" line.
5. Review the branch diff with the `code-review` skill. Fix the findings and rerun `make verify`.
6. One PR, with the summary lines from `make verify` and, for visible changes, two or three screenshots.
7. At the end of the phase: `make verify-all`, `make report`, and the phase journal entry.

An agent may not report a task done without pasting the verify output from that run.

### Parallel work

After phase 1 fixes the interfaces in `gridbot_core` (state types, the sensor rig format, topic names), separate capabilities touch separate folders. Mapping, planning and the UI panels can be built in parallel sessions in their own git worktrees. Localization waits for the sensor models; SLAM waits for mapping and localization.

### Where the owner steps in

- Approving this design and each phase plan.
- Reviewing each PR's screenshots for feel: colors, speed, whether the screen reads at a glance.
- Every deploy, including the first push to a public GitHub repo.

## Phases

Each phase ends with something demoable and a journal entry.

| # | Phase | Done when | Looks right when | Estimate |
|---|---|---|---|---|
| 0 | Repo skeleton: layout, Makefile, CI, pre-commit, README and AGENTS.md, empty packages with one passing test each, Docker Compose profiles | `make verify` passes in CI | No UI yet | 1 to 2 days |
| 1 | World, sim, lidar and odometry in `gridbot_core`; runner; gateway; UI showing map, robot and lidar; scripted driving from the scenario | `drive-01` passes in the runner and in Playwright | Robot drives smoothly, rays stop at walls | 1 week |
| 2 | Explore mode: mapping and frontier exploration | `explore-01` reaches map agreement 0.9 | Grey map fills in as the robot explores | 3 to 4 days |
| 3 | Localize mode: MCL, kidnapped robot recovery | `localize-01` and `localize-kidnap-01` pass | Particle cloud shrinks onto the robot, scatters on kidnap, recovers | 4 to 5 days |
| 4 | A*, pure pursuit | Every scenario reaches its goal with 0 collisions | Path redraws when an obstacle lands on it | 4 to 5 days |
| 5 | ROS 2 runtime: sim node, wrapper nodes, launch files, `foxglove_bridge` behind the gateway, rosbag tests | Every scenario passes on ROS within tolerance; the UI is unchanged | Same screen, now labeled "ROS 2" | 1 to 1.5 weeks |
| 6 | Reference comparisons: Nav2 AMCL, Smac planner, regulated pure pursuit; `make report` | Report compares Gridbot and reference on every single-lidar scenario | Side-by-side view of both estimates | 1 week |
| 7 | SLAM v1: particle filter SLAM, plus `slam_toolbox` as reference | `slam-loop-01` passes with ATE under its threshold | Each particle's map visible on hover | 1 week |
| 8 | Sensor rig experiments: every mode against every rig | Results table in the report and the journal | UI labels the active rig | 4 to 5 days |
| 9 | SLAM v2: pose graph with loop closure; live algorithm switching with lifecycle nodes | `slam-loop-01` ATE beats SLAM v1 | Map snaps into place when a loop closes | 1.5 weeks |
| 10 | Deploy and present: production images, k3s manifests, playlist, chosen presentation formats | `make verify-all` passes against the deployed images; owner approves the deploy | Owner signs off | 1 week |

Total: about 9 to 11 weeks of agent work plus the owner's review time. Phases 1 to 4 run without ROS, so a working demo exists within about 3 weeks.

Stretch goals: recorded replays in the browser, a learned exploration policy (a small network trained offline that picks the next frontier, which adds a machine learning component), Gazebo with a 3D world on the Firefly desktops, and real hardware.

## Deploying

The deploy follows the same steps Firefly uses for its own apps, implemented inside this repo:

- `docker/` builds three images: `gateway` (Node, also serves the built UI), `runner`, and `ros` (one image with every ROS package). All are built for arm64 and amd64.
- `deploy/k8s/` holds a Deployment and Service per component and one Ingress for the gateway. The gateway is the only thing exposed. Resource requests start small (gateway 64Mi, runner 256Mi, ros 1Gi) and get tuned from measurements in phase 10.
- `deploy/ship.sh <runtime>` builds arm64 images, takes the tag from this repo's git commit (marked `-dirty` when there are uncommitted changes), copies them to the target host over SSH, imports them into k3s and applies the manifests. The target host and public hostname come from environment variables (`GRIDBOT_DEPLOY_HOST`, `GRIDBOT_HOSTNAME`), so nothing about Firefly is hard-coded.
- On Firefly, the hostname must stay one label deep (for example `gridbot.diamondjdev.me`) because of how its certificate works.

## Decisions made on the owner's behalf

All of these are proposals and can change:

- Python 3.12 for the algorithm libraries, ROS 2 Jazzy for the ROS runtime.
- A separate TypeScript gateway as the only public entry point, sending JSON to the browser.
- SLAM v1 as a particle filter and v2 as a pose graph, with `slam_toolbox` as the reference.
- The six starter sensor rigs.
- The phase order, with ROS arriving in phase 5 after a working runner-based demo.
- Rosbags checked in for regression tests.
- MIT licence.

## Left to the builder

- Colors, fonts and panel layout of the UI, following a design pass with the `design-taste-frontend` skill with Claude Design screenshots in phase 1.
- Exact algorithm parameters, recorded in config files with a comment for each.
- How the shelf layout generator works.
- Scenario thresholds beyond those named above, each justified in the scenario's `note` field.
- Whether a library needs a C++ rewrite, decided only from profiling.

## To confirm early in phase 1

These are assumptions a short spike should confirm before building on them:

- The Foxglove SDK for Python can serve JSON-schema channels without ROS, as the runner needs.
- `@foxglove/ws-protocol` works as a client in Node for the gateway.
- A Raspberry Pi 5 runs the ROS image with every node at 20 Hz under 50% CPU (checked in phase 5).
