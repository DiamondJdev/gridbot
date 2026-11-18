"""Occupancy grid type and coordinate conversion."""

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, eq=False)
class GridMap:
    """A read-only occupancy grid in meters. Row 0 is the southern edge."""

    resolution_m: float
    origin_x_m: float
    origin_y_m: float
    occupied: NDArray[np.bool_]


def world_to_cell(world: GridMap, x: float, y: float) -> tuple[int, int] | None:
    """Return the ``(row, col)`` containing a point in meters, if on the map."""
    col = math.floor((x - world.origin_x_m) / world.resolution_m)
    row = math.floor((y - world.origin_y_m) / world.resolution_m)
    rows, cols = world.occupied.shape
    return (row, col) if 0 <= row < rows and 0 <= col < cols else None


def cell_center(world: GridMap, row: int, col: int) -> tuple[float, float]:
    """Return the world ``(x, y)`` of a cell center in meters."""
    return (
        world.origin_x_m + (col + 0.5) * world.resolution_m,
        world.origin_y_m + (row + 0.5) * world.resolution_m,
    )
