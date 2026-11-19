import { describe, expect, it } from "vitest";
import { initialState, reduce } from "../src/frames.js";
import { drawnFrame } from "../src/render.js";
import { installTestApi, type TestApi } from "../src/testApi.js";
import { fitView } from "../src/view.js";
import { groundTruth, scan, telemetry, tfStatic, world } from "./fixtures.js";

const VIEW = fitView(
  { resolution: 0.5, width: 4, height: 2, originX: 0, originY: 0 },
  200,
  100,
);

function frameAt(theta: number, ranges: (number | null)[]) {
  const state = [
    world(),
    tfStatic(0.1),
    scan(5, ranges),
    groundTruth(5, 1, 0.5, theta),
    telemetry(5),
  ].reduce(reduce, initialState());
  if (state.latest === null) throw new Error("frame did not complete");
  return state.latest;
}

function close(a: { x: number; y: number }, b: { x: number; y: number }) {
  expect(a.x).toBeCloseTo(b.x, 9);
  expect(a.y).toBeCloseTo(b.y, 9);
}

describe("drawnFrame", () => {
  it("null ranges draw no hit", () => {
    const drawn = drawnFrame(frameAt(0, [1, null, null]), VIEW);
    expect(drawn.rayHits).toHaveLength(1);
  });

  it("rays start at the mounted lidar", () => {
    const drawn = drawnFrame(frameAt(Math.PI / 2, [1, 2]), VIEW);
    close(drawn.lidarOrigin, { x: 1, y: 0.6 });
    close(drawn.rayHits[0]!, { x: 1, y: 1.6 });
    close(drawn.rayHits[1]!, { x: -1, y: 0.6 });
    expect(drawn.tick).toBe(5);
    close(drawn.robotPx, { x: 100, y: 50 });
  });

  it("starts each lidar's rays at its own mount", () => {
    const scanOf = (ranges: (number | null)[]) => ({
      stamp: { sec: 0, nanosec: 0 },
      angleMin: 0,
      angleIncrement: Math.PI,
      ranges,
    });
    const drawn = drawnFrame(
      {
        tick: 1,
        collisions: 0,
        pathLengthM: 0,
        robot: { x: 1, y: 0.5, theta: 0 },
        scans: [
          { mount: { x: 0.1, y: 0, yaw: 0 }, scan: scanOf([null]) },
          { mount: { x: -0.2, y: 0, yaw: Math.PI }, scan: scanOf([0.5]) },
        ],
      },
      VIEW,
    );
    expect(drawn.sensors).toHaveLength(2);
    close(drawn.sensors[1]!.origin, { x: 0.8, y: 0.5 });
    close(drawn.sensors[1]!.hits[0]!, { x: 0.3, y: 0.5 });
    close(drawn.lidarOrigin, { x: 1.1, y: 0.5 });
  });
});

describe("test API", () => {
  function install(search: string) {
    const sent: string[] = [];
    const target: { __gridbot?: TestApi } = {};
    const state = { runtime: "connected" as const, testControl: true };
    installTestApi(target, search, {
      state: () => ({ ...state, drawn: null }),
      send: (text) => sent.push(text),
    });
    return { target, sent };
  }

  it("test API is absent without test=1", () => {
    expect(install("").target.__gridbot).toBeUndefined();
    expect(install("?test=0").target.__gridbot).toBeUndefined();
  });

  it("splits large steps into gateway-sized commands", () => {
    const { target, sent } = install("?test=1");
    target.__gridbot!.step(2500);
    expect(sent.map((text) => JSON.parse(text) as unknown)).toEqual([
      { op: "step", count: 1000 },
      { op: "step", count: 1000 },
      { op: "step", count: 500 },
    ]);
  });

  it("rejects a wait that never reaches its tick", async () => {
    const { target } = install("?test=1");
    await expect(target.__gridbot!.waitForTick(3, 30)).rejects.toThrow(
      "tick 3",
    );
  });
});
