"""Load maps stored in the ROS ``map_server`` PNG and YAML format."""

from pathlib import Path
from typing import Annotated, Literal, Self

import numpy as np
from numpy.typing import NDArray
from PIL import Image
from pydantic import Field, StringConstraints, model_validator

from gridbot_core.scenario.loader import ScenarioError, load_yaml_model
from gridbot_core.types import ConfigModel
from gridbot_core.world.grid import GridMap

MAX_GRAY = 255.0


class MapFile(ConfigModel):
    """The supported ``map_server`` YAML fields."""

    image: Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9_-]*\.png$")]
    resolution: float = Field(gt=0)
    origin: tuple[float, float, float]
    negate: Literal[0, 1]
    occupied_thresh: float = Field(gt=0, lt=1)
    free_thresh: float = Field(gt=0, lt=1)

    @model_validator(mode="after")
    def map_is_supported(self) -> Self:
        """Reject rotated maps and thresholds that leave no free range."""
        if self.origin[2] != 0.0:
            raise ValueError("origin yaw must be 0")
        if self.free_thresh >= self.occupied_thresh:
            raise ValueError("free_thresh must be below occupied_thresh")
        return self


def _read_gray(path: Path) -> NDArray[np.uint8]:
    try:
        with Image.open(path) as image:
            return np.asarray(image.convert("L"), dtype=np.uint8)
    except OSError as error:
        raise ScenarioError(f"{path}: cannot read map image: {error}") from error


def load_map(yaml_path: Path) -> GridMap:
    """Load a map. Cells between the two thresholds count as free."""
    config = load_yaml_model(yaml_path, MapFile)
    gray = _read_gray(yaml_path.parent / config.image) / MAX_GRAY
    occupancy = gray if config.negate else 1.0 - gray
    # PNG rows run north to south, while grid rows grow with world y.
    occupied = np.flipud(occupancy > config.occupied_thresh).copy()
    occupied.setflags(write=False)
    return GridMap(config.resolution, config.origin[0], config.origin[1], occupied)
