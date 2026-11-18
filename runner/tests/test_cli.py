import pytest
from gridbot_runner.cli import main


def test_version_flag_prints_core_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == "gridbot-run 0.1.0"
