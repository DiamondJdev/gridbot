import math
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from gridbot_core.metrics.run import run_metrics
from gridbot_core.scenario.loader import ScenarioError, load_rig
from gridbot_core.scenario.models import Scenario
from gridbot_core.sensors.lidar import cast_scan
from gridbot_core.sensors.rig import Rig
from gridbot_core.sim.world_step import (
    Frame,
    SimState,
    first_frame,
    make_rngs,
    next_frame,
)
from gridbot_core.types import TICK_S, Pose2D
from gridbot_core.world.grid import GridMap
from gridbot_core.world.loader import load_map

ROOT = Path(__file__).resolve().parents[2]
SPEED_M_S = 0.5
SCRIPT_TICKS = 3
MAX_TICKS = 6


def world() -> GridMap:
    return load_map(ROOT / "assets/warehouse-01.yaml")


def rig() -> Rig:
    return load_rig(ROOT / "config/rigs/lidar-360.yaml")


def scenario(x: float = 3.0, y: float = 3.0) -> Scenario:
    return Scenario.model_validate(
        {
            "name": "sample",
            "note": "Short drive.",
            "map": "warehouse-01",
            "rig": "lidar-360",
            "mode": "drive",
            "seed": 42,
            "start": {"x": x, "y": y, "theta": 0.0},
            "drive": [{"ticks": SCRIPT_TICKS, "v": SPEED_M_S, "omega": 0.0}],
            "maxTicks": MAX_TICKS,
            "expect": {
                "collisions": 0,
                "minPathLengthM": 0.05,
                "endWithinM": {"x": 3.075, "y": 3.0, "radiusM": 0.01},
                "maxOdomErrorM": 0.5,
            },
        }
    )


def run(active_rig: Rig) -> list[SimState]:
    plan = scenario()
    grid = world()
    rngs = make_rngs(plan.seed, active_rig)
    states = [first_frame(plan, grid, active_rig, rngs)]
    for _ in range(MAX_TICKS):
        states.append(next_frame(states[-1], plan, grid, active_rig, rngs))
    return states


def noiseless_rig() -> Rig:
    base = rig()
    sensor = base.sensors[0].model_copy(update={"noise_sigma_m": 0.0})
    return base.model_copy(update={"sensors": (sensor,)})


def two_sensor_rig() -> Rig:
    base = rig()
    second = base.sensors[0].model_copy(update={"id": "second"})
    return base.model_copy(update={"sensors": (base.sensors[0], second)})


def test_scan_is_from_pose_at_same_tick() -> None:
    active_rig = noiseless_rig()
    for state in run(active_rig):
        frame = state.frame
        expected = cast_scan(
            world(),
            frame.true_pose,
            active_rig.sensors[0],
            np.random.default_rng(0),
        )
        assert np.array_equal(frame.scans[0].ranges, expected.ranges)


def test_script_then_stop() -> None:
    frames = [state.frame for state in run(rig())]
    assert [frame.tick for frame in frames] == list(range(MAX_TICKS + 1))
    assert [frame.cmd.v for frame in frames] == [SPEED_M_S] * SCRIPT_TICKS + [0.0] * 4
    distance = SPEED_M_S * SCRIPT_TICKS * TICK_S
    assert math.isclose(frames[-1].true_pose.x, 3.0 + distance)
    assert frames[-1].true_pose == frames[SCRIPT_TICKS].true_pose


def test_first_frame_starts_odometry_at_truth() -> None:
    frame = run(rig())[0].frame
    assert frame.odom_pose == frame.true_pose == Pose2D(3.0, 3.0, 0.0)
    assert frame.collisions == 0


def test_new_sensor_does_not_change_odometry_noise() -> None:
    one = [state.frame.odom_pose for state in run(rig())]
    two = [state.frame.odom_pose for state in run(two_sensor_rig())]
    assert one == two


def test_scan_noise_streams_are_independent() -> None:
    frame = run(two_sensor_rig())[0].frame
    assert not np.array_equal(frame.scans[0].ranges, frame.scans[1].ranges)


def test_start_in_wall_raises_scenario_error() -> None:
    plan = scenario(10.0, 6.0)
    active_rig = rig()
    with pytest.raises(ScenarioError, match="start"):
        first_frame(plan, world(), active_rig, make_rngs(plan.seed, active_rig))


def final_frame(**changes: object) -> Frame:
    return replace(run(noiseless_rig())[-1].frame, **changes)


def test_metrics_pass_when_thresholds_hold() -> None:
    metrics = run_metrics(final_frame(odom_pose=Pose2D(3.075, 3.0, 0.0)), scenario())
    assert metrics.failures == ()
    assert metrics.ticks == MAX_TICKS
    assert math.isclose(metrics.path_length_m, 0.075)
    assert metrics.end_error_m < 1e-9
    assert metrics.odom_error_m < 1e-9


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"collisions": 1}, "collisions"),
        ({"path_length_m": 0.01}, "minPathLengthM"),
        ({"true_pose": Pose2D(4.0, 3.0, 0.0)}, "endWithinM"),
        ({"odom_pose": Pose2D(5.0, 3.0, 0.0)}, "maxOdomErrorM"),
    ],
)
def test_metrics_name_each_missed_threshold(
    changes: dict[str, object], field: str
) -> None:
    failures = run_metrics(final_frame(**changes), scenario()).failures
    assert any(field in failure for failure in failures)
