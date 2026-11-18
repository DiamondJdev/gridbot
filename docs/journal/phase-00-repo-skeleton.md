# Phase 0 · Repository skeleton

Phase 0 set up the Python, TypeScript and ROS workspaces, Docker profiles and Make targets. It added package and container smoke tests. Simulation starts in Phase 1.

The Python and TypeScript workspace checks passed locally. The ROS image built all four packages. The Compose smoke test found the runner and gateway version lines and the installed `gridbot_msgs` package, then removed its project.

Colcon initially selected unittest for the ROS Python packages. Their setup metadata now selects pytest. The message build initially produced Python bindings without registering the package in the ROS overlay. Its manifest now declares the `ament_cmake` build type.
