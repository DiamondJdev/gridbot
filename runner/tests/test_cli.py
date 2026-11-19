import pytest
from gridbot_runner import cli
from gridbot_runner.cli import main
from gridbot_runner.headless import LoadedRun


def test_version_flag_prints_core_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == "gridbot-run 0.1.0"


@pytest.mark.parametrize(
    "args",
    [
        ["scenarios/drive-01.json", "--serve", "--port", "0"],
        ["scenarios/drive-01.json", "--serve", "--port", "65536"],
        ["scenarios/drive-01.json", "--test-control"],
        ["scenarios/drive-01.json", "--serve", "--trace", "out.jsonl"],
    ],
)
def test_invalid_serve_options_exit_2(args: list[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(args)
    assert exit_info.value.code == 2


def test_serve_passes_options(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, int, bool]] = []

    def fake_serve(run: LoadedRun, host: str, port: int, test_control: bool) -> None:
        calls.append((run.scenario.name, host, port, test_control))

    monkeypatch.setattr(cli, "serve", fake_serve)
    args = ["scenarios/drive-01.json", "--serve", "--test-control", "--port", "18765"]
    assert main(args) == 0
    assert calls == [("drive-01", "127.0.0.1", 18765, True)]
