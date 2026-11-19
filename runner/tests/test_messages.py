import json
import math
from pathlib import Path
from typing import cast

import numpy as np
from gridbot_core.scenario.loader import load_rig
from gridbot_core.sensors.lidar import LaserScan
from gridbot_core.sim.world_step import Frame
from gridbot_core.types import Pose2D, Twist2D
from gridbot_core.world.grid import GridMap
from gridbot_core.world.loader import load_map
from gridbot_runner.messages import frame_messages, topics

ROOT = Path(__file__).resolve().parents[2]
RIG = load_rig(ROOT / "config/rigs/lidar-360.yaml")
WORLD = load_map(ROOT / "assets/warehouse-01.yaml")
TICK_TOPICS = [
    "/scan/lidar",
    "/odom",
    "/tf",
    "/sim/ground_truth",
    "/cmd_vel",
    "/telemetry",
]


def frame(tick: int = 1, theta: float = 0.5) -> Frame:
    ranges = np.array([1.5, math.inf, 2.0])
    ranges.setflags(write=False)
    scan = LaserScan("lidar", -math.pi, 2 * math.pi / 3, 0.05, 10.0, ranges)
    return Frame(
        tick=tick,
        true_pose=Pose2D(3.0, 4.0, theta),
        odom_pose=Pose2D(3.1, 4.1, theta),
        cmd=Twist2D(0.8, 0.2),
        scans=(scan,),
        collisions=2,
        path_length_m=1.25,
    )


def messages(tick: int = 1, world: GridMap = WORLD) -> dict[str, dict[str, object]]:
    return dict(frame_messages(frame(tick), world, RIG))


def field(message: object, *path: str | int) -> object:
    value = message
    for key in path:
        if isinstance(key, int):
            value = cast(list[object], value)[key]
        else:
            value = cast(dict[str, object], value)[key]
    return value


def test_tick_topics_end_with_telemetry() -> None:
    topics = [topic for topic, _ in frame_messages(frame(1), WORLD, RIG)]
    assert topics == TICK_TOPICS


def test_latched_topics_are_sent_every_20_ticks_before_telemetry() -> None:
    for tick in (0, 20):
        topics = [topic for topic, _ in frame_messages(frame(tick), WORLD, RIG)]
        assert topics == ["/sim/world", "/tf_static", *TICK_TOPICS]
    assert "/sim/world" not in messages(19)


def test_no_return_serializes_as_null() -> None:
    assert field(messages()["/scan/lidar"], "ranges") == [1.5, None, 2.0]


def test_scan_uses_ros_fields() -> None:
    scan = messages()["/scan/lidar"]
    assert field(scan, "header", "frame_id") == "lidar"
    angle_max = field(scan, "angle_max")
    assert isinstance(angle_max, float)
    assert math.isclose(angle_max, math.pi / 3)
    assert field(scan, "range_max") == 10.0


def test_payloads_are_strict_json() -> None:
    for _, message in frame_messages(frame(0), WORLD, RIG):
        json.dumps(message, allow_nan=False)


def test_stamps_are_exact_integers() -> None:
    stamp = field(messages(1128)["/odom"], "header", "stamp")
    assert stamp == {"sec": 56, "nanosec": 400_000_000}


def test_latched_stamps_are_fixed() -> None:
    latched = messages(20)
    for topic in ("/sim/world",):
        assert field(latched[topic], "header", "stamp") == {"sec": 0, "nanosec": 0}
    stamp = field(latched["/tf_static"], "transforms", 0, "header", "stamp")
    assert stamp == {"sec": 0, "nanosec": 0}


def test_poses_use_quaternions() -> None:
    orientation = field(messages()["/sim/ground_truth"], "pose", "orientation")
    assert orientation == {"x": 0.0, "y": 0.0, "z": math.sin(0.25), "w": math.cos(0.25)}


def test_ground_truth_and_odometry_differ() -> None:
    sent = messages()
    truth = field(sent["/sim/ground_truth"], "pose", "position", "x")
    odom = field(sent["/odom"], "pose", "pose", "position", "x")
    assert (truth, odom) == (3.0, 3.1)


def test_telemetry_reports_tick() -> None:
    telemetry = messages(7)["/telemetry"]
    assert field(telemetry, "source") == "sim"
    assert field(telemetry, "keys") == ["tick", "collisions", "pathLengthM"]
    assert field(telemetry, "values") == [7.0, 2.0, 1.25]


def test_static_transform_uses_mount() -> None:
    sensor = field(messages(0)["/tf_static"], "transforms", 0)
    assert field(sensor, "header", "frame_id") == "base_link"
    assert field(sensor, "child_frame_id") == "lidar"
    assert field(sensor, "transform", "translation", "x") == 0.10


def test_world_uses_ros_fields_and_south_first_rows() -> None:
    occupied = np.zeros((2, 3), dtype=np.bool_)
    occupied[1, 0] = True
    small = GridMap(0.5, -1.0, 2.0, occupied)
    world = messages(0, small)["/sim/world"]
    assert field(world, "info", "width") == 3
    assert field(world, "info", "height") == 2
    assert field(world, "info", "resolution") == 0.5
    assert field(world, "info", "origin", "position") == {"x": -1.0, "y": 2.0, "z": 0.0}
    assert field(world, "data") == [0, 0, 0, 100, 0, 0]


def test_topics_lists_every_published_topic_up_front() -> None:
    published = [topic for topic, _ in frame_messages(frame(0), WORLD, RIG)]
    assert topics(RIG) == published
