"""Shared state types and configuration primitives."""

import math
from dataclasses import dataclass
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

TICK_NS = 50_000_000
"""Simulation tick length in nanoseconds (20 Hz)."""

TICK_S = TICK_NS / 1_000_000_000
"""Simulation tick length in seconds."""

AssetName = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9_-]*$")]
"""A file stem that cannot leave its asset or config folder."""


class ConfigModel(BaseModel):
    """Immutable config that rejects unknown fields and non-finite numbers."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)


@dataclass(frozen=True, slots=True)
class Pose2D:
    """Planar pose: x and y in meters, theta in radians within (-pi, pi]."""

    x: float
    y: float
    theta: float


@dataclass(frozen=True, slots=True)
class Twist2D:
    """Planar velocity: v in meters per second, omega in radians per second."""

    v: float
    omega: float


def normalize_angle(theta: float) -> float:
    """Return an angle in radians wrapped to (-pi, pi]."""
    wrapped = math.remainder(theta, math.tau)
    return math.pi if wrapped <= -math.pi else wrapped
