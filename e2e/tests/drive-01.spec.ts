import { execFileSync } from "node:child_process";
import { resolve } from "node:path";
import { expect, test, type Page } from "@playwright/test";
import type { DrawnFrame } from "../../ui/src/render.js";
import type { TestApi } from "../../ui/src/testApi.js";

const ROOT = resolve(import.meta.dirname, "../..");
const SCREENSHOTS = resolve(ROOT, "artifacts/e2e");
const LAST_TICK = 1128;
const CHECK_TICKS = [0, 350, LAST_TICK];
const HIT_TOLERANCE_M = 0.15;
const OCCUPIED = 100;
const WAIT_MS = 60_000;

type Grid = {
  resolution: number;
  width: number;
  height: number;
  originX: number;
  originY: number;
  data: number[];
};
type Report = {
  collisions: number;
  endPose: { x: number; y: number; theta: number };
};

declare global {
  interface Window {
    __gridbot?: TestApi;
  }
}

test.describe.configure({ mode: "serial" });

let page: Page;
const problems: string[] = [];
let lastTick = -1;

test.beforeAll(async ({ browser }) => {
  page = await browser.newPage();
  page.on("console", (message) => {
    if (message.type() === "error") problems.push(`console: ${message.text()}`);
  });
  page.on("pageerror", (error) => problems.push(`page: ${error.message}`));
  page.on("requestfailed", (request) =>
    problems.push(`request: ${request.url()} ${request.failure()?.errorText}`),
  );
  await page.goto("/?test=1");
  await page.waitForFunction(
    () => window.__gridbot?.getState().runtime === "connected",
  );
});

test.afterEach(() => {
  expect(problems).toEqual([]);
});

test.afterAll(async () => {
  await page.close();
});

/** Step until `tick` is drawn. The first step publishes tick 0. */
async function stepTo(tick: number): Promise<DrawnFrame> {
  const count = tick - lastTick;
  lastTick = tick;
  return page.evaluate(
    async ({ count, tick, timeout }) => {
      const api = window.__gridbot!;
      api.step(count);
      return api.waitForTick(tick, timeout);
    },
    { count, tick, timeout: WAIT_MS },
  );
}

/** Read the cached world through a second, read-only viewer socket. */
function readGrid(): Promise<Grid> {
  return page.evaluate(
    () =>
      new Promise<Grid>((done, fail) => {
        const ws = new WebSocket(`ws://${location.host}/ws`);
        ws.onerror = () => fail(new Error("world socket failed"));
        ws.onmessage = (event) => {
          const message = JSON.parse(String(event.data));
          if (message.topic !== "/sim/world") return;
          const { info, data } = message.message;
          ws.close();
          done({
            resolution: info.resolution,
            width: info.width,
            height: info.height,
            originX: info.origin.position.x,
            originY: info.origin.position.y,
            data,
          });
        };
      }),
  );
}

/** Distance in metres from a point to the nearest occupied cell. */
function wallDistance(grid: Grid, x: number, y: number): number {
  const reach = Math.ceil(HIT_TOLERANCE_M / grid.resolution) + 1;
  const col = Math.floor((x - grid.originX) / grid.resolution);
  const row = Math.floor((y - grid.originY) / grid.resolution);
  let best = Infinity;
  for (let r = row - reach; r <= row + reach; r++) {
    for (let c = col - reach; c <= col + reach; c++) {
      if (r < 0 || c < 0 || r >= grid.height || c >= grid.width) continue;
      if (grid.data[r * grid.width + c] !== OCCUPIED) continue;
      const left = grid.originX + c * grid.resolution;
      const bottom = grid.originY + r * grid.resolution;
      const dx = Math.max(left - x, 0, x - (left + grid.resolution));
      const dy = Math.max(bottom - y, 0, y - (bottom + grid.resolution));
      best = Math.min(best, Math.hypot(dx, dy));
    }
  }
  return best;
}

async function robotPixel(frame: DrawnFrame): Promise<number[]> {
  return page.evaluate(({ x, y }) => {
    const canvas = document.querySelector<HTMLCanvasElement>("#stage")!;
    const pixel = canvas
      .getContext("2d")!
      .getImageData(Math.round(x), Math.round(y), 1, 1);
    return [...pixel.data];
  }, frame.robotPx);
}

test("draws rays that end at walls", async () => {
  // The runner publishes the world with tick 0, so read it after that step.
  const first = await stepTo(0);
  const grid = await readGrid();
  for (const tick of CHECK_TICKS) {
    const frame = tick === 0 ? first : await stepTo(tick);
    expect(frame.tick).toBe(tick);
    expect(frame.rayHits.length).toBeGreaterThan(0);
    const far = frame.rayHits.filter(
      (hit) => wallDistance(grid, hit.x, hit.y) > HIT_TOLERANCE_M,
    );
    expect(far).toEqual([]);
    const [red, green, blue] = await robotPixel(frame);
    // The robot is white at its centre; the floor (#1c1c20) is near black.
    expect(Math.min(red!, green!, blue!)).toBeGreaterThan(200);
    await page.screenshot({
      path: `${SCREENSHOTS}/drive-01-tick-${String(tick).padStart(4, "0")}.png`,
    });
  }
});

test("matches the headless run", async () => {
  const output = execFileSync(
    "uv",
    ["run", "gridbot-run", "scenarios/drive-01.json", "--json"],
    { cwd: ROOT, encoding: "utf8" },
  );
  const report = JSON.parse(output) as Report;
  const frame = await page.evaluate(() => window.__gridbot!.getState().drawn);
  expect(frame?.tick).toBe(LAST_TICK);
  expect(frame?.robot.x).toBe(report.endPose.x);
  expect(frame?.robot.y).toBe(report.endPose.y);
  // Theta crosses the wire as a quaternion, so it may differ in the last bits.
  expect(frame?.robot.theta).toBeCloseTo(report.endPose.theta, 12);
  await expect(page.locator("#collisions")).toHaveText(
    String(report.collisions),
  );
});
