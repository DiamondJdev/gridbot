# Phase 0 · Repository skeleton

Phase 0 set up the Python, TypeScript and ROS workspaces, Docker profiles and Make targets. It added package and container smoke tests. Simulation starts in Phase 1.

The Python and TypeScript workspace checks passed locally. The ROS image built all four packages. The Compose smoke test found the runner and gateway version lines and the installed `gridbot_msgs` package, then removed its project.

Colcon initially selected unittest for the ROS Python packages. Their setup metadata now selects pytest. The message build initially produced Python bindings without registering the package in the ROS overlay. Its manifest now declares the `ament_cmake` build type.

Pre-commit and `make verify-all` passed locally. A fresh source copy under a path with spaces passed the same Make checks. Actionlint checked both workflows.

On [PR #1](https://github.com/DiamondJdev/gridbot/pull/1), the first host check stopped before running tests. The setup action expected a TOML version file. Moving the uv pin to `pyproject.toml` fixed the setup. Both [verify](https://github.com/DiamondJdev/gridbot/actions/runs/44407958299) and [verify-ros](https://github.com/DiamondJdev/gridbot/actions/runs/44407958053) passed on Arm Linux at `a97f410`.
