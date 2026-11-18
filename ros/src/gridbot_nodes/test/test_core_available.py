from gridbot_core import __version__


def test_core_is_importable_inside_ros() -> None:
    assert __version__ == "0.1.0"
