"""Score a completed scripted drive against its thresholds."""

import math
from dataclasses import dataclass

from gridbot_core.scenario.models import Scenario
from gridbot_core.sim.world_step import Frame


@dataclass(frozen=True, slots=True)
class RunMetrics:
    """Run results in meters, with one message per missed threshold."""

    ticks: int
    collisions: int
    path_length_m: float
    end_error_m: float
    odom_error_m: float
    failures: tuple[str, ...]


def run_metrics(final: Frame, scenario: Scenario) -> RunMetrics:
    """Compare a run's final frame with the scenario's thresholds."""
    expect = scenario.expect
    zone = expect.endWithinM
    pose = final.true_pose
    end_error = math.hypot(pose.x - zone.x, pose.y - zone.y)
    odom_error = math.hypot(pose.x - final.odom_pose.x, pose.y - final.odom_pose.y)
    checks = (
        (final.collisions > expect.collisions, f"collisions: {final.collisions}"),
        (
            final.path_length_m < expect.minPathLengthM,
            f"minPathLengthM: {final.path_length_m:.3f}",
        ),
        (end_error > zone.radiusM, f"endWithinM: {end_error:.3f}"),
        (odom_error > expect.maxOdomErrorM, f"maxOdomErrorM: {odom_error:.3f}"),
    )
    return RunMetrics(
        final.tick,
        final.collisions,
        final.path_length_m,
        end_error,
        odom_error,
        tuple(message for failed, message in checks if failed),
    )
