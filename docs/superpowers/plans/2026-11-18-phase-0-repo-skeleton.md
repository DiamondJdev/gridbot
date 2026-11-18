# Phase 0: Repo Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the standalone Gridbot repository, with every package present, tested and wired into `make verify`, `make verify-ros`, `make verify-all` and CI.

**Architecture:** A uv workspace holds the Python packages (`core`, `runner`). A pnpm workspace holds the TypeScript packages (`gateway`, `ui`, `e2e`). A colcon workspace under `ros/src` builds only inside Docker. In this phase each TypeScript package is a placeholder with one test; no robotics code, server or WebSocket exists yet.

**Tech Stack:** Python 3.12, uv, Ruff, pyright, pytest, import-linter; Node 24, pnpm, TypeScript, Vitest, ESLint, Prettier; ROS 2 Jazzy, colcon; Docker Compose; GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-17-gridbot-design.md`

## Global Constraints

- Gridbot is its own git repository. Nothing may import from, call or name a path inside Firefly.
- `gridbot_core`: no ROS imports, no network, no global state, no `random` or `time` imports.
- Python functions under 50 lines, files under 400 lines, public functions typed with docstrings, pyright strict.
- Create new objects; do not mutate inputs.
- Test first for every change to logic.
- Commit messages: `<type>: <description>`, with type one of feat, fix, refactor, docs, test, chore, ci.
- Every top-level folder and package has a README with these exact headings: `## What it does`, `## How it fits`, `## Running its tests`, `## Main files`.
- Run the `humanizer:humanizer` skill on READMEs and files under `docs/` before committing them.
- No secrets in the repo. Settings come from environment variables.
- Pushing, creating the GitHub repo and deploying need the owner's approval.

## Review Focus

