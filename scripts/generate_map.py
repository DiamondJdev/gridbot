"""Generate the warehouse-01 occupancy map files."""

from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image

RESOLUTION_M = 0.05
WIDTH_M = 20.0
HEIGHT_M = 12.0
WALL_M = 0.2
SHELVES_M = ((6.0, 14.0, 1.0, 1.6), (6.0, 14.0, 5.0, 7.0), (6.0, 14.0, 10.5, 11.2))
OCCUPIED_GRAY = 0
FREE_GRAY = 255
MAP_YAML = """image: warehouse-01.png
resolution: 0.05
origin: [0.0, 0.0, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
"""


def cells(meters: float) -> int:
    """Convert a distance in meters to a whole number of cells."""
    return round(meters / RESOLUTION_M)


def build_grid() -> NDArray[np.bool_]:
    """Return occupancy with row 0 at the southern edge."""
    # This fresh array is filled in place before it is returned.
    grid = np.zeros((cells(HEIGHT_M), cells(WIDTH_M)), dtype=np.bool_)
    wall = cells(WALL_M)
    grid[:wall, :] = grid[-wall:, :] = True
    grid[:, :wall] = grid[:, -wall:] = True
    for x_min, x_max, y_min, y_max in SHELVES_M:
        grid[cells(y_min) : cells(y_max), cells(x_min) : cells(x_max)] = True
    return grid


def main() -> None:
    """Write the PNG and YAML files into ``assets``."""
    assets = Path(__file__).resolve().parents[1] / "assets"
    pixels = np.where(np.flipud(build_grid()), OCCUPIED_GRAY, FREE_GRAY)
    Image.fromarray(pixels.astype(np.uint8)).save(
        assets / "warehouse-01.png", optimize=True
    )
    (assets / "warehouse-01.yaml").write_text(MAP_YAML, encoding="utf-8")


if __name__ == "__main__":
    main()
