"""Differential-drive motion with a round collision footprint."""

import math
from dataclasses import dataclass, replace

import numpy as np

from gridbot_core.types import TICK_S, Pose2D, Twist2D, normalize_angle
from gridbot_core.world.grid import GridMap

STRAIGHT_OMEGA_RAD_S = 1e-9


@dataclass(frozen=True, slots=True)
class RobotParams:
    """Robot limits in meters, m/s and rad/s. Slip is a unitless sigma."""

    wheel_base_m: float = 0.4
    radius_m: float = 0.25
    max_v: float = 1.0
    max_omega: float = 1.5
    slip_sigma: float = 0.0


@dataclass(frozen=True, slots=True)
class RobotState:
    """True robot state, with path length in meters."""

    pose: Pose2D
    collisions: int
    in_contact: bool
    path_length_m: float


def _clamp(value: float, limit: float) -> float:
    return max(-limit, min(limit, value))


def _actual_motion(
    cmd: Twist2D, params: RobotParams, rng: np.random.Generator
) -> tuple[float, float]:
    """Return the body velocity after limits and wheel slip."""
    v = _clamp(cmd.v, params.max_v)
    omega = _clamp(cmd.omega, params.max_omega)
    half_base = params.wheel_base_m / 2.0
    left_slip, right_slip = np.abs(rng.normal(0.0, params.slip_sigma, 2))
    left = (v - omega * half_base) * (1.0 - min(float(left_slip), 1.0))
    right = (v + omega * half_base) * (1.0 - min(float(right_slip), 1.0))
    return (left + right) / 2.0, (right - left) / params.wheel_base_m


def _integrate(pose: Pose2D, v: float, omega: float, dt_s: float) -> Pose2D:
    """Follow the exact arc for constant body velocity."""
    theta = pose.theta + omega * dt_s
    if abs(omega) < STRAIGHT_OMEGA_RAD_S:
        x = pose.x + v * dt_s * math.cos(pose.theta)
        y = pose.y + v * dt_s * math.sin(pose.theta)
    else:
        radius = v / omega
        x = pose.x + radius * (math.sin(theta) - math.sin(pose.theta))
        y = pose.y - radius * (math.cos(theta) - math.cos(pose.theta))
    return Pose2D(x, y, normalize_angle(theta))


def footprint_hits(world: GridMap, x: float, y: float, radius_m: float) -> bool:
    """Return whether a circle overlaps an occupied or off-map cell."""
    size = world.resolution_m
    col_low = math.floor((x - radius_m - world.origin_x_m) / size)
    col_high = math.floor((x + radius_m - world.origin_x_m) / size)
    row_low = math.floor((y - radius_m - world.origin_y_m) / size)
    row_high = math.floor((y + radius_m - world.origin_y_m) / size)
    rows, cols = world.occupied.shape
    if col_low < 0 or row_low < 0 or col_high >= cols or row_high >= rows:
        return True
    left = world.origin_x_m + np.arange(col_low, col_high + 1) * size
    bottom = world.origin_y_m + np.arange(row_low, row_high + 1) * size
    dx = np.clip(x, left, left + size) - x
    dy = np.clip(y, bottom, bottom + size) - y
    touches = dx[np.newaxis, :] ** 2 + dy[:, np.newaxis] ** 2 < radius_m**2
    window = world.occupied[row_low : row_high + 1, col_low : col_high + 1]
    return bool(np.any(window & touches))


def step_robot(
    state: RobotState,
    cmd: Twist2D,
    world: GridMap,
    params: RobotParams,
    rng: np.random.Generator,
    dt_s: float = TICK_S,
) -> RobotState:
    """Advance the robot. A blocked move keeps the previous pose."""
    v, omega = _actual_motion(cmd, params, rng)
    target = _integrate(state.pose, v, omega, dt_s)
    if footprint_hits(world, target.x, target.y, params.radius_m):
        collisions = state.collisions + (0 if state.in_contact else 1)
        return replace(state, collisions=collisions, in_contact=True)
    return replace(
        state,
        pose=target,
        in_contact=False,
        path_length_m=state.path_length_m + abs(v) * dt_s,
    )
