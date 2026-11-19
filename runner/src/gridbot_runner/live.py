"""Serve a scenario over the Foxglove WebSocket protocol at 20 Hz."""

import json
import logging
import threading
import time
from collections.abc import Callable
from typing import cast

import foxglove
from foxglove.websocket import Capability, Client, ClientChannel, ServerListener
from gridbot_core.sim.world_step import first_frame, make_rngs, next_frame
from gridbot_core.types import TICK_NS, TICK_S

from gridbot_runner.headless import LoadedRun
from gridbot_runner.messages import Message, frame_messages, topics

LOG = logging.getLogger(__name__)
STEP_TOPIC = "/test/step"
MAX_STEP_COUNT = 1000
SERVER_NAME = "gridbot-runner"

Publish = Callable[[str, Message, int], None]
WaitTurn = Callable[[], bool]


def server_capabilities(test_control: bool) -> list[Capability]:
    """Allow client publishing only when test control is on."""
    return [Capability.ClientPublish] if test_control else []


def parse_step(data: bytes) -> int | None:
    """Return the count from ``{"count": n}``, or None for any other payload."""
    try:
        message = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(message, dict):
        return None
    fields = cast(dict[str, object], message)
    count = fields.get("count")
    if set(fields) != {"count"} or not isinstance(count, int):
        return None
    if isinstance(count, bool) or not 1 <= count <= MAX_STEP_COUNT:
        return None
    return count


class StepGate:
    """Lets one frame publish per queued test step."""

    def __init__(self) -> None:
        self._pending = 0
        self._closed = False
        self._changed = threading.Condition()

    def add(self, count: int) -> None:
        """Queue more frames."""
        with self._changed:
            self._pending += count
            self._changed.notify_all()

    def close(self) -> None:
        """Release a waiting loop so it can stop."""
        with self._changed:
            self._closed = True
            self._changed.notify_all()

    def wait_turn(self) -> bool:
        """Block until a step is queued. Return False after ``close``."""
        with self._changed:
            self._changed.wait_for(lambda: self._pending > 0 or self._closed)
            if self._closed:
                return False
            self._pending -= 1
            return True


class ClockPacer:
    """Paces frames with absolute deadlines and skips ahead after overruns."""

    def __init__(
        self,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._clock = clock
        self._sleep = sleep
        self._deadline: float | None = None
        self.overruns = 0

    def wait_turn(self) -> bool:
        """Sleep until the next 50 ms deadline."""
        now = self._clock()
        if self._deadline is None or now >= self._deadline + TICK_S:
            if self._deadline is not None:
                self.overruns += 1
                LOG.warning("tick overran by %.3f s", now - self._deadline)
            self._deadline = now + TICK_S
            return True
        if now < self._deadline:
            self._sleep(self._deadline - now)
        self._deadline += TICK_S
        return True


def run_live(
    run: LoadedRun, publish: Publish, wait_turn: WaitTurn, frames: int | None = None
) -> int:
    """Publish frames, restarting the scenario after its last tick."""
    scenario = run.scenario
    published = 0
    while True:
        rngs = make_rngs(scenario.seed, run.rig)
        state = first_frame(scenario, run.world, run.rig, rngs)
        while True:
            if frames is not None and published >= frames:
                return published
            if not wait_turn():
                return published
            for topic, message in frame_messages(state.frame, run.world, run.rig):
                publish(topic, message, state.frame.tick * TICK_NS)
            published += 1
            if state.frame.tick >= scenario.maxTicks:
                break
            state = next_frame(state, scenario, run.world, run.rig, rngs)


class _StepListener(ServerListener):
    """Queues steps sent on the test channel."""

    def __init__(self, gate: StepGate) -> None:
        self._gate = gate
        self._topics: dict[tuple[int, int], str] = {}

    def on_client_advertise(self, client: Client, channel: ClientChannel) -> None:
        self._topics[(client.id, channel.id)] = channel.topic

    def on_message_data(
        self, client: Client, client_channel_id: int, data: bytes
    ) -> None:
        topic = self._topics.get((client.id, client_channel_id))
        count = parse_step(data) if topic == STEP_TOPIC else None
        if count is None:
            LOG.warning("ignored client message on %s", topic)
            return
        self._gate.add(count)


def serve(run: LoadedRun, host: str, port: int, test_control: bool) -> None:
    """Serve until interrupted. Test control waits for step requests."""
    gate = StepGate()
    server = foxglove.start_server(
        name=SERVER_NAME,
        host=host,
        port=port,
        capabilities=server_capabilities(test_control),
        supported_encodings=["json"],
        server_listener=_StepListener(gate) if test_control else None,
    )
    # Advertise everything before tick 0 so clients can subscribe first.
    channels = {
        topic: foxglove.Channel(topic, schema={"type": "object"})
        for topic in topics(run.rig)
    }

    def publish(topic: str, message: Message, stamp_ns: int) -> None:
        channels[topic].log(message, log_time=stamp_ns)

    LOG.info("serving %s on %s:%d", run.scenario.name, host, port)
    try:
        run_live(
            run, publish, gate.wait_turn if test_control else ClockPacer().wait_turn
        )
    finally:
        server.stop()
