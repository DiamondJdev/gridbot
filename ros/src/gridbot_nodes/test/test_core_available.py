from gridbot_core import __version__


def test_core_is_importable_inside_ros() -> None:
    assert __version__ == "0.1.0"


def test_core_dependencies_work_inside_ros() -> None:
    import numpy
    from gridbot_core.scenario.loader import load_rig

    assert callable(load_rig)
    assert numpy.__version__.startswith("1.26.")
