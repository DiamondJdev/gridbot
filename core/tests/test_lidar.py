import math

import numpy as np
import pytest

from gridbot_core.sensors.lidar import RANGE_MIN_M, cast_scan
from gridbot_core.sensors.rig import LidarSpec, Mount
from gridbot_core.types import Pose2D
from gridbot_core.world.grid import GridMap

RESOLUTION_M = 0.05
SIZE_CELLS = 200
WALL_START_COL = 100
EAST_BEAM = 4
NORTHEAST_BEAM = 5
WEST_BEAM = 0
TOLERANCE_M = 1e-9


def rng() -> np.random.Generator:
    return np.random.default_rng(11)


def east_wall_world() -> GridMap:
    occupied = np.zeros((SIZE_CELLS, SIZE_CELLS), dtype=np.bool_)
    occupied[:, WALL_START_COL:] = True
    occupied.setflags(write=False)
    return GridMap(RESOLUTION_M, 0.0, 0.0, occupied)


def lidar(
    *,
    x: float = 0.0,
    yaw_deg: float = 0.0,
    fov_deg: float = 360.0,
    beams: int = 8,
    range_m: float = 10.0,
    noise_sigma_m: float = 0.0,
) -> LidarSpec:
    return LidarSpec(
        id="lidar",
        type="lidar",
        mount=Mount(x=x, y=0.0, yaw_deg=yaw_deg),
        fov_deg=fov_deg,
        beams=beams,
        range_m=range_m,
        noise_sigma_m=noise_sigma_m,
    )


def test_ray_hits_wall_at_known_distance() -> None:
    scan = cast_scan(east_wall_world(), Pose2D(4.0, 5.0, 0.0), lidar(), rng())
    assert math.isclose(scan.ranges[EAST_BEAM], 1.0, abs_tol=TOLERANCE_M)
    assert math.isclose(
        scan.ranges[NORTHEAST_BEAM], math.sqrt(2.0), abs_tol=TOLERANCE_M
    )


def test_ray_leaving_map_is_inf() -> None:
    scan = cast_scan(east_wall_world(), Pose2D(4.0, 5.0, 0.0), lidar(), rng())
    assert math.isinf(scan.ranges[WEST_BEAM])


def test_beyond_range_is_inf() -> None:
    spec = lidar(range_m=0.5)
    scan = cast_scan(east_wall_world(), Pose2D(4.0, 5.0, 0.0), spec, rng())
    assert math.isinf(scan.ranges[EAST_BEAM])


def test_origin_in_wall_returns_range_min() -> None:
    scan = cast_scan(east_wall_world(), Pose2D(6.0, 5.0, 0.0), lidar(), rng())
    assert np.all(scan.ranges == RANGE_MIN_M)


def test_origin_off_map_has_no_returns() -> None:
    scan = cast_scan(east_wall_world(), Pose2D(-1.0, 5.0, 0.0), lidar(), rng())
    assert np.all(np.isinf(scan.ranges))


def test_mount_offset_is_applied() -> None:
    world = east_wall_world()
    forward = cast_scan(world, Pose2D(4.0, 5.0, 0.0), lidar(x=0.1), rng())
    backward = cast_scan(world, Pose2D(4.0, 5.0, math.pi), lidar(x=0.1), rng())
    assert math.isclose(forward.ranges[EAST_BEAM], 0.9, abs_tol=TOLERANCE_M)
    assert math.isclose(backward.ranges[WEST_BEAM], 1.1, abs_tol=TOLERANCE_M)


def test_mount_yaw_is_applied() -> None:
    spec = lidar(yaw_deg=180.0)
    scan = cast_scan(east_wall_world(), Pose2D(4.0, 5.0, 0.0), spec, rng())
    assert math.isclose(scan.ranges[WEST_BEAM], 1.0, abs_tol=TOLERANCE_M)
    assert math.isinf(scan.ranges[EAST_BEAM])


def test_360_degree_spacing_does_not_repeat_a_beam() -> None:
    spec = lidar(beams=360)
    scan = cast_scan(east_wall_world(), Pose2D(4.0, 5.0, 0.0), spec, rng())
    assert math.isclose(scan.angle_min, -math.pi)
    assert math.isclose(scan.angle_increment, math.radians(1.0))


def test_270_degree_spacing() -> None:
    spec = lidar(fov_deg=270.0, beams=541)
    scan = cast_scan(east_wall_world(), Pose2D(4.0, 5.0, 0.0), spec, rng())
    assert scan.ranges.shape == (541,)
    assert math.isclose(scan.angle_min, math.radians(-135.0))
    assert math.isclose(scan.angle_increment, math.radians(0.5))


def test_noise_never_turns_miss_into_hit() -> None:
    spec = lidar(noise_sigma_m=0.5)
    scan = cast_scan(east_wall_world(), Pose2D(4.0, 5.0, 0.0), spec, rng())
    assert math.isinf(scan.ranges[WEST_BEAM])
    hits = scan.ranges[np.isfinite(scan.ranges)]
    assert hits.size > 0
    assert np.all((hits >= scan.range_min) & (hits <= scan.range_max))
    assert not math.isclose(scan.ranges[EAST_BEAM], 1.0, abs_tol=TOLERANCE_M)


def test_ranges_are_read_only() -> None:
    scan = cast_scan(east_wall_world(), Pose2D(4.0, 5.0, 0.0), lidar(), rng())
    with pytest.raises(ValueError, match="read-only"):
        scan.ranges[0] = 1.0
