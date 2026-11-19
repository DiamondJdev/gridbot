import type { ServerMessage } from "../../gateway/src/protocol.js";

const TICK_NS = 50_000_000;
const NS_PER_S = 1_000_000_000;

export function stamp(tick: number): { sec: number; nanosec: number } {
  const ns = tick * TICK_NS;
  return { sec: Math.floor(ns / NS_PER_S), nanosec: ns % NS_PER_S };
}

export function message(topic: string, body: unknown): ServerMessage {
  return { type: "message", topic, message: body };
}

export function quaternion(yaw: number) {
  return { x: 0, y: 0, z: Math.sin(yaw / 2), w: Math.cos(yaw / 2) };
}

/** A 4 x 2 map at 0.5 m whose top-left cell (north-west) is occupied. */
export function world(): ServerMessage {
  return message("/sim/world", {
    header: { stamp: stamp(0), frame_id: "map" },
    info: {
      resolution: 0.5,
      width: 4,
      height: 2,
      origin: { position: { x: 0, y: 0, z: 0 }, orientation: quaternion(0) },
    },
    // Rows run south to north, so index 4 is the north-west cell.
    data: [0, 0, 0, 0, 100, 0, 0, 0],
  });
}

export function tfStatic(mountX = 0.1, yaw = 0): ServerMessage {
  return message("/tf_static", {
    transforms: [
      {
        header: { stamp: stamp(0), frame_id: "base_link" },
        child_frame_id: "lidar",
        transform: {
          translation: { x: mountX, y: 0, z: 0 },
          rotation: quaternion(yaw),
        },
      },
    ],
  });
}

export function scan(
  tick: number,
  ranges: (number | null)[] = [1, null],
): ServerMessage {
  return message("/scan/lidar", {
    header: { stamp: stamp(tick), frame_id: "lidar" },
    angle_min: 0,
    angle_increment: Math.PI / 2,
    range_min: 0.05,
    range_max: 10,
    ranges,
  });
}

export function groundTruth(
  tick: number,
  x = 1,
  y = 0.5,
  theta = 0,
): ServerMessage {
  return message("/sim/ground_truth", {
    header: { stamp: stamp(tick), frame_id: "map" },
    pose: { position: { x, y, z: 0 }, orientation: quaternion(theta) },
  });
}

export function telemetry(tick: number, collisions = 0): ServerMessage {
  return message("/telemetry", {
    stamp: stamp(tick),
    source: "sim",
    keys: ["tick", "collisions", "pathLengthM"],
    values: [tick, collisions, tick * 0.04],
  });
}

/** Every message of one tick, in the runner's publish order. */
export function tick(n: number): ServerMessage[] {
  return [scan(n), groundTruth(n), telemetry(n)];
}
