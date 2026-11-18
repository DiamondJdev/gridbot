"""Sensor rig configuration models."""

from typing import Annotated, Literal, Self

from pydantic import Field, StringConstraints, model_validator

from gridbot_core.types import ConfigModel

SensorId = Annotated[str, StringConstraints(pattern=r"^[a-z0-9_]+$")]
"""A sensor name that is safe to use in a topic such as ``/scan/<id>``."""


class Mount(ConfigModel):
    """Sensor pose on the robot: x and y in meters, yaw in degrees."""

    x: float
    y: float
    yaw_deg: float


class LidarSpec(ConfigModel):
    """A 2D lidar with range noise as a standard deviation in meters."""

    id: SensorId
    type: Literal["lidar"]
    mount: Mount
    fov_deg: float = Field(gt=0, le=360)
    beams: int = Field(gt=0)
    range_m: float = Field(gt=0)
    noise_sigma_m: float = Field(ge=0)


class WheelNoise(ConfigModel):
    """Odometry noise: ``trans`` per meter traveled, ``rot`` per radian turned."""

    trans: float = Field(ge=0)
    rot: float = Field(ge=0)


class Odometry(ConfigModel):
    """Wheel odometry settings."""

    wheel_noise: WheelNoise


class Rig(ConfigModel):
    """The sensors carried by the robot and its odometry settings."""

    sensors: tuple[LidarSpec, ...] = Field(min_length=1)
    odometry: Odometry

    @model_validator(mode="after")
    def sensor_ids_are_unique(self) -> Self:
        """Reject rigs whose sensors would share a topic."""
        seen: set[str] = set()
        for sensor in self.sensors:
            if sensor.id in seen:
                raise ValueError(f"duplicate sensor id: {sensor.id}")
            seen.add(sensor.id)
        return self
