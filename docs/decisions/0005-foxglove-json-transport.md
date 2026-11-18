# 0005 · Foxglove JSON transport

## Context

The runner must stream JSON to the gateway without ROS, and test runs need one way for the gateway to send step requests back. A spike tested `foxglove-sdk` 0.31.0 for Python with `@foxglove/ws-protocol` 0.8.0 and `ws` 8.23.0 on Node 24.

## Decision

Use those packages. Keep `foxglove-sdk` below 0.32 and pin `@foxglove/ws-protocol` exactly, because the runner and gateway depend on their wire behavior.

The runner uses these calls:

```python
server = foxglove.start_server(
    name="gridbot-runner",
    host=host,
    port=port,
    capabilities=[Capability.ClientPublish] if test_control else [],
    supported_encodings=["json"],
    server_listener=listener,
)
channel = foxglove.Channel(topic, schema=json_schema)
channel.log(message, log_time=stamp_ns)
```

`ServerListener.on_client_advertise(client, channel)` supplies `channel.id` and `channel.topic`. `on_message_data(client, client_channel_id, data)` receives only the ID, so the listener keeps a map keyed by `(client.id, channel.id)`.

The gateway must create its own socket and offer both subprotocols:

```ts
const ws = new WebSocket(url, [
  "foxglove.sdk.v1",
  FoxgloveClient.SUPPORTED_SUBPROTOCOL,
]);
const client = new FoxgloveClient({ ws });
```

`FoxgloveClient.SUPPORTED_SUBPROTOCOL` is `foxglove.websocket.v1`. The SDK rejects a connection offering only that value with HTTP 400. Phase 5 must confirm that `foxglove_bridge` accepts the second entry.

## Results

| Check                                  | Result                                                           |
| -------------------------------------- | ---------------------------------------------------------------- |
| JSON-schema channels without ROS       | Passed                                                           |
| 20 Hz for 4 seconds in Node            | 80 messages, median gap about 50 ms, 99th percentile 54 to 61 ms |
| 384 KB JSON message once per second    | 4 of 4 received and parsed                                       |
| JSON `null` in a message               | Preserved                                                        |
| Client publish with the capability on  | Server received `{"count": 3}` on `/test/step`                   |
| Client publish with the capability off | Not advertised, and a forced message was refused                 |
| `python:3.12-slim` on arm64            | Installed, imported and started the server                       |

## Consequences

The runner can only accept step requests when it is started with test control. `uv.lock` includes `foxglove-sdk` wheels for Linux arm64 and amd64. The amd64 wheel was not run in the spike.
