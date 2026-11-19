"""Convert simulation frames to JSON messages with ROS field names."""

import math

import numpy as np
from gridbot_core.sensors.lidar import LaserScan
from gridbot_core.sensors.rig import Rig
from gridbot_core.sim.world_step import Frame
from gridbot_core.types import TICK_NS, TICK_S, Pose2D, Twist2D
from gridbot_core.world.grid import GridMap

Message = dict[str, object]
LATCH_EVERY_TICKS = 20
NANOS_PER_SECOND = 1_000_000_000
OCCUPIED = 100
FREE = 0
MAP_FRAME = "map"
ODOM_FRAME = "odom"
BASE_FRAME = "base_link"
TELEMETRY_KEYS = ["tick", "collisions", "pathLengthM"]


def _stamp(stamp_ns: int) -> Message:
    sec, nanosec = divmod(stamp_ns, NANOS_PER_SECOND)
    return {"sec": sec, "nanosec": nanosec}


def _header(stamp_ns: int, frame_id: str) -> Message:
    return {"stamp": _stamp(stamp_ns), "frame_id": frame_id}


def _vector(x: float = 0.0, y: float = 0.0, z: float = 0.0) -> Message:
    return {"x": x, "y": y, "z": z}


def _quaternion(yaw: float) -> Message:
    return {"x": 0.0, "y": 0.0, "z": math.sin(yaw / 2.0), "w": math.cos(yaw / 2.0)}


def _pose(pose: Pose2D) -> Message:
    return {"position": _vector(pose.x, pose.y), "orientation": _quaternion(pose.theta)}


def _twist(cmd: Twist2D) -> Message:
    return {"linear": _vector(cmd.v), "angular": _vector(z=cmd.omega)}


def _transform(stamp_ns: int, parent: str, child: str, pose: Pose2D) -> Message:
    return {
        "header": _header(stamp_ns, parent),
        "child_frame_id": child,
        "transform": {
            "translation": _vector(pose.x, pose.y),
            "rotation": _quaternion(pose.theta),
        },
    }


def scan_message(scan: LaserScan, stamp_ns: int) -> Message:
    """Return ``sensor_msgs/LaserScan``. Missing returns become ``None``."""
    count = len(scan.ranges)
    return {
        "header": _header(stamp_ns, scan.sensor_id),
        "angle_min": scan.angle_min,
        "angle_max": scan.angle_min + scan.angle_increment * (count - 1),
        "angle_increment": scan.angle_increment,
        "time_increment": 0.0,
        "scan_time": TICK_S,
        "range_min": scan.range_min,
        "range_max": scan.range_max,
        "ranges": [float(r) if math.isfinite(r) else None for r in scan.ranges],
        "intensities": [],
    }


def world_message(world: GridMap) -> Message:
    """Return ``nav_msgs/OccupancyGrid`` with rows from south to north."""
    height, width = world.occupied.shape
    origin = Pose2D(world.origin_x_m, world.origin_y_m, 0.0)
    return {
        "header": _header(0, MAP_FRAME),
        "info": {
            "map_load_time": _stamp(0),
            "resolution": world.resolution_m,
            "width": width,
            "height": height,
            "origin": _pose(origin),
        },
        "data": np.where(world.occupied, OCCUPIED, FREE).ravel().tolist(),
    }


def _static_transforms(rig: Rig) -> Message:
    return {
        "transforms": [
            _transform(
                0,
                BASE_FRAME,
                sensor.id,
                Pose2D(
                    sensor.mount.x, sensor.mount.y, math.radians(sensor.mount.yaw_deg)
                ),
            )
            for sensor in rig.sensors
        ]
    }


def _odometry(frame: Frame, stamp_ns: int) -> Message:
    zeros = [0.0] * 36
    return {
        "header": _header(stamp_ns, ODOM_FRAME),
        "child_frame_id": BASE_FRAME,
        "pose": {"pose": _pose(frame.odom_pose), "covariance": zeros},
        # The simulator has no velocity estimate yet, so this is the command.
        "twist": {"twist": _twist(frame.cmd), "covariance": zeros},
    }


def _telemetry(frame: Frame, stamp_ns: int) -> Message:
    values = [float(frame.tick), float(frame.collisions), frame.path_length_m]
    return {
        "stamp": _stamp(stamp_ns),
        "source": "sim",
        "keys": TELEMETRY_KEYS,
        "values": values,
    }


def topics(rig: Rig) -> list[str]:
    """Return every topic a run publishes, so channels exist before tick 0."""
    scans = [f"/scan/{sensor.id}" for sensor in rig.sensors]
    return [
        "/sim/world",
        "/tf_static",
        *scans,
        "/odom",
        "/tf",
        "/sim/ground_truth",
        "/cmd_vel",
        "/telemetry",
    ]


def frame_messages(frame: Frame, world: GridMap, rig: Rig) -> list[tuple[str, Message]]:
    """Return a tick's messages in publish order, ending with ``/telemetry``."""
    stamp_ns = frame.tick * TICK_NS
    latched: list[tuple[str, Message]] = []
    if frame.tick % LATCH_EVERY_TICKS == 0:
        latched = [
            ("/sim/world", world_message(world)),
            ("/tf_static", _static_transforms(rig)),
        ]
    odom_tf = _transform(stamp_ns, ODOM_FRAME, BASE_FRAME, frame.odom_pose)
    truth: Message = {
        "header": _header(stamp_ns, MAP_FRAME),
        "pose": _pose(frame.true_pose),
    }
    return [
        *latched,
        *((f"/scan/{s.sensor_id}", scan_message(s, stamp_ns)) for s in frame.scans),
        ("/odom", _odometry(frame, stamp_ns)),
        ("/tf", {"transforms": [odom_tf]}),
        ("/sim/ground_truth", truth),
        ("/cmd_vel", _twist(frame.cmd)),
        ("/telemetry", _telemetry(frame, stamp_ns)),
    ]
