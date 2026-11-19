"""Run a scenario as fast as possible and report its metrics."""

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from gridbot_core.metrics.run import RunMetrics, run_metrics
from gridbot_core.scenario.loader import load_rig, load_scenario
from gridbot_core.scenario.models import Scenario
from gridbot_core.sensors.rig import Rig
from gridbot_core.sim.world_step import Frame, first_frame, make_rngs, next_frame
from gridbot_core.types import Pose2D
from gridbot_core.world.grid import GridMap
from gridbot_core.world.loader import load_map


@dataclass(frozen=True, eq=False)
class LoadedRun:
    """A scenario with the map and rig it names."""

    scenario: Scenario
    world: GridMap
    rig: Rig


@dataclass(frozen=True, eq=False)
class HeadlessResult:
    """The last frame of a run and its score."""

    final: Frame
    metrics: RunMetrics


def load_run(path: Path) -> LoadedRun:
    """Load a scenario from ``<repo>/scenarios`` with its map and rig."""
    scenario = load_scenario(path)
    root = path.resolve().parents[1]
    world = load_map(root / "assets" / f"{scenario.map}.yaml")
    rig = load_rig(root / "config" / "rigs" / f"{scenario.rig}.yaml")
    return LoadedRun(scenario, world, rig)


def pose_json(pose: Pose2D) -> dict[str, float]:
    """Return a pose with ROS-style field names."""
    return {"x": pose.x, "y": pose.y, "theta": pose.theta}


def trace_line(frame: Frame) -> str:
    """Return one deterministic JSON line describing a tick."""
    true_pose, odom = frame.true_pose, frame.odom_pose
    line = {
        "tick": frame.tick,
        "truePose": pose_json(true_pose),
        "odomPose": pose_json(odom),
        "odomErrorM": math.hypot(true_pose.x - odom.x, true_pose.y - odom.y),
        "cmd": {"v": frame.cmd.v, "omega": frame.cmd.omega},
        "collisions": frame.collisions,
        "pathLengthM": frame.path_length_m,
    }
    return json.dumps(line, sort_keys=True, allow_nan=False)


def run_headless(run: LoadedRun, trace: TextIO | None = None) -> HeadlessResult:
    """Step every tick of a scenario, optionally writing a JSON Lines trace."""
    scenario = run.scenario
    rngs = make_rngs(scenario.seed, run.rig)
    state = first_frame(scenario, run.world, run.rig, rngs)
    while True:
        if trace is not None:
            trace.write(trace_line(state.frame) + "\n")
        if state.frame.tick >= scenario.maxTicks:
            break
        state = next_frame(state, scenario, run.world, run.rig, rngs)
    return HeadlessResult(state.frame, run_metrics(state.frame, scenario))


def report(scenario: Scenario, result: HeadlessResult) -> dict[str, object]:
    """Return the ``--json`` report."""
    metrics = result.metrics
    return {
        "scenario": scenario.name,
        "passed": not metrics.failures,
        "ticks": metrics.ticks,
        "collisions": metrics.collisions,
        "pathLengthM": metrics.path_length_m,
        "endErrorM": metrics.end_error_m,
        "odomErrorM": metrics.odom_error_m,
        "endPose": pose_json(result.final.true_pose),
        "failures": list(metrics.failures),
    }
