import { describe, expect, it } from "vitest";
import { initialState, reduce, type ViewState } from "../src/frames.js";
import {
  groundTruth,
  scan,
  telemetry,
  tfStatic,
  tick,
  world,
} from "./fixtures.js";
import type { ServerMessage } from "../../gateway/src/protocol.js";

function feed(messages: ServerMessage[], start = initialState()): ViewState {
  return messages.reduce(reduce, start);
}

describe("frame assembly", () => {
  it("commits only complete ticks", () => {
    const ready = feed([world(), tfStatic()]);
    const partial = feed([groundTruth(3), telemetry(3)], ready);
    expect(partial.latest).toBeNull();
    const done = feed(tick(4), partial);
    expect(done.latest?.tick).toBe(4);
    expect(done.latest?.collisions).toBe(0);
    expect(done.latest?.robot).toEqual({ x: 1, y: 0.5, theta: 0 });
  });

  it("skips a tick with a mismatched scan stamp", () => {
    const first = feed([world(), tfStatic(), ...tick(1)]);
    const next = feed([scan(1), groundTruth(2), telemetry(2)], first);
    expect(next.latest?.tick).toBe(1);
  });

  it("waits for the static transforms before drawing", () => {
    expect(feed([world(), ...tick(1)]).latest).toBeNull();
  });

  it("does not mutate the previous state", () => {
    const before = feed([world(), tfStatic()]);
    const after = feed(tick(1), before);
    expect(before.latest).toBeNull();
    expect(after).not.toBe(before);
  });

  it("ignores malformed messages", () => {
    const ready = feed([world(), tfStatic()]);
    const bad = feed(
      [
        { type: "message", topic: "/telemetry", message: { values: "x" } },
        { type: "message", topic: "/sim/world", message: null },
      ],
      ready,
    );
    expect(bad).toEqual(ready);
  });

  it("tracks runtime status and clears the frame when offline", () => {
    const live = feed([
      { type: "status", runtime: "connected", testControl: true },
      world(),
      tfStatic(),
      ...tick(1),
    ]);
    expect(live.runtime).toBe("connected");
    expect(live.testControl).toBe(true);
    const offline = reduce(live, {
      type: "status",
      runtime: "offline",
      testControl: true,
    });
    expect(offline.runtime).toBe("offline");
    expect(offline.latest).toBeNull();
    expect(offline.world).toBeNull();
  });
});
