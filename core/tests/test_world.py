import math
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from gridbot_core.scenario.loader import ScenarioError
from gridbot_core.world.grid import GridMap, cell_center, world_to_cell
from gridbot_core.world.loader import load_map

ROOT = Path(__file__).resolve().parents[2]
BLACK = 0
WHITE = 255


def write_map(tmp_path: Path, *, negate: int = 0, yaw: float = 0.0) -> Path:
    pixels = np.array(
        [[BLACK, WHITE, WHITE], [WHITE, WHITE, WHITE]],
        dtype=np.uint8,
    )
    Image.fromarray(pixels).save(tmp_path / "sample.png")
    path = tmp_path / "sample.yaml"
    path.write_text(
        "image: sample.png\n"
        "resolution: 1.0\n"
        f"origin: [10.0, 20.0, {yaw}]\n"
        f"negate: {negate}\n"
        "occupied_thresh: 0.65\n"
        "free_thresh: 0.196\n",
        encoding="utf-8",
    )
    return path


def test_png_top_row_becomes_north(tmp_path: Path) -> None:
    world = load_map(write_map(tmp_path))
    assert world.occupied.shape == (2, 3)
    assert world.occupied[1, 0]
    assert int(world.occupied.sum()) == 1
    assert cell_center(world, 1, 0) == (10.5, 21.5)
    assert world_to_cell(world, 10.5, 21.5) == (1, 0)


def test_negate_inverts_occupancy(tmp_path: Path) -> None:
    world = load_map(write_map(tmp_path, negate=1))
    assert not world.occupied[1, 0]
    assert int(world.occupied.sum()) == 5


@pytest.mark.parametrize(
    ("x", "y"),
    [(9.99, 20.0), (10.0, 19.99), (13.0, 20.0), (10.0, 22.0)],
)
def test_outside_map_has_no_cell(tmp_path: Path, x: float, y: float) -> None:
    assert world_to_cell(load_map(write_map(tmp_path)), x, y) is None


def test_nonzero_origin_yaw_is_rejected(tmp_path: Path) -> None:
    path = write_map(tmp_path, yaw=0.5)
    with pytest.raises(ScenarioError, match="origin"):
        load_map(path)


def test_image_cannot_leave_map_folder(tmp_path: Path) -> None:
    path = write_map(tmp_path)
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("sample.png", "../sample.png"), encoding="utf-8")
    with pytest.raises(ScenarioError, match="image"):
        load_map(path)


def test_missing_image_names_file(tmp_path: Path) -> None:
    path = write_map(tmp_path)
    (tmp_path / "sample.png").unlink()
    with pytest.raises(ScenarioError, match="sample.png"):
        load_map(path)


def test_corrupt_image_names_file(tmp_path: Path) -> None:
    path = write_map(tmp_path)
    (tmp_path / "sample.png").write_bytes(b"not a png")
    with pytest.raises(ScenarioError, match="sample.png"):
        load_map(path)


def test_occupied_array_is_read_only(tmp_path: Path) -> None:
    world = load_map(write_map(tmp_path))
    with pytest.raises(ValueError, match="read-only"):
        world.occupied[0, 0] = True


def disk_is_free(world: GridMap, x: float, y: float, radius_m: float) -> bool:
    for angle in np.linspace(0.0, math.tau, 24, endpoint=False):
        cell = world_to_cell(
            world,
            x + radius_m * math.cos(float(angle)),
            y + radius_m * math.sin(float(angle)),
        )
        if cell is None or world.occupied[cell]:
            return False
    return True


def test_warehouse_has_expected_size_and_clear_loop() -> None:
    world = load_map(ROOT / "assets/warehouse-01.yaml")
    assert world.occupied.shape == (240, 400)
    assert world.resolution_m == 0.05
    assert bool(world.occupied[0, :].all() and world.occupied[-1, :].all())
    assert bool(world.occupied[:, 0].all() and world.occupied[:, -1].all())
    shelf = world_to_cell(world, 10.0, 6.0)
    assert shelf is not None
    assert world.occupied[shelf]
    corners = [(3.0, 3.0), (17.0, 3.0), (17.0, 9.0), (3.0, 9.0), (3.0, 3.0)]
    for (x0, y0), (x1, y1) in zip(corners, corners[1:], strict=False):
        for share in np.linspace(0.0, 1.0, 100):
            x = x0 + (x1 - x0) * float(share)
            y = y0 + (y1 - y0) * float(share)
            assert disk_is_free(world, x, y, 0.25), (x, y)
