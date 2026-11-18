# Sensors

Sensor rigs are planned. Phase 0 has no sensor models or rig YAML files.

A rig in `config/rigs/` will list sensors by ID. Each entry has a type and a mount pose in meters and degrees. A lidar entry sets the field of view, beam count, maximum range and noise. The rig can also configure wheel odometry noise and gyro bias and noise. ROS will publish each mount as a static transform.

| Sensor         | Planned model                                                 |
| -------------- | ------------------------------------------------------------- |
| 2D lidar       | Rays cast through the occupancy grid, with range noise        |
| Sonar          | Closest obstacle inside a wide cone                           |
| Wheel encoders | Wheel motion with configurable translation and rotation noise |
| Gyro           | Angular rate with bias and noise                              |

The baseline rig is `lidar-360`. The [design](superpowers/specs/2026-11-17-gridbot-design.md#sensor-rigs) lists the other rigs and shows a dual-lidar config. A scenario names the rig, and a run config can override it. Reference comparisons use single-lidar rigs.
