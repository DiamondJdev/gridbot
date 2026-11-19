/** Assemble gateway messages into complete simulation ticks. */

import type { ServerMessage } from "../../gateway/src/protocol.js";
import {
  parseMounts,
  parsePose,
  parseScan,
  parseTelemetry,
  parseWorld,
  sameStamp,
  type Mount,
  type Pose2D,
  type Scan,
  type Stamp,
  type World,
} from "./parse.js";

export type { Mount, Pose2D, Scan, World } from "./parse.js";

const SCAN_PREFIX = "/scan/";

/** One tick whose pose and scans all carry the telemetry stamp. */
export type CompleteFrame = {
  tick: number;
  collisions: number;
  pathLengthM: number;
  robot: Pose2D;
  scans: readonly { mount: Mount; scan: Scan }[];
};

export type ViewState = {
  runtime: "connecting" | "connected" | "offline";
  testControl: boolean;
  world: World | null;
  mounts: ReadonlyMap<string, Mount> | null;
  pose: { stamp: Stamp; pose: Pose2D } | null;
  scans: ReadonlyMap<string, Scan>;
  latest: CompleteFrame | null;
};

export function initialState(): ViewState {
  return {
    runtime: "connecting",
    testControl: false,
    world: null,
    mounts: null,
    pose: null,
    scans: new Map(),
    latest: null,
  };
}

/**
 * Close the tick that `/telemetry` ends. The tick is kept only when the pose
 * and every mounted sensor's scan carry the same stamp, so rays never attach
 * to an older robot pose.
 */
function closeTick(state: ViewState, body: unknown): ViewState {
  const telemetry = parseTelemetry(body);
  const { mounts, pose } = state;
  if (telemetry === null || mounts === null || pose === null) return state;
  if (!sameStamp(pose.stamp, telemetry.stamp)) return state;
  const scans: { mount: Mount; scan: Scan }[] = [];
  for (const [id, mount] of mounts) {
    const scan = state.scans.get(id);
    if (scan === undefined || !sameStamp(scan.stamp, telemetry.stamp)) {
      return state;
    }
    scans.push({ mount, scan });
  }
  const { tick, collisions, pathLengthM } = telemetry;
  return {
    ...state,
    latest: { tick, collisions, pathLengthM, robot: pose.pose, scans },
  };
}

function receive(state: ViewState, topic: string, body: unknown): ViewState {
  if (topic === "/telemetry") return closeTick(state, body);
  if (topic === "/sim/world") {
    const world = parseWorld(body);
    return world === null ? state : { ...state, world };
  }
  if (topic === "/tf_static") {
    const mounts = parseMounts(body);
    return mounts === null ? state : { ...state, mounts };
  }
  if (topic === "/sim/ground_truth") {
    const pose = parsePose(body);
    return pose === null ? state : { ...state, pose };
  }
  if (topic.startsWith(SCAN_PREFIX)) {
    const scan = parseScan(body);
    if (scan === null) return state;
    const scans = new Map(state.scans);
    scans.set(topic.slice(SCAN_PREFIX.length), scan);
    return { ...state, scans };
  }
  return state;
}

/** Return the state after one gateway message. Never mutates `state`. */
export function reduce(state: ViewState, message: ServerMessage): ViewState {
  if (message.type === "message") {
    return receive(state, message.topic, message.message);
  }
  if (message.runtime === "offline") {
    return {
      ...initialState(),
      runtime: "offline",
      testControl: message.testControl,
    };
  }
  return { ...state, runtime: "connected", testControl: message.testControl };
}
