import math

import numpy as np
import pytest

from gridbot_core.sensors.rig import Odometry, WheelNoise
from gridbot_core.sim.drive import (
    RobotParams,
    RobotState,
    footprint_hits,
    step_robot,
)
from gridbot_core.sim.odometry import step_odometry
from gridbot_core.types import TICK_S, Pose2D, Twist2D
from gridbot_core.world.grid import GridMap

PARAMS = RobotParams()
RESOLUTION_M = 0.05
SIZE_CELLS = 200
WALL_START_COL = 100
NO_NOISE = Odometry(wheel_noise=WheelNoise(trans=0.0, rot=0.0))


def rng() -> np.random.Generator:
    return np.random.default_rng(7)


def open_world() -> GridMap:
    occupied = np.zeros((SIZE_CELLS, SIZE_CELLS), dtype=np.bool_)
    occupied.setflags(write=False)
    return GridMap(RESOLUTION_M, 0.0, 0.0, occupied)


def wall_world() -> GridMap:
    occupied = np.zeros((SIZE_CELLS, SIZE_CELLS), dtype=np.bool_)
    occupied[:, WALL_START_COL:] = True
    occupied.setflags(write=False)
    return GridMap(RESOLUTION_M, 0.0, 0.0, occupied)


def robot_at(x: float, y: float, theta: float = 0.0) -> RobotState:
    return RobotState(Pose2D(x, y, theta), 0, False, 0.0)


def drive(
    state: RobotState, cmd: Twist2D, world: GridMap, ticks: int, params: RobotParams
) -> RobotState:
    generator = rng()
    current = state
    for _ in range(ticks):
        current = step_robot(current, cmd, world, params, generator)
    return current


def test_straight_line_distance() -> None:
    end = drive(robot_at(2.0, 5.0), Twist2D(0.5, 0.0), open_world(), 20, PARAMS)
    assert math.isclose(end.pose.x, 2.5)
    assert end.pose.y == 5.0
    assert math.isclose(end.path_length_m, 0.5)


def test_quarter_turn_in_place_keeps_position() -> None:
    start = robot_at(5.0, 5.0)
    end = step_robot(
        start, Twist2D(0.0, 1.0), open_world(), PARAMS, rng(), dt_s=math.pi / 2
    )
    assert (end.pose.x, end.pose.y) == (5.0, 5.0)
    assert math.isclose(end.pose.theta, math.pi / 2)
    assert end.path_length_m == 0.0


def test_arc_matches_closed_form() -> None:
    ticks = 10
    end = drive(robot_at(5.0, 5.0), Twist2D(0.5, 0.5), open_world(), ticks, PARAMS)
    angle = 0.5 * ticks * TICK_S
    assert math.isclose(end.pose.x, 5.0 + math.sin(angle))
    assert math.isclose(end.pose.y, 5.0 + 1.0 - math.cos(angle))
    assert math.isclose(end.pose.theta, angle)


def test_heading_stays_normalized() -> None:
    start = robot_at(5.0, 5.0, 3.1)
    end = step_robot(start, Twist2D(0.0, 1.0), open_world(), PARAMS, rng())
    assert -math.pi < end.pose.theta <= math.pi
    assert end.pose.theta < 0.0


def test_command_is_clamped() -> None:
    start = robot_at(5.0, 5.0)
    end = step_robot(start, Twist2D(9.0, 0.0), open_world(), PARAMS, rng())
    turned = step_robot(start, Twist2D(0.0, -9.0), open_world(), PARAMS, rng())
    assert math.isclose(end.pose.x, 5.0 + PARAMS.max_v * TICK_S)
    assert math.isclose(turned.pose.theta, -PARAMS.max_omega * TICK_S)


def test_slip_only_slows_the_robot() -> None:
    params = RobotParams(slip_sigma=0.3)
    start = robot_at(2.0, 5.0)
    end = drive(start, Twist2D(0.5, 0.0), open_world(), 20, params)
    assert 2.0 < end.pose.x < 2.5
    assert end.pose == drive(start, Twist2D(0.5, 0.0), open_world(), 20, params).pose


