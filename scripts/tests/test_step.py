import shutil
import subprocess
from pathlib import Path

STEP = Path(__file__).resolve().parents[1] / "step.sh"


def run_step(
    root: Path, label: str, *command: str, script: Path = STEP
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", script, label, *command], cwd=root, capture_output=True, text=True
    )


def test_success_prints_summary(tmp_path: Path) -> None:
    result = run_step(tmp_path, "unit", "true")
    assert result.returncode == 0
    assert result.stdout == "unit: passed\n"


def test_failure_prints_log_tail_and_exit_code(tmp_path: Path) -> None:
    result = run_step(tmp_path, "unit", "bash", "-c", "echo boom; exit 3")
    assert result.returncode == 3
    assert "boom" in result.stdout
    assert "unit: FAILED (exit 3)" in result.stdout


def test_works_from_a_path_with_spaces(tmp_path: Path) -> None:
    folder = tmp_path / "dir with spaces"
    folder.mkdir()
    script = folder / "step.sh"
    shutil.copyfile(STEP, script)
    result = run_step(folder, "unit", "printf", "%s", "arg with spaces", script=script)
    assert result.returncode == 0
    assert (folder / "artifacts/logs/unit.log").read_text() == "arg with spaces"


def test_log_name_is_safe_for_labels_with_spaces_and_parens(tmp_path: Path) -> None:
    result = run_step(tmp_path, "scenarios (runner)", "true")
    assert result.returncode == 0
    assert (tmp_path / "artifacts/logs/scenarios-runner.log").exists()
