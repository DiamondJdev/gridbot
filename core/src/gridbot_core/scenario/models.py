"""Scenario file models. Field names match the JSON format."""

from typing import Literal, Self

from pydantic import Field, NonNegativeInt, PositiveInt, model_validator

from gridbot_core.types import AssetName, ConfigModel, Pose2D, normalize_angle


class StartPose(ConfigModel):
    """Starting pose: x and y in meters, theta in radians."""

    x: float
    y: float
    theta: float

    def to_pose(self) -> Pose2D:
        """Return the pose with theta wrapped to (-pi, pi]."""
        return Pose2D(self.x, self.y, normalize_angle(self.theta))


class DriveSegment(ConfigModel):
    """A command held for some ticks: v in m/s, omega in rad/s."""

    ticks: PositiveInt
    v: float
    omega: float


class EndZone(ConfigModel):
    """A circle the robot must finish inside, in meters."""

    x: float
    y: float
    radiusM: float = Field(gt=0)


class DriveExpect(ConfigModel):
    """Pass thresholds for a scripted drive."""

    collisions: NonNegativeInt
    minPathLengthM: float = Field(ge=0)
    endWithinM: EndZone
    maxOdomErrorM: float = Field(ge=0)


class Scenario(ConfigModel):
    """A repeatable run. The robot stops after its drive script ends."""

    name: AssetName
    note: str
    map: AssetName
    rig: AssetName
    mode: Literal["drive"]
    seed: NonNegativeInt
    start: StartPose
    drive: tuple[DriveSegment, ...]
    maxTicks: PositiveInt
    expect: DriveExpect

    @model_validator(mode="after")
    def drive_fits_run(self) -> Self:
        """Reject scripts that the run would cut short."""
        total = sum(segment.ticks for segment in self.drive)
        if total > self.maxTicks:
            raise ValueError(f"drive lasts {total} ticks, over maxTicks")
        return self
