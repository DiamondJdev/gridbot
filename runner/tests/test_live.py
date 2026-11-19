import threading
from dataclasses import replace
from pathlib import Path

import pytest
from foxglove.websocket import Capability
from gridbot_runner.headless import LoadedRun, load_run
from gridbot_runner.live import (
    ClockPacer,
    StepGate,
    parse_step,
    run_live,
    server_capabilities,
)

ROOT = Path(__file__).resolve().parents[2]
JOIN_TIMEOUT_S = 5.0


def short_run(max_ticks: int = 2) -> LoadedRun:
    run = load_run(ROOT / "scenarios/drive-01.json")
    scenario = run.scenario.model_copy(update={"maxTicks": max_ticks, "drive": ()})
    return replace(run, scenario=scenario)


class Recorder:
    def __init__(self) -> None:
        self.ticks: list[float] = []
        self.lock = threading.Lock()
        self.published = threading.Condition(self.lock)

    def publish(self, topic: str, message: dict[str, object], stamp_ns: int) -> None:
        if topic == "/telemetry":
            values = message["values"]
            assert isinstance(values, list)
            with self.published:
                self.ticks.append(float(values[0]))  # pyright: ignore[reportUnknownArgumentType]
                self.published.notify_all()

    def wait_for(self, count: int) -> None:
        with self.published:
            assert self.published.wait_for(
                lambda: len(self.ticks) >= count, JOIN_TIMEOUT_S
            )


def test_step_channel_absent_without_test_control() -> None:
    assert server_capabilities(test_control=False) == []
    assert server_capabilities(test_control=True) == [Capability.ClientPublish]


@pytest.mark.parametrize(
    ("data", "count"),
    [
        (b'{"count": 1}', 1),
        (b'{"count": 1000}', 1000),
        (b'{"count": 0}', None),
        (b'{"count": 1001}', None),
        (b'{"count": true}', None),
        (b'{"count": 2.5}', None),
        (b'{"count": 2, "extra": 1}', None),
        (b"[]", None),
        (b"not json", None),
        (b"\xff", None),
    ],
)
def test_parse_step_accepts_only_bounded_integer_counts(
    data: bytes, count: int | None
) -> None:
    assert parse_step(data) == count


def test_test_mode_waits_for_step() -> None:
    gate = StepGate()
    recorder = Recorder()
    worker = threading.Thread(
        target=run_live,
        args=(short_run(), recorder.publish, gate.wait_turn),
        kwargs={"frames": 3},
    )
    worker.start()
    with recorder.published:
        assert not recorder.published.wait_for(lambda: recorder.ticks, 0.2)
    gate.add(1)
    recorder.wait_for(1)
    assert recorder.ticks == [0.0]
    gate.add(2)
    worker.join(JOIN_TIMEOUT_S)
    assert not worker.is_alive()
    assert recorder.ticks == [0.0, 1.0, 2.0]


def test_closing_gate_stops_the_loop() -> None:
    gate = StepGate()
    worker = threading.Thread(
        target=run_live, args=(short_run(), Recorder().publish, gate.wait_turn)
    )
    worker.start()
    gate.close()
    worker.join(JOIN_TIMEOUT_S)
    assert not worker.is_alive()


def test_live_run_restarts_after_last_tick() -> None:
    recorder = Recorder()
    run_live(short_run(2), recorder.publish, lambda: True, frames=7)
    assert recorder.ticks == [0.0, 1.0, 2.0, 0.0, 1.0, 2.0, 0.0]


def test_pacer_uses_absolute_deadlines() -> None:
    now = [10.0]
    sleeps: list[float] = []

    def sleep(seconds: float) -> None:
        sleeps.append(round(seconds, 6))
        now[0] += seconds

    pacer = ClockPacer(clock=lambda: now[0], sleep=sleep)
    assert pacer.wait_turn()
    now[0] += 0.01
    assert pacer.wait_turn()
    assert sleeps == [0.04]
    now[0] += 0.2
    assert pacer.wait_turn()
    assert pacer.overruns == 1
    assert sleeps == [0.04]
    assert pacer.wait_turn()
    assert sleeps == [0.04, 0.05]