def test_wall_blocks_and_counts_contact_once() -> None:
    world = wall_world()
    end = drive(robot_at(4.7, 5.0), Twist2D(0.5, 0.0), world, 20, PARAMS)
    assert end.pose.x <= 4.75 + 1e-9
    assert end.collisions == 1
    assert end.in_contact
    assert end.path_length_m <= 0.05 + 1e-9


def test_leaving_contact_allows_a_new_collision() -> None:
    world = wall_world()
    touching = drive(robot_at(4.7, 5.0), Twist2D(0.5, 0.0), world, 5, PARAMS)
    backed = drive(touching, Twist2D(-0.5, 0.0), world, 2, PARAMS)
    assert not backed.in_contact
    again = drive(backed, Twist2D(0.5, 0.0), world, 5, PARAMS)
    assert again.collisions == 2


def test_map_edge_counts_as_occupied() -> None:
    world = open_world()
    assert footprint_hits(world, 0.2, 5.0, PARAMS.radius_m)
    assert not footprint_hits(world, 0.3, 5.0, PARAMS.radius_m)


def test_footprint_is_round() -> None:
    occupied = np.zeros((SIZE_CELLS, SIZE_CELLS), dtype=np.bool_)
    occupied[100, 100] = True
    world = GridMap(RESOLUTION_M, 0.0, 0.0, occupied)
    assert not footprint_hits(world, 4.8, 4.8, PARAMS.radius_m)
    assert footprint_hits(world, 4.8, 5.02, PARAMS.radius_m)


def test_inputs_are_not_mutated() -> None:
    start = robot_at(2.0, 5.0)
    copy = robot_at(2.0, 5.0)
    moved = step_robot(start, Twist2D(0.5, 0.0), open_world(), PARAMS, rng())
    assert start == copy
    assert moved is not start


def test_stationary_odometry_does_not_drift() -> None:
    noise = Odometry(wheel_noise=WheelNoise(trans=0.5, rot=0.5))
    pose = Pose2D(1.0, 2.0, 0.3)
    odom = Pose2D(4.0, 5.0, -1.0)
    assert step_odometry(odom, pose, pose, noise, rng()) == odom


def test_noiseless_odometry_follows_motion_in_its_own_frame() -> None:
    before = Pose2D(1.0, 1.0, math.pi / 2)
    after = Pose2D(1.0, 2.0, math.pi / 2)
    odom = step_odometry(Pose2D(0.0, 0.0, 0.0), before, after, NO_NOISE, rng())
    assert math.isclose(odom.x, 1.0)
    assert math.isclose(odom.y, 0.0, abs_tol=1e-12)
    assert odom.theta == 0.0


def test_noiseless_odometry_tracks_reverse_motion() -> None:
    before = Pose2D(2.0, 0.0, 0.0)
    after = Pose2D(1.0, 0.0, 0.0)
    odom = step_odometry(Pose2D(0.0, 0.0, 0.0), before, after, NO_NOISE, rng())
    assert math.isclose(odom.x, -1.0)


@pytest.mark.parametrize("distance_m", [1.0, 2.0])
def test_odometry_noise_scales_with_motion(distance_m: float) -> None:
    noise = Odometry(wheel_noise=WheelNoise(trans=0.02, rot=0.0))
    generator = rng()
    before = Pose2D(0.0, 0.0, 0.0)
    after = Pose2D(distance_m, 0.0, 0.0)
    samples = [
        step_odometry(before, before, after, noise, generator).x - distance_m
        for _ in range(4000)
    ]
    assert math.isclose(float(np.std(samples)), 0.02 * distance_m, rel_tol=0.08)


def test_rotation_noise_scales_with_turn() -> None:
    noise = Odometry(wheel_noise=WheelNoise(trans=0.0, rot=0.05))
    generator = rng()
    before = Pose2D(0.0, 0.0, 0.0)
    after = Pose2D(0.0, 0.0, 1.0)
    samples = [
        step_odometry(before, before, after, noise, generator).theta - 1.0
        for _ in range(4000)
    ]
    assert math.isclose(float(np.std(samples)), 0.05, rel_tol=0.08)
