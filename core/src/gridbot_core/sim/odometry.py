"""Wheel odometry with noise proportional to motion."""

import math

import numpy as np

from gridbot_core.sensors.rig import Odometry
from gridbot_core.types import Pose2D, normalize_angle


def step_odometry(
    odom: Pose2D,
    before: Pose2D,
    after: Pose2D,
    noise: Odometry,
    rng: np.random.Generator,
) -> Pose2D:
    """Apply the true motion between two poses to the odometry estimate."""
    dx = after.x - before.x
    dy = after.y - before.y
    forward = dx * math.cos(before.theta) + dy * math.sin(before.theta)
    distance = math.copysign(math.hypot(dx, dy), forward)
    turn = normalize_angle(after.theta - before.theta)
    measured_distance = distance + float(
        rng.normal(0.0, noise.wheel_noise.trans * abs(distance))
    )
    measured_turn = turn + float(rng.normal(0.0, noise.wheel_noise.rot * abs(turn)))
    heading = odom.theta + measured_turn / 2.0
    return Pose2D(
        odom.x + measured_distance * math.cos(heading),
        odom.y + measured_distance * math.sin(heading),
        normalize_angle(odom.theta + measured_turn),
    )