1. The repo may live in a path containing spaces (this session's folder does). `make` steps must still work. Test in Task 7.
2. The docs checker must follow real links and anchors, and ignore external URLs and links shown inside code fences. Test in Task 2.

## Deliberately left out

Each item arrives with the phase that needs it: scenarios and a scenario test step (1), NumPy and Pydantic (1), Foxglove and WebSockets (1), the gateway server, the UI app, Vite and Playwright (1), `make report` (6), k3s manifests and `ship.sh` (10), and the deploy workflow to Firefly (10). `config/`, `assets/`, `scenarios/` and `deploy/` hold only a README for now.

---

### Task 1: Repository, `gridbot_core` and `runner`

**Files:**
- Create: `.gitignore`, `.python-version`, `LICENSE`, `pyproject.toml`, `.importlinter`
- Create: `core/pyproject.toml`, `core/README.md`, `core/src/gridbot_core/__init__.py`, `core/src/gridbot_core/py.typed`
- Create: `runner/pyproject.toml`, `runner/README.md`, `runner/src/gridbot_runner/__init__.py`, `runner/src/gridbot_runner/cli.py`
- Test: `core/tests/test_boundaries.py`, `runner/tests/test_cli.py`

**Interfaces:**
- Produces: `gridbot_core.__version__: str`, `gridbot_runner.cli.main(argv: Sequence[str] | None = None) -> int`, and the console script `gridbot-run`.

- [ ] **Step 1: Initialize git with the approved documents**

Run: `git init -b main && git add docs && git commit -m "docs: add approved design and phase 0 plan" && git switch -c phase-0-skeleton`
Expected: branch `phase-0-skeleton`, with one commit on `main`.

- [ ] **Step 2: Create the workspace configuration**

Root `pyproject.toml`: uv workspace with members `core` and `runner`; dev group with `ruff`, `pyright`, `pytest`, `import-linter`, `pre-commit`; pytest `--import-mode=importlib`, `pythonpath = ["scripts"]` and testpaths `core/tests`, `runner/tests`, `scripts/tests`; pyright `strict` over those packages and `scripts`; Ruff selects `E,F,I,UP,B,TID`.

`core/pyproject.toml` has `[tool.ruff] extend = "../pyproject.toml"` and bans `random` and `time` through `[tool.ruff.lint.flake8-tidy-imports.banned-api]`, with a message pointing to the caller-supplied generator. `core` has no runtime dependencies yet.

`.importlinter`: `root_package = gridbot_core`, `include_external_packages = True`, and one forbidden contract covering `rclpy`, `foxglove`, `socket`, `http`, `urllib` and `gridbot_runner`.

`.gitignore` includes `.venv/`, `node_modules/`, `dist/`, `artifacts/`, `build/`, `install/`, `log/`, `.env` and `.env.*`.

- [ ] **Step 3: Write the failing tests**

```python
# core/tests/test_boundaries.py
def test_version_is_exposed():
    assert gridbot_core.__version__ == "0.1.0"

def test_ruff_rejects_random_in_core():
    result = run_ruff_on_stdin("import random\n", "core/src/gridbot_core/example.py")
    assert result.returncode == 1
    assert "TID251" in result.stdout

def test_ruff_rejects_time_in_core():
    result = run_ruff_on_stdin("import time\n", "core/src/gridbot_core/example.py")
    assert result.returncode == 1
    assert "TID251" in result.stdout

def test_import_contract_rejects_rclpy(tmp_path):
    result = run_import_linter_on_copy(tmp_path, bad_source="import rclpy\n")
    assert result.returncode == 1
    assert "rclpy" in result.stdout
```

`run_ruff_on_stdin` runs `ruff check --stdin-filename <path> -` from the repo root. `run_import_linter_on_copy` writes a temporary `gridbot_core` package and a copy of `.importlinter`, then runs `lint-imports` from `tmp_path`.

```python
# runner/tests/test_cli.py
def test_version_flag_prints_core_version(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == "gridbot-run 0.1.0"
```

- [ ] **Step 4: Run the tests and watch them fail**

Run: `uv sync && uv run pytest core/tests runner/tests -v`
Expected: FAIL because `gridbot_core` and `gridbot_runner.cli` have no implementation.

- [ ] **Step 5: Implement the two packages**

`gridbot_core.__version__ = "0.1.0"`. `main` uses `argparse` with a `--version` action built from that value, returns `0` when no action exits, and is registered as `gridbot-run`.

- [ ] **Step 6: Run the checks**

Run: `uv run pytest core/tests runner/tests -v && uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports`
Expected: all pass.

- [ ] **Step 7: Write both READMEs with the four required headings, then commit**

```bash
git add .gitignore .python-version LICENSE pyproject.toml uv.lock .importlinter core runner
git commit -m "feat: add python workspace with core and runner"
```

### Task 2: Documentation checker

**Files:**
- Create: `scripts/check_docs.py`, `scripts/README.md`
- Test: `scripts/tests/test_check_docs.py`

**Interfaces:**
- Produces: `check_repo(root: Path) -> list[str]` (one readable problem per entry) and `main() -> int`. Run with `uv run python scripts/check_docs.py`.
- `REQUIRED_READMES`: `core`, `runner`, `gateway`, `ui`, `e2e`, `ros`, `ros/src/gridbot_msgs`, `ros/src/gridbot_sim`, `ros/src/gridbot_nodes`, `ros/src/gridbot_bringup`, `config`, `assets`, `scenarios`, `docker`, `deploy`, `scripts`, `docs`.

- [ ] **Step 1: Write the failing tests**

```python
def test_missing_readme_is_reported(tmp_path): ...
    # problems contain "core/README.md: missing"
def test_missing_required_heading_is_reported(tmp_path): ...
    # problems contain "core/README.md: missing heading '## Main files'"
def test_broken_relative_link_is_reported(tmp_path): ...
    # "[x](nope.md)" gives "README.md: broken link nope.md"
def test_broken_anchor_is_reported(tmp_path): ...
    # "[x](other.md#absent)" gives "README.md: broken link other.md#absent"
def test_valid_anchor_passes(tmp_path): ...
    # "## Topics and messages" satisfies "#topics-and-messages"
def test_external_links_and_fenced_code_are_ignored(tmp_path): ...
    # https links and a fenced "[x](nope.md)" produce no problems
```

Each test builds a minimal tree under `tmp_path` that is complete apart from the defect it names.

- [ ] **Step 2: Run the tests and watch them fail**

Run: `uv run pytest scripts/tests/test_check_docs.py -v`
Expected: FAIL because `check_docs` does not exist.

- [ ] **Step 3: Implement `check_repo` and `main`**

Use only the standard library. Scan tracked-style Markdown under `root`, skipping `.git`, `.venv`, `node_modules`, `dist`, `artifacts`, `build`, `install` and `log`. Anchors use GitHub's slug rule: lowercase, remove punctuation, spaces become hyphens. `main` prints each problem and returns `1` if any exist.

- [ ] **Step 4: Run the tests**

Run: `uv run pytest scripts/tests/test_check_docs.py -v`
Expected: PASS. The real repo is not expected to pass the checker until Task 8.

- [ ] **Step 5: Commit**

```bash
git add scripts
git commit -m "test: add documentation checker"
```

### Task 3: TypeScript workspace and `gateway`

**Files:**
- Create: `package.json`, `pnpm-workspace.yaml`, `tsconfig.base.json`, `eslint.config.mjs`, `.prettierrc.json`, `.prettierignore`
- Create: `gateway/package.json`, `gateway/tsconfig.json`, `gateway/README.md`, `gateway/src/index.ts`, `gateway/src/main.ts`
- Test: `gateway/tests/index.test.ts`

**Interfaces:**
- Produces: `versionLine(): string`, returning `gridbot-gateway 0.1.0`.
- Package name: `@gridbot/gateway`, with `build`, `start`, `test` and `typecheck` scripts. Every TypeScript package in this plan has `test` and `typecheck`. Root `packageManager` pins pnpm, and `engines.node` is `>=24`.

- [ ] **Step 1: Write the failing test**

```ts
it("reports the package version", () => {
  expect(versionLine()).toBe("gridbot-gateway 0.1.0");
});
```

- [ ] **Step 2: Run the test and watch it fail**

Run: `pnpm install && pnpm --filter @gridbot/gateway test`
Expected: FAIL because `versionLine` does not exist.

- [ ] **Step 3: Implement the package**

`index.ts` exports `versionLine`, and `main.ts` prints it. `.prettierignore` lists `docs/superpowers/` and `pnpm-lock.yaml`.

- [ ] **Step 4: Run the checks**

Run: `pnpm --filter @gridbot/gateway test && pnpm --filter @gridbot/gateway typecheck && pnpm --filter @gridbot/gateway build && pnpm exec eslint gateway && pnpm exec prettier --check gateway`
Expected: all pass.

- [ ] **Step 5: Write the README and commit**

```bash
git add package.json pnpm-workspace.yaml pnpm-lock.yaml tsconfig.base.json eslint.config.mjs .prettierrc.json .prettierignore gateway
git commit -m "feat: add typescript workspace and gateway package"
```

### Task 4: `ui` and `e2e` packages

**Files:**
- Create: `ui/package.json`, `ui/tsconfig.json`, `ui/src/index.ts`, `ui/README.md`
- Create: `e2e/package.json`, `e2e/tsconfig.json`, `e2e/src/index.ts`, `e2e/README.md`
- Test: `ui/tests/index.test.ts`, `e2e/tests/index.test.ts`

**Interfaces:**
- Produces: `versionLine(): string` in each package, returning `gridbot-ui 0.1.0` and `gridbot-e2e 0.1.0`; package names `@gridbot/ui` and `@gridbot/e2e`.

- [ ] **Step 1: Write the failing tests**

Use the Task 3 test with each package's expected string.

- [ ] **Step 2: Run the tests and watch them fail**

Run: `pnpm install && pnpm --filter @gridbot/ui test && pnpm --filter @gridbot/e2e test`
Expected: FAIL because `versionLine` does not exist.

- [ ] **Step 3: Implement both packages**

Each `index.ts` exports `versionLine`. Phase 1 replaces these placeholders with the real UI and Playwright tests.

- [ ] **Step 4: Run the checks**

Run: `pnpm -r test && pnpm -r typecheck && pnpm exec eslint ui e2e && pnpm exec prettier --check ui e2e`
Expected: all pass.

- [ ] **Step 5: Write the READMEs and commit**

```bash
git add ui e2e pnpm-lock.yaml
git commit -m "feat: add ui and e2e packages"
```

### Task 5: ROS 2 workspace

**Files:**
- Create: `ros/README.md`, `docker/ros.Dockerfile`, `.dockerignore`
- Create: `ros/src/gridbot_msgs/{package.xml,CMakeLists.txt,README.md,msg/Telemetry.msg,test/test_telemetry.py}`
- Create: `ros/src/gridbot_sim`, `ros/src/gridbot_nodes`, `ros/src/gridbot_bringup` as `ament_python` packages, each with `package.xml`, `setup.py`, `setup.cfg`, `README.md`, `resource/<name>` and one test
- Create: `ros/src/gridbot_bringup/launch/gridbot.launch.py`

**Interfaces:**
- Consumes: `gridbot_core.__version__`.
- Produces: image target built from `docker/ros.Dockerfile`; message `gridbot_msgs/msg/Telemetry`:

```text
builtin_interfaces/Time stamp
string source
string[] keys
float64[] values
```

- [ ] **Step 1: Write the failing tests**

```python
# gridbot_msgs/test/test_telemetry.py
def test_telemetry_fields():
    msg = Telemetry(source="planner", keys=["nodes"], values=[3.0])
    assert (msg.source, list(msg.keys), list(msg.values)) == ("planner", ["nodes"], [3.0])

# gridbot_sim/test/test_package.py
def test_package_imports(): assert gridbot_sim.__name__ == "gridbot_sim"

# gridbot_nodes/test/test_core_available.py
def test_core_is_importable_inside_ros(): assert gridbot_core.__version__ == "0.1.0"

# gridbot_bringup/test/test_launch.py
def test_launch_description_loads():
    assert isinstance(load_launch_module().generate_launch_description(), LaunchDescription)
```

- [ ] **Step 2: Write the image and watch the tests fail**

The image starts from `ros:jazzy-ros-base`, installs `python3-pip`, `python3-pytest` and `ros-dev-tools`, installs `/workspace/core` with `pip install --break-system-packages`, copies `ros/src`, runs `rosdep install` and `colcon build`. The flag is required because Ubuntu 24.04 marks its Python as externally managed. Pip also can't replace the image's apt NumPy 1.26.4, so when Phase 1 adds NumPy, pin it to 1.26.x across the workspace.

Run: `docker build -f docker/ros.Dockerfile -t gridbot-ros:dev . && docker run --rm gridbot-ros:dev bash -lc "colcon test && colcon test-result --verbose"`
Expected: FAIL because the package code is not complete.

- [ ] **Step 3: Implement the packages**

`gridbot_msgs` uses `rosidl_generate_interfaces` and `ament_add_pytest_test`. The launch file returns an empty `LaunchDescription`. Do not add ament lint tests, because Ruff replaces them.

- [ ] **Step 4: Run the build and tests**

Run the command from Step 2.
Expected: `colcon test-result` reports 0 errors and 0 failures across four packages.

- [ ] **Step 5: Write the READMEs and commit**

```bash
git add ros docker/ros.Dockerfile .dockerignore
git commit -m "feat: add ros 2 workspace skeleton"
```

### Task 6: Docker Compose profiles

**Files:**
- Create: `docker/compose.yaml`, `docker/gateway.Dockerfile`, `docker/runner.Dockerfile`, `docker/README.md`
- Create: `scripts/e2e_compose.sh`

**Interfaces:**
- Consumes: `docker/ros.Dockerfile`, the gateway start command, `gridbot-run --version`.
- Produces: services `gateway` (profiles `runner`, `ros`), `runner` (profile `runner`) and `ros` (profile `ros`).

- [ ] **Step 1: Write the end-to-end check**

`scripts/e2e_compose.sh` uses `set -euo pipefail`, quotes every path and always runs `docker compose down` through a trap. It must:

1. Build the `runner` and `ros` profiles.
2. Assert that `run --rm runner` prints `gridbot-run 0.1.0` (using the `runner` profile).
3. Assert that `run --rm ros ros2 pkg list` includes `gridbot_msgs`.
4. Assert that `run --rm gateway` prints `gridbot-gateway 0.1.0`.

- [ ] **Step 2: Run it and watch it fail**

Run: `bash scripts/e2e_compose.sh`
Expected: FAIL because the Compose file does not exist.

- [ ] **Step 3: Add the images and Compose file**

The gateway image is a multi-stage Node 24 build that contains the built gateway, runs as a non-root user and prints its version line. The runner image installs the uv workspace without dev dependencies and has `gridbot-run --version` as its command. All three services are one-shot in this phase, and none publishes a port.

- [ ] **Step 4: Run the check**

Run: `bash scripts/e2e_compose.sh`
Expected: exit 0, and no Gridbot containers remain.

- [ ] **Step 5: Write the README and commit**

```bash
git add docker scripts/e2e_compose.sh
git commit -m "feat: add docker compose runtime profiles"
```

### Task 7: Make targets

**Files:**
- Create: `Makefile`, `scripts/step.sh`
- Test: `scripts/tests/test_step.py`

**Interfaces:**
- Consumes: every command from Tasks 1 to 6.
- Produces: `make help`, `make verify`, `make verify-ros`, `make verify-all`, and `scripts/step.sh <label> <command> [args...]`.

- [ ] **Step 1: Write the failing tests**

```python
def test_success_prints_summary(tmp_path):
    # label "unit", command true: exit 0, stdout has "unit: passed"

def test_failure_prints_log_tail_and_exit_code(tmp_path):
    # command prints "boom" and exits 3
    # exit 3; stdout has "unit: FAILED (exit 3)" and "boom"

def test_works_from_a_path_with_spaces(tmp_path):
    # copy step.sh under "dir with spaces" and run it there; exit 0

def test_log_name_is_safe_for_labels_with_spaces_and_parens(tmp_path):
    # label "scenarios (runner)" writes artifacts/logs/scenarios-runner.log
```

- [ ] **Step 2: Run the tests and watch them fail**

Run: `uv run pytest scripts/tests/test_step.py -v`
Expected: FAIL because `step.sh` does not exist.

- [ ] **Step 3: Implement `step.sh` and the Makefile**

`step.sh` writes full output to `artifacts/logs/<slug>.log`, prints `<label>: passed` on success, and on failure prints the last 40 log lines plus `<label>: FAILED (exit N)`, then exits with `N`.

`make verify` runs these labeled steps in order, stopping at the first failure:

| Label | Command |
|---|---|
| `python lint` | `uv run ruff check .` and `uv run ruff format --check .` |
| `python types` | `uv run pyright` |
| `python boundaries` | `uv run lint-imports` |
| `python tests` | `uv run pytest` |
| `docs` | `uv run python scripts/check_docs.py` |
| `ts lint` | `pnpm exec eslint .` and `pnpm exec prettier --check .` |
| `ts types` | `pnpm -r typecheck` |
| `ts tests` | `pnpm -r test` |
| `build` | `pnpm --filter @gridbot/gateway build` |

`make verify-ros` builds the ROS image through Compose and runs `colcon test` plus `colcon test-result --verbose`. `make verify-all` runs `verify`, `verify-ros`, then `scripts/e2e_compose.sh`.

- [ ] **Step 4: Run the step tests and the available targets**

Run: `uv run pytest scripts/tests/test_step.py -v && make help && make verify-ros`
Expected: tests pass, every target is listed, and `ros tests: passed` is printed. `make verify` is expected to stop at `docs` until Task 8.

- [ ] **Step 5: Commit**

```bash
git add Makefile scripts/step.sh scripts/tests/test_step.py
git commit -m "feat: add verify commands"
```

### Task 8: Project documentation

**Files:**
- Create: `README.md`, `AGENTS.md`, `CLAUDE.md`, `docs/README.md`, `docs/architecture.md`, `docs/runtimes.md`, `docs/sensors.md`, `docs/testing.md`
- Create: `docs/decisions/0001-layered-architecture.md`, `0002-ros-2-jazzy.md`, `0003-gateway-as-public-entry.md`, `0004-ruff-replaces-ament-flake8.md`, `0005-mit-licence.md`
- Create: `docs/journal/phase-00-repo-skeleton.md`
- Create: `config/README.md`, `assets/README.md`, `scenarios/README.md`, `deploy/README.md`

**Interfaces:**
- Consumes: the real commands from `make help` and the real folder layout.

- [ ] **Step 1: Run the docs check and see the missing files**

Run: `uv run python scripts/check_docs.py`
Expected: exit 1, listing the missing top-level READMEs.

- [ ] **Step 2: Write the documentation**

- `README.md`: what Gridbot is, current status (phase 0, no robot yet), three quick-start commands, the layer diagram and a repo map. It must not claim features that do not exist.
- `AGENTS.md`: project summary, layer map, every command, the `gridbot_core` rules, what not to do, and the rule to update this file with any change that makes it wrong.
- `CLAUDE.md`: `@AGENTS.md`, plus the plan location and the `ponytail` requirement for phase plans.
- `docs/architecture.md`: the current architecture, marking what exists and what is planned.
- `docs/runtimes.md`, `docs/sensors.md`: the intended contract, labeled as planned.
- `docs/testing.md`: each make target, what it runs, where logs go, and how to debug a failed step.
- Decision records: context, decision, consequences, each under about 30 lines, taken from the spec.
- Phase journal: what was built, what was verified, what went wrong.

- [ ] **Step 3: Run humanizer, then run the checks**

Run: `make verify`
Expected: every step prints `passed`.

- [ ] **Step 4: Commit**

```bash
git add README.md AGENTS.md CLAUDE.md docs config assets scenarios deploy
git commit -m "docs: add project documentation"
```

### Task 9: CI, pre-commit and dependency updates

**Files:**
- Create: `.github/workflows/verify.yml`, `.github/workflows/verify-ros.yml`, `.github/README.md`, `.pre-commit-config.yaml`, `renovate.json`
- Modify: `scripts/check_docs.py` and its test, to require `.github/README.md`

**Interfaces:**
- Consumes: `make verify`, `make verify-ros`.
- Produces: required check named `verify`.

- [ ] **Step 1: Add the failing docs-check case**

```python
def test_github_readme_is_required(tmp_path): ...
    # problems contain ".github/README.md: missing"
```

Run: `uv run pytest scripts/tests/test_check_docs.py -v`
Expected: FAIL.

- [ ] **Step 2: Add `.github` to `REQUIRED_READMES` and make the test pass**

The scan must include `.github` while still skipping `.git`.

- [ ] **Step 3: Add the workflows and hooks**

Both workflows use `ubuntu-24.04-arm`, read-only `contents` permission and actions pinned to commit SHAs. `verify.yml` runs on every PR and on pushes to `main`: set up uv and pnpm from the repo's pinned versions, install locked dependencies, run `make verify`, and upload `artifacts/` on failure.

`verify-ros.yml` runs `make verify-ros` for PRs changing `ros/**`, `core/**`, `scenarios/**`, `docker/ros.Dockerfile` or the workflow itself.

Pre-commit runs Ruff, Prettier and the docs checker. `renovate.json` extends `config:recommended`.

- [ ] **Step 4: Validate locally**

Run: `uv run pre-commit run --all-files && make verify-all`
Expected: all hooks pass and `make verify-all` exits 0.

- [ ] **Step 5: Commit**

```bash
git add .github .pre-commit-config.yaml renovate.json scripts
git commit -m "ci: add verification workflows and hooks"
```

### Task 10: Publish and pass CI (needs the owner's approval)

**Files:**
- Modify: `docs/journal/phase-00-repo-skeleton.md`

**Interfaces:**
- Consumes: the `verify` and `verify-ros` workflows.

- [ ] **Step 1: Ask the owner for the GitHub repo name and visibility**

Do not create or push anything before the owner answers. GitHub's arm64 runner availability depends on the repo's visibility and plan, so check that before choosing private.

- [ ] **Step 2: Create the repo and push both branches**

Run: `gh repo create <owner>/<name> --source . --<visibility>`, then `git push -u origin main phase-0-skeleton`.
Expected: both branches exist on GitHub.

- [ ] **Step 3: Open the phase PR**

Run the `humanizer:humanizer` skill on the title and body. Include the `make verify-all` summary lines and what was and wasn't run.
Expected: `verify` and `verify-ros` start.

- [ ] **Step 4: Confirm CI and record it**

Expected: both checks pass. Add the result to the phase journal and commit it with `docs: record phase 0 ci result`.

- [ ] **Step 5: Offer the repository settings to the owner**

List branch protection requiring `verify` and installation of the Renovate app. Apply them only after approval.
