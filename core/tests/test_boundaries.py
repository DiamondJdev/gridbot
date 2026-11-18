import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import gridbot_core

ROOT = Path(__file__).resolve().parents[2]
BIN = Path(sys.executable).parent


def test_version_is_exposed() -> None:
    assert gridbot_core.__version__ == "0.1.0"


@pytest.mark.parametrize("module", ["random", "time"])
def test_ruff_rejects_import_in_core(module: str) -> None:
    result = subprocess.run(
        [
            BIN / "ruff",
            "check",
            "--stdin-filename",
            "core/src/gridbot_core/example.py",
            "-",
        ],
        input=f"import {module}\n",
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "TID251" in result.stdout


@pytest.mark.parametrize("module", ["rclpy", "socket"])
def test_import_contract_rejects_forbidden_module(tmp_path: Path, module: str) -> None:
    package = tmp_path / "gridbot_core"
    package.mkdir()
    (package / "__init__.py").write_text(f"import {module}\n", encoding="utf-8")
    shutil.copyfile(ROOT / ".importlinter", tmp_path / ".importlinter")
    result = subprocess.run(
        [BIN / "lint-imports"],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert f"-> {module}" in result.stdout
