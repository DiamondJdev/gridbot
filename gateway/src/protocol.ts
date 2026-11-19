/** Messages between the gateway and browsers. Shared with the UI as types. */

export type Stamp = { sec: number; nanosec: number };

export type ServerMessage =
  | { type: "message"; topic: string; message: unknown }
  | {
      type: "status";
      runtime: "connected" | "offline";
      testControl: boolean;
    };

export type TestCommand = { op: "step"; count: number };

export const MAX_STEP_COUNT = 1000;

const ALLOWED_TOPICS = new Set([
  "/sim/world",
  "/tf_static",
  "/odom",
  "/tf",
  "/sim/ground_truth",
  "/cmd_vel",
  "/telemetry",
]);
const SCAN_TOPIC = /^\/scan\/[a-z0-9_]+$/;

/** Topics browsers may receive. Everything else stays inside the gateway. */
export function isAllowedTopic(topic: string): boolean {
  return ALLOWED_TOPICS.has(topic) || SCAN_TOPIC.test(topic);
}

/** Parse a browser test command, or return null for anything else. */
export function parseTestCommand(raw: string): TestCommand | null {
  let value: unknown;
  try {
    value = JSON.parse(raw);
  } catch {
    return null;
  }
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return null;
  }
  const fields = value as Record<string, unknown>;
  const keys = Object.keys(fields).sort();
  const count = fields.count;
  const valid =
    keys.length === 2 &&
    keys[0] === "count" &&
    keys[1] === "op" &&
    fields.op === "step" &&
    Number.isInteger(count) &&
    (count as number) >= 1 &&
    (count as number) <= MAX_STEP_COUNT;
  return valid ? { op: "step", count: count as number } : null;
}
