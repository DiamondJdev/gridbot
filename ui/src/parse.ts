/** Narrow untrusted gateway JSON into the few shapes the view draws. */

export type Stamp = { sec: number; nanosec: number };
/** Metres and radians in the map frame. */
export type Pose2D = { x: number; y: number; theta: number };
/** Sensor offset from base_link, in metres and radians. */
export type Mount = { x: number; y: number; yaw: number };
export type World = {
  resolution: number;
  width: number;
  height: number;
  originX: number;
  originY: number;
  /** Row-major, rows south to north; 100 is occupied. */
  data: readonly number[];
};
export type Scan = {
  stamp: Stamp;
  angleMin: number;
  angleIncrement: number;
  ranges: readonly (number | null)[];
};
export type Telemetry = {
  stamp: Stamp;
  tick: number;
  collisions: number;
  pathLengthM: number;
};

type Obj = Record<string, unknown>;

function obj(value: unknown): Obj | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Obj)
    : null;
}

function num(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function at(value: unknown, ...path: string[]): unknown {
  return path.reduce<unknown>((node, key) => obj(node)?.[key], value);
}

function stamp(value: unknown): Stamp | null {
  const sec = num(at(value, "sec"));
  const nanosec = num(at(value, "nanosec"));
  return sec === null || nanosec === null ? null : { sec, nanosec };
}

export function sameStamp(a: Stamp, b: Stamp): boolean {
  return a.sec === b.sec && a.nanosec === b.nanosec;
}

/** Yaw from a quaternion that only rotates about z. */
function yaw(value: unknown): number | null {
  const z = num(at(value, "z"));
  const w = num(at(value, "w"));
  return z === null || w === null ? null : 2 * Math.atan2(z, w);
}

function planar(position: unknown, rotation: unknown): Pose2D | null {
  const x = num(at(position, "x"));
  const y = num(at(position, "y"));
  const theta = yaw(rotation);
  return x === null || y === null || theta === null ? null : { x, y, theta };
}

export function parseWorld(value: unknown): World | null {
  const info = at(value, "info");
  const resolution = num(at(info, "resolution"));
  const width = num(at(info, "width"));
  const height = num(at(info, "height"));
  const originX = num(at(info, "origin", "position", "x"));
  const originY = num(at(info, "origin", "position", "y"));
  const data = at(value, "data");
  const valid =
    resolution !== null &&
    resolution > 0 &&
    width !== null &&
    height !== null &&
    originX !== null &&
    originY !== null &&
    Array.isArray(data) &&
    data.length === width * height &&
    data.every((cell) => typeof cell === "number");
  return valid
    ? { resolution, width, height, originX, originY, data: data as number[] }
    : null;
}

/** Sensor mounts keyed by frame id, from /tf_static. */
export function parseMounts(value: unknown): ReadonlyMap<string, Mount> | null {
  const transforms = at(value, "transforms");
  if (!Array.isArray(transforms)) return null;
  const entries: [string, Mount][] = [];
  for (const item of transforms) {
    const id = at(item, "child_frame_id");
    const pose = planar(
      at(item, "transform", "translation"),
      at(item, "transform", "rotation"),
    );
    if (typeof id !== "string" || pose === null) return null;
    entries.push([id, { x: pose.x, y: pose.y, yaw: pose.theta }]);
  }
  return new Map(entries);
}

export function parsePose(
  value: unknown,
): { stamp: Stamp; pose: Pose2D } | null {
  const when = stamp(at(value, "header", "stamp"));
  const pose = planar(
    at(value, "pose", "position"),
    at(value, "pose", "orientation"),
  );
  return when === null || pose === null ? null : { stamp: when, pose };
}

export function parseScan(value: unknown): Scan | null {
  const when = stamp(at(value, "header", "stamp"));
  const angleMin = num(at(value, "angle_min"));
  const angleIncrement = num(at(value, "angle_increment"));
  const ranges = at(value, "ranges");
  const valid =
    when !== null &&
    angleMin !== null &&
    angleIncrement !== null &&
    Array.isArray(ranges) &&
    ranges.every((r) => r === null || num(r) !== null);
  return valid
    ? {
        stamp: when,
        angleMin,
        angleIncrement,
        ranges: ranges as (number | null)[],
      }
    : null;
}

export function parseTelemetry(value: unknown): Telemetry | null {
  const when = stamp(at(value, "stamp"));
  const keys = at(value, "keys");
  const values = at(value, "values");
  if (when === null || !Array.isArray(keys) || !Array.isArray(values)) {
    return null;
  }
  const field = (key: string) => num(values[keys.indexOf(key)]);
  const tick = field("tick");
  const collisions = field("collisions");
  const pathLengthM = field("pathLengthM");
  return tick === null || collisions === null || pathLengthM === null
    ? null
    : { stamp: when, tick, collisions, pathLengthM };
}
