import json
import math
from pathlib import Path

import pytest

from gridbot_core.scenario.loader import ScenarioError, load_rig, load_scenario
from gridbot_core.types import TICK_NS, TICK_S, Pose2D, normalize_angle

ROOT = Path(__file__).resolve().parents[2]


def scenario_data() -> dict[str, object]:
    return {
        "name": "sample",
        "note": "A short scripted drive.",
        "map": "warehouse-01",
        "rig": "lidar-360",
        "mode": "drive",
        "seed": 42,
        "start": {"x": 3.0, "y": 3.0, "theta": 0.0},
        "drive": [{"ticks": 10, "v": 0.5, "omega": 0.0}],
        "maxTicks": 20,
        "expect": {
            "collisions": 0,
            "minPathLengthM": 0.2,
            "endWithinM": {"x": 3.25, "y": 3.0, "radiusM": 0.05},
            "maxOdomErrorM": 1.0,
        },
    }


def write_scenario(tmp_path: Path, data: dict[str, object]) -> Path:
    path = tmp_path / "sample.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_tick_constants_agree() -> None:
    assert TICK_NS == 50_000_000
    assert TICK_S == TICK_NS / 1e9


def test_normalize_angle_uses_half_open_range() -> None:
    assert normalize_angle(-math.pi) == math.pi
    assert math.isclose(normalize_angle(3 * math.pi / 2), -math.pi / 2)


def test_rig_loads_lidar_360() -> None:
    rig = load_rig(ROOT / "config/rigs/lidar-360.yaml")
    lidar = rig.sensors[0]
    assert len(rig.sensors) == 1
    assert (lidar.id, lidar.type) == ("lidar", "lidar")
    assert (lidar.mount.x, lidar.mount.y, lidar.mount.yaw_deg) == (0.10, 0.0, 0.0)
    assert (lidar.fov_deg, lidar.beams, lidar.range_m) == (360.0, 360, 10.0)
    assert lidar.noise_sigma_m == 0.02
    assert rig.odometry.wheel_noise.trans == 0.02
    assert rig.odometry.wheel_noise.rot == 0.05


def test_scenario_start_converts_to_normalized_pose(tmp_path: Path) -> None:
    data = scenario_data() | {"start": {"x": 1.0, "y": 2.0, "theta": 3 * math.pi}}
    start = load_scenario(write_scenario(tmp_path, data)).start.to_pose()
    assert start == Pose2D(1.0, 2.0, math.pi)


def test_unknown_field_names_field(tmp_path: Path) -> None:
    path = write_scenario(tmp_path, scenario_data() | {"events": "none"})
    with pytest.raises(ScenarioError) as error:
        load_scenario(path)
    assert str(path) in str(error.value)
    assert "events" in str(error.value)


def test_unknown_rig_field_names_field(tmp_path: Path) -> None:
    source = (ROOT / "config/rigs/lidar-360.yaml").read_text(encoding="utf-8")
    path = tmp_path / "rig.yaml"
    path.write_text(source + "gyro: { bias_deg_s: 0.1 }\n", encoding="utf-8")
    with pytest.raises(ScenarioError) as error:
        load_rig(path)
    assert str(path) in str(error.value)
    assert "gyro" in str(error.value)


def test_invalid_json_names_file(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(ScenarioError, match="broken.json"):
        load_scenario(path)


def test_invalid_yaml_names_file(tmp_path: Path) -> None:
    path = tmp_path / "broken.yaml"
    path.write_text("sensors: [", encoding="utf-8")
    with pytest.raises(ScenarioError, match="broken.yaml"):
        load_rig(path)


def test_missing_file_names_file(tmp_path: Path) -> None:
    with pytest.raises(ScenarioError, match="absent.json"):
        load_scenario(tmp_path / "absent.json")


def test_drive_shorter_than_max_ticks_is_allowed(tmp_path: Path) -> None:
    scenario = load_scenario(write_scenario(tmp_path, scenario_data()))
    assert sum(segment.ticks for segment in scenario.drive) < scenario.maxTicks


def test_drive_longer_than_max_ticks_is_rejected(tmp_path: Path) -> None:
    path = write_scenario(tmp_path, scenario_data() | {"maxTicks": 9})
    with pytest.raises(ScenarioError, match="maxTicks"):
        load_scenario(path)


@pytest.mark.parametrize("field", ["map", "rig"])
def test_asset_names_cannot_leave_their_folder(tmp_path: Path, field: str) -> None:
    path = write_scenario(tmp_path, scenario_data() | {field: "../secret"})
    with pytest.raises(ScenarioError, match=field):
        load_scenario(path)


def test_non_finite_number_is_rejected(tmp_path: Path) -> None:
    data = scenario_data() | {"start": {"x": float("nan"), "y": 0.0, "theta": 0.0}}
    with pytest.raises(ScenarioError, match="start"):
        load_scenario(write_scenario(tmp_path, data))


def test_duplicate_sensor_ids_are_rejected(tmp_path: Path) -> None:
    sensor = (
        "  - { id: lidar, type: lidar, mount: { x: 0, y: 0, yaw_deg: 0 }, "
        "fov_deg: 360, beams: 4, range_m: 5, noise_sigma_m: 0 }\n"
    )
    path = tmp_path / "rig.yaml"
    path.write_text(
        "sensors:\n" + sensor * 2 + "odometry: { wheel_noise: { trans: 0, rot: 0 } }\n",
        encoding="utf-8",
    )
    with pytest.raises(ScenarioError, match="duplicate sensor id"):
        load_rig(path)
