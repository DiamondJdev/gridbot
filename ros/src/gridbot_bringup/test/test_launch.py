import runpy
from pathlib import Path

from ament_index_python.packages import get_package_share_path
from launch import LaunchDescription


def test_launch_description_loads() -> None:
    share: Path = get_package_share_path("gridbot_bringup")
    module = runpy.run_path(str(share / "launch/gridbot.launch.py"))
    assert isinstance(module["generate_launch_description"](), LaunchDescription)
