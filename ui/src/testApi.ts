/** Browser hooks for end-to-end tests. Installed only with ?test=1. */

import {
  MAX_STEP_COUNT,
  type TestCommand,
} from "../../gateway/src/protocol.js";
import type { DrawnFrame } from "./render.js";

const POLL_MS = 20;
const DEFAULT_TIMEOUT_MS = 30_000;

export type TestState = {
  runtime: "connecting" | "connected" | "offline";
  testControl: boolean;
  drawn: DrawnFrame | null;
};

export type TestApi = {
  getState(): TestState;
  /** Resolve once a frame at or after `tick` has been drawn. */
  waitForTick(tick: number, timeoutMs?: number): Promise<DrawnFrame>;
  /** Ask the simulator for `count` more ticks. */
  step(count: number): void;
};

export type TestSource = {
  state(): TestState;
  send(text: string): void;
};

function waitForTick(
  source: TestSource,
  tick: number,
  timeoutMs: number,
): Promise<DrawnFrame> {
  const deadline = Date.now() + timeoutMs;
  return new Promise((resolve, reject) => {
    const check = () => {
      const drawn = source.state().drawn;
      if (drawn !== null && drawn.tick >= tick) return resolve(drawn);
      if (Date.now() > deadline)
        return reject(new Error(`timed out waiting for tick ${tick}`));
      setTimeout(check, POLL_MS);
    };
    check();
  });
}

function step(source: TestSource, count: number): void {
  if (!Number.isInteger(count) || count < 1)
    throw new Error("step count must be a positive integer");
  for (let left = count; left > 0; left -= MAX_STEP_COUNT) {
    const command: TestCommand = {
      op: "step",
      count: Math.min(left, MAX_STEP_COUNT),
    };
    source.send(JSON.stringify(command));
  }
}

export function installTestApi(
  target: { __gridbot?: TestApi },
  search: string,
  source: TestSource,
): void {
  if (new URLSearchParams(search).get("test") !== "1") return;
  target.__gridbot = {
    getState: () => source.state(),
    waitForTick: (tick, timeoutMs = DEFAULT_TIMEOUT_MS) =>
      waitForTick(source, tick, timeoutMs),
    step: (count) => step(source, count),
  };
}
