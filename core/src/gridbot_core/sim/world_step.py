"""Advance a scenario one fixed tick at a time."""

from dataclasses import dataclass

import numpy as np

from gridbot_core.scenario.loader import ScenarioError
from gridbot_core.scenario.models import Scenario
from gridbot_core.sensors.lidar import LaserScan, cast_scan
from gridbot_core.sensors.rig import Rig
from gridbot_core.sim.drive import (
    RobotParams,
    RobotState,
    footprint_hits,
    step_robot,
)
from gridbot_core.sim.odometry import step_odometry
from gridbot_core.types import Pose2D, Twist2D
from gridbot_core.world.grid import GridMap

ROBOT = RobotParams()
SLIP_STREAM = 0
ODOMETRY_STREAM = 1
FIRST_SENSOR_STREAM = 2
STOPPED = Twist2D(0.0, 0.0)


@dataclass(frozen=True, eq=False)
class Frame:
    """State at a tick and the command about to be applied."""

    tick: int
    true_pose: Pose2D
    odom_pose: Pose2D
    cmd: Twist2D
    scans: tuple[LaserScan, ...]
    collisions: int
    path_length_m: float


@dataclass(frozen=True, eq=False)
class SimRngs:
    """Independent random streams, so adding a sensor changes nothing else."""

    slip: np.random.Generator
    odometry: np.random.Generator
    sensors: tuple[np.random.Generator, ...]


@dataclass(frozen=True, eq=False)
class SimState:
    """The latest frame and the true robot state behind it."""

    frame: Frame
    robot: RobotState


def make_rngs(seed: int, rig: Rig) -> SimRngs:
    """Create one seeded random stream per noise source."""
    return SimRngs(
        np.random.default_rng([seed, SLIP_STREAM]),
        np.random.default_rng([seed, ODOMETRY_STREAM]),
        tuple(
            np.random.default_rng([seed, FIRST_SENSOR_STREAM + index])
            for index in range(len(rig.sensors))
        ),
    )


def _command_at(scenario: Scenario, tick: int) -> Twist2D:
    end = 0
    for segment in scenario.drive:
        end += segment.ticks
        if tick < end:
            return Twist2D(segment.v, segment.omega)
    return STOPPED


def _scans(
    pose: Pose2D, world: GridMap, rig: Rig, rngs: SimRngs
) -> tuple[LaserScan, ...]:
    return tuple(
        cast_scan(world, pose, sensor, rng)
        for sensor, rng in zip(rig.sensors, rngs.sensors, strict=True)
    )


def _state(
    tick: int,
    robot: RobotState,
    odom: Pose2D,
    scenario: Scenario,
    world: GridMap,
    rig: Rig,
    rngs: SimRngs,
) -> SimState:
    frame = Frame(
        tick,
        robot.pose,
        odom,
        _command_at(scenario, tick),
        _scans(robot.pose, world, rig, rngs),
        robot.collisions,
        robot.path_length_m,
    )
    return SimState(frame, robot)


def first_frame(
    scenario: Scenario, world: GridMap, rig: Rig, rngs: SimRngs
) -> SimState:
    """Return tick 0, or raise ``ScenarioError`` if the start is blocked."""
    pose = scenario.start.to_pose()
    if footprint_hits(world, pose.x, pose.y, ROBOT.radius_m):
        raise ScenarioError(
            f"{scenario.name}: start overlaps an obstacle or the map edge"
        )
    robot = RobotState(pose, 0, False, 0.0)
    return _state(0, robot, pose, scenario, world, rig, rngs)


def next_frame(
    state: SimState, scenario: Scenario, world: GridMap, rig: Rig, rngs: SimRngs
) -> SimState:
    """Apply the current frame's command and return the following tick."""
    frame = state.frame
    robot = step_robot(state.robot, frame.cmd, world, ROBOT, rngs.slip)
    odom = step_odometry(
        frame.odom_pose,
        state.robot.pose,
        robot.pose,
        rig.odometry,
        rngs.odometry,
    )
    return _state(frame.tick + 1, robot, odom, scenario, world, rig, rngs)
