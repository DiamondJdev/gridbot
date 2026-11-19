import { describe, expect, it } from "vitest";
import { isAllowedTopic, parseTestCommand } from "../src/protocol.js";
import { Relay, type Viewer } from "../src/relay.js";

const MAX_BUFFERED = 1024;
const WORLD = JSON.stringify({ info: { width: 2 }, data: [0, 100] });
const TF_STATIC = JSON.stringify({ transforms: [] });
const TELEMETRY = JSON.stringify({
  stamp: { sec: 1, nanosec: 50_000_000 },
  source: "sim",
  keys: ["tick"],
  values: [21],
});

class FakeViewer implements Viewer {
  sent: unknown[] = [];
  bufferedAmount = 0;
  send(data: string): void {
    this.sent.push(JSON.parse(data));
  }
  topics(): string[] {
    return this.sent.flatMap((message) =>
      (message as { type: string }).type === "message"
        ? [(message as { topic: string }).topic]
        : [],
    );
  }
}

function connectedRelay(testControl = false): Relay {
  const relay = new Relay({ testControl, maxBufferedBytes: MAX_BUFFERED });
  relay.setRuntimeConnected(true);
  return relay;
}

describe("topic allowlist", () => {
  it.each(["/scan/lidar", "/sim/world", "/tf_static", "/telemetry"])(
    "allows %s",
    (topic) => expect(isAllowedTopic(topic)).toBe(true),
  );
  it.each([
    "/test/step",
    "/scan",
    "/scanner",
    "/scan/",
    "/rosout",
    "/scan/a/b",
  ])("blocks %s", (topic) => expect(isAllowedTopic(topic)).toBe(false));
});

describe("Relay", () => {
  it("forwards only allowlisted topics", () => {
    const relay = connectedRelay();
    const viewer = new FakeViewer();
    relay.addViewer(viewer);
    relay.receive("/test/step", '{"count":1}');
    relay.receive("/telemetry", TELEMETRY);
    expect(viewer.topics()).toEqual(["/telemetry"]);
    expect(viewer.sent.at(-1)).toEqual({
      type: "message",
      topic: "/telemetry",
      message: JSON.parse(TELEMETRY),
    });
  });

  it("drops payloads that are not JSON objects", () => {
    const relay = connectedRelay();
    const viewer = new FakeViewer();
    relay.addViewer(viewer);
    relay.receive("/odom", "{");
    relay.receive("/odom", "[1]");
    expect(viewer.topics()).toEqual([]);
  });

  it("starts each viewer with status, then cached world and tf_static", () => {
    const relay = connectedRelay(true);
    relay.receive("/sim/world", WORLD);
    relay.receive("/tf_static", TF_STATIC);
    relay.receive("/telemetry", TELEMETRY);
    const viewer = new FakeViewer();
    relay.addViewer(viewer);
    expect(viewer.sent[0]).toEqual({
      type: "status",
      runtime: "connected",
      testControl: true,
    });
    expect(viewer.topics()).toEqual(["/sim/world", "/tf_static"]);
  });

  it("suppresses an unchanged world", () => {
    const relay = connectedRelay();
    const viewer = new FakeViewer();
    relay.addViewer(viewer);
    relay.receive("/sim/world", WORLD);
    relay.receive("/sim/world", WORLD);
    relay.receive("/sim/world", JSON.stringify({ data: [100, 100] }));
    expect(viewer.topics()).toEqual(["/sim/world", "/sim/world"]);
  });

  it("drops tick data but not world for a slow viewer", () => {
    const relay = connectedRelay();
    const slow = new FakeViewer();
    const fast = new FakeViewer();
    relay.addViewer(slow);
    relay.addViewer(fast);
    slow.bufferedAmount = MAX_BUFFERED + 1;
    relay.receive("/telemetry", TELEMETRY);
    relay.receive("/sim/world", WORLD);
    expect(slow.topics()).toEqual(["/sim/world"]);
    expect(fast.topics()).toEqual(["/telemetry", "/sim/world"]);
  });

  it("reports offline and forgets cached data", () => {
    const relay = connectedRelay();
    const viewer = new FakeViewer();
    relay.addViewer(viewer);
    relay.receive("/sim/world", WORLD);
    relay.setRuntimeConnected(false);
    expect(viewer.sent.at(-1)).toEqual({
      type: "status",
      runtime: "offline",
      testControl: false,
    });
    const late = new FakeViewer();
    relay.addViewer(late);
    expect(late.topics()).toEqual([]);
  });

  it("stops sending to removed viewers", () => {
    const relay = connectedRelay();
    const viewer = new FakeViewer();
    relay.addViewer(viewer);
    relay.removeViewer(viewer);
    relay.receive("/telemetry", TELEMETRY);
    expect(viewer.topics()).toEqual([]);
    expect(relay.viewerCount).toBe(0);
  });

  it("reports health with the last telemetry stamp", () => {
    const relay = connectedRelay();
    expect(relay.health()).toEqual({ runtimeConnected: true, lastStamp: null });
    relay.receive("/telemetry", TELEMETRY);
    expect(relay.health()).toEqual({
      runtimeConnected: true,
      lastStamp: { sec: 1, nanosec: 50_000_000 },
    });
  });
});

describe("parseTestCommand", () => {
  it("accepts a bounded integer step", () => {
    expect(parseTestCommand('{"op":"step","count":1}')).toEqual({
      op: "step",
      count: 1,
    });
    expect(parseTestCommand('{"op":"step","count":1000}')?.count).toBe(1000);
  });

  it.each([
    '{"op":"step","count":0}',
    '{"op":"step","count":1001}',
    '{"op":"step","count":2.5}',
    '{"op":"step","count":true}',
    '{"op":"step","count":"3"}',
    '{"op":"load","count":1}',
    '{"op":"step","count":1,"extra":1}',
    "[]",
    "null",
    "not json",
  ])("rejects %s", (raw) => {
    expect(parseTestCommand(raw)).toBeNull();
  });
});
