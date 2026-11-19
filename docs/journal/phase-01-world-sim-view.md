# Phase 1 · World, simulation and live view

Phase 1 added the grid world, the scripted drive, the lidar model and the Foxglove runner. The gateway relays runtime topics to browsers, and the UI draws the map, robot and rays from them. Playwright drives drive-01 through the whole stack.

The headless drive-01 run took 1128 ticks with no collisions. The robot covered 40.00 m and stopped 2.1e-7 m from its goal. Odometry drifted 0.78 m from ground truth over the run. The browser test checked that every lidar hit lies within 0.15 m of an occupied cell at ticks 0, 350 and 1128. At the last tick the drawn pose matched the headless end pose exactly in x and y, and to 12 decimal places in heading. The three screenshots show the robot at its start, at (17, 3) after 14.00 m, and back at the start after 40.00 m.

Test mode publishes the world and static transforms only at tick 0 and every 20 ticks after it, so the browser test steps to tick 0 before it reads the grid. The heading mark first covered the robot's centre pixel and failed the colour check. It now starts 40% of the way out from the centre.

`uv run` forwards SIGTERM to the runner, which then received the signal twice and raised inside the Foxglove server's shutdown. The runner now ignores further SIGTERMs once it starts stopping. On this Mac the `.venv` files were hidden four times during the phase, which breaks `gridbot_core` imports. `chflags -R nohidden .venv` restores them, and AGENTS.md records the fix.

The whole-branch review was a self-review with the code-review skill. It found four problems, each fixed with a test that failed first:

- With two lidars, the UI drew every ray from the first sensor's mount. Each sensor's rays now start at its own mount.
- The UI accepted a world with zero, negative or fractional dimensions. It now requires positive whole cell counts.
- The UI treated any unknown message type as a status update. It now ignores them.
- The Compose smoke test failed when host port 8080 was busy. `GRIDBOT_HOST_PORT` now sets the published port, and the smoke test uses `0`.

Four smaller findings were left for later. Frames wait for a scan from every static transform child, which only matters once a rig has a sensor other than lidar. The gateway drops a test step without an error when the runtime link is down. The browser test parses the world message itself instead of reusing the UI parser. The UI reads its palette from CSS on every repaint.

`make verify-all` passed locally after the fixes, covering Python lint, types, boundaries and tests, the scenario run, docs, TypeScript lint, types and tests, the build, the browser test, the ROS tests and the Compose smoke test.
