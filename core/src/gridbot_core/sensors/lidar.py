"""2D lidar model using a vectorized grid traversal."""

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from gridbot_core.sensors.rig import LidarSpec
from gridbot_core.types import Pose2D
from gridbot_core.world.grid import GridMap, world_to_cell

RANGE_MIN_M = 0.05
FULL_CIRCLE_DEG = 360.0

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


@dataclass(frozen=True, eq=False)
class LaserScan:
    """A scan in the sensor frame. Angles are radians, ranges are meters."""

    sensor_id: str
    angle_min: float
    angle_increment: float
    range_min: float
    range_max: float
    ranges: FloatArray  # read-only, inf means no return


def _beam_angles(spec: LidarSpec) -> tuple[float, float]:
    """Return the first beam angle and spacing in radians."""
    fov = math.radians(spec.fov_deg)
    gaps = spec.beams if spec.fov_deg == FULL_CIRCLE_DEG else spec.beams - 1
    return -fov / 2.0, fov / gaps if gaps else 0.0


def _axis_start(
    cell: int, offset_m: float, direction: FloatArray, size_m: float
) -> tuple[FloatArray, FloatArray, IntArray]:
    """Return distance to the first boundary, boundary spacing and cell step."""
    moving = direction != 0.0
    safe = np.where(moving, direction, 1.0)
    boundary = np.where(direction > 0.0, cell + 1, cell) * size_m
    first = np.where(moving, (boundary - offset_m) / safe, np.inf)
    spacing = np.where(moving, size_m / np.abs(safe), np.inf)
    return first, spacing, np.sign(direction).astype(np.int64)


def _cast_ranges(
    world: GridMap, x: float, y: float, angles: FloatArray, range_m: float
) -> FloatArray:
    """Step all rays together and return hit distances, or inf for misses."""
    start = world_to_cell(world, x, y)
    if start is None:
        return np.full(angles.shape, np.inf)
    if world.occupied[start]:
        return np.zeros(angles.shape)
    size = world.resolution_m
    next_x, gap_x, step_x = _axis_start(
        start[1], x - world.origin_x_m, np.cos(angles), size
    )
    next_y, gap_y, step_y = _axis_start(
        start[0], y - world.origin_y_m, np.sin(angles), size
    )
    rows = np.full(angles.shape, start[0], dtype=np.int64)
    cols = np.full(angles.shape, start[1], dtype=np.int64)
    active = np.arange(angles.size)
    height, width = world.occupied.shape
    # This fresh result array is filled as each ray finishes.
    ranges = np.full(angles.shape, np.inf)
    while active.size:
        use_x = next_x < next_y
        distance = np.where(use_x, next_x, next_y)
        cols = cols + np.where(use_x, step_x, 0)
        rows = rows + np.where(use_x, 0, step_y)
        next_x = np.where(use_x, next_x + gap_x, next_x)
        next_y = np.where(use_x, next_y, next_y + gap_y)
        inside = (distance <= range_m) & (rows >= 0) & (rows < height)
        inside &= (cols >= 0) & (cols < width)
        hit = np.zeros(active.shape, dtype=np.bool_)
        hit[inside] = world.occupied[rows[inside], cols[inside]]
        ranges[active[hit]] = distance[hit]
        keep = inside & ~hit
        active, rows, cols = active[keep], rows[keep], cols[keep]
        next_x, next_y = next_x[keep], next_y[keep]
        gap_x, gap_y = gap_x[keep], gap_y[keep]
        step_x, step_y = step_x[keep], step_y[keep]
    return ranges


def cast_scan(
    world: GridMap, robot: Pose2D, spec: LidarSpec, rng: np.random.Generator
) -> LaserScan:
    """Simulate one scan from a robot pose. Noise applies to hits only."""
    angle_min, increment = _beam_angles(spec)
    cos_theta, sin_theta = math.cos(robot.theta), math.sin(robot.theta)
    mount = spec.mount
    x = robot.x + mount.x * cos_theta - mount.y * sin_theta
    y = robot.y + mount.x * sin_theta + mount.y * cos_theta
    heading = robot.theta + math.radians(mount.yaw_deg)
    beams = angle_min + np.arange(spec.beams) * increment
    true_ranges = _cast_ranges(world, x, y, heading + beams, spec.range_m)
    noisy = true_ranges + rng.normal(0.0, spec.noise_sigma_m, spec.beams)
    ranges = np.where(
        np.isfinite(true_ranges),
        np.clip(noisy, RANGE_MIN_M, spec.range_m),
        np.inf,
    )
    ranges.setflags(write=False)
    return LaserScan(spec.id, angle_min, increment, RANGE_MIN_M, spec.range_m, ranges)
