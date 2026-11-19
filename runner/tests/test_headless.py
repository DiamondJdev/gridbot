import json
import math
import signal
from pathlib import Path

import pytest
from gridbot_runner.cli import _stop, main  # pyright: ignore[reportPrivateUsage]

ROOT = Path(__file__).resolve().parents[2]
DRIVE_01 = ROOT / "scenarios/drive-01.json"
MAX_STEP_M = 0.05
DRIVE_01_TICKS = 1128


def scenario_copy(tmp_path: Path, **changes: object) -> Path:
    """Write a modified drive-01 into a temporary repo with the real assets."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "assets").symlink_to(ROOT / "assets")
    (tmp_path / "config").symlink_to(ROOT / "config")
    (tmp_path / "scenarios").mkdir()
    data = json.loads(DRIVE_01.read_text(encoding="utf-8")) | changes
    path = tmp_path / "scenarios/sample.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def drive_01_trace(tmp_path_factory: pytest.TempPathFactory) -> Path:
    trace = tmp_path_factory.mktemp("trace") / "drive-01.jsonl"
    assert main([str(DRIVE_01), "--trace", str(trace)]) == 0
    return trace


def trace_lines(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def pose_xy(line: dict[str, object]) -> tuple[float, float]:
    pose = line["truePose"]
    assert isinstance(pose, dict)
    return float(pose["x"]), float(pose["y"])  # pyright: ignore[reportUnknownArgumentType]


def test_drive_01_passes(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(DRIVE_01), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["scenario"] == "drive-01"
    assert report["passed"] is True
    assert report["failures"] == []
    assert report["ticks"] == DRIVE_01_TICKS
    assert report["collisions"] == 0
    assert report["pathLengthM"] >= 39.9
    assert report["endErrorM"] <= 0.05
    assert 0.0 < report["odomErrorM"] <= 1.0
    assert set(report["endPose"]) == {"x", "y", "theta"}


def test_text_output_names_result(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(DRIVE_01)]) == 0
    assert capsys.readouterr().out.startswith("drive-01: passed")


def test_same_seed_gives_identical_trace_bytes(
    tmp_path: Path, drive_01_trace: Path
) -> None:
    first, second = drive_01_trace, tmp_path / "second.jsonl"
    assert main([str(DRIVE_01), "--trace", str(second)]) == 0
    assert first.read_bytes() == second.read_bytes()
    assert len(trace_lines(first)) == DRIVE_01_TICKS + 1


def test_other_seed_changes_odometry_not_truth(
    tmp_path: Path, drive_01_trace: Path
) -> None:
    base, other = drive_01_trace, tmp_path / "other.jsonl"
    seeded = scenario_copy(tmp_path / "repo", seed=7)
    assert main([str(seeded), "--trace", str(other)]) == 0
    base_lines, other_lines = trace_lines(base), trace_lines(other)
    assert [line["truePose"] for line in base_lines] == [
        line["truePose"] for line in other_lines
    ]
    assert base_lines[-1]["odomPose"] != other_lines[-1]["odomPose"]


def test_pose_step_never_exceeds_max_speed(drive_01_trace: Path) -> None:
    poses = [pose_xy(line) for line in trace_lines(drive_01_trace)]
    steps = [math.dist(a, b) for a, b in zip(poses, poses[1:], strict=False)]
    assert max(steps) <= MAX_STEP_M + 1e-9


def test_missed_threshold_exits_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    expect = json.loads(DRIVE_01.read_text(encoding="utf-8"))["expect"]
    far = expect | {"endWithinM": {"x": 10.0, "y": 10.0, "radiusM": 0.05}}
    path = scenario_copy(tmp_path, expect=far)
    assert main([str(path), "--json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["passed"] is False
    assert any("endWithinM" in failure for failure in report["failures"])


def test_bad_file_exits_2_with_field(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = scenario_copy(tmp_path, events=[])
    assert main([str(path), "--json"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert str(path) in captured.err
    assert "events" in captured.err


def test_missing_map_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = scenario_copy(tmp_path, map="absent")
    assert main([str(path)]) == 2
    assert "absent.yaml" in capsys.readouterr().err


def test_start_in_wall_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = scenario_copy(tmp_path, start={"x": 10.0, "y": 6.0, "theta": 0.0})
    assert main([str(path)]) == 2
    assert "start" in capsys.readouterr().err


def test_unwritable_trace_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    trace = tmp_path / "missing-dir/trace.jsonl"
    assert main([str(DRIVE_01), "--trace", str(trace)]) == 2
    assert "trace.jsonl" in capsys.readouterr().err


def test_stop_ignores_a_second_sigterm() -> None:
    previous = signal.getsignal(signal.SIGTERM)
    try:
        with pytest.raises(SystemExit):
            _stop(signal.SIGTERM, None)
        assert signal.getsignal(signal.SIGTERM) == signal.SIG_IGN
    finally:
        signal.signal(signal.SIGTERM, previous)
