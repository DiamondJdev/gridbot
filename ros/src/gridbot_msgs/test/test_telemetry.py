from gridbot_msgs.msg import Telemetry


def test_telemetry_fields() -> None:
    msg = Telemetry(source="planner", keys=["nodes"], values=[3.0])
    assert (msg.source, list(msg.keys), list(msg.values)) == (
        "planner",
        ["nodes"],
        [3.0],
    )
