/** Turn a complete frame into canvas geometry and paint it. */

import type { CompleteFrame, Pose2D, World } from "./frames.js";
import type { View } from "./view.js";

/** Drawn robot radius in metres, matching the simulator's default robot. */
const ROBOT_RADIUS_M = 0.25;
const OCCUPIED = 100;
const RGBA = 4;
const HIT_PX = 3;
const RAY_ALPHA = 0.22;
/** Where the heading tick starts, as a fraction of the robot radius. */
const HEADING_START = 0.4;

type Point = { x: number; y: number };

/** One sensor's rays: its origin and hits in metres in the map frame. */
export type SensorRays = { origin: Point; hits: Point[] };

export type DrawnFrame = {
  tick: number;
  robot: Pose2D;
  /** The first sensor's origin, in metres in the map frame. */
  lidarOrigin: Point;
  /** Every sensor's hits in metres; one per non-null range. */
  rayHits: Point[];
  sensors: SensorRays[];
  robotPx: Point;
};

export type Palette = {
  ground: string;
  free: string;
  wall: string;
  robot: string;
  ray: string;
};

function sensorRays(
  robot: Pose2D,
  { mount, scan }: CompleteFrame["scans"][number],
): SensorRays {
  const cos = Math.cos(robot.theta);
  const sin = Math.sin(robot.theta);
  const origin = {
    x: robot.x + mount.x * cos - mount.y * sin,
    y: robot.y + mount.x * sin + mount.y * cos,
  };
  const hits: Point[] = [];
  scan.ranges.forEach((range, i) => {
    if (range === null) return;
    const angle =
      robot.theta + mount.yaw + scan.angleMin + i * scan.angleIncrement;
    hits.push({
      x: origin.x + range * Math.cos(angle),
      y: origin.y + range * Math.sin(angle),
    });
  });
  return { origin, hits };
}

/** Geometry for one frame. Each sensor's rays start at its own mount. */
export function drawnFrame(frame: CompleteFrame, view: View): DrawnFrame {
  const { robot } = frame;
  const sensors = frame.scans.map((entry) => sensorRays(robot, entry));
  return {
    tick: frame.tick,
    robot,
    lidarOrigin: sensors[0]?.origin ?? { x: robot.x, y: robot.y },
    rayHits: sensors.flatMap((sensor) => sensor.hits),
    sensors,
    robotPx: view.toPx(robot.x, robot.y),
  };
}

function rgb(hex: string): [number, number, number] {
  const value = Number.parseInt(hex.replace("#", ""), 16);
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
}

/**
 * Pixels for the map, one per cell, north row first. Fills a fresh array
 * because ImageData needs one mutable buffer.
 */
export function mapPixels(
  world: World,
  free: string,
  wall: string,
): Uint8ClampedArray<ArrayBuffer> {
  const pixels = new Uint8ClampedArray(world.width * world.height * RGBA);
  const [freeRgb, wallRgb] = [rgb(free), rgb(wall)];
  for (let row = 0; row < world.height; row++) {
    const source = (world.height - 1 - row) * world.width;
    for (let col = 0; col < world.width; col++) {
      const colour = world.data[source + col] === OCCUPIED ? wallRgb : freeRgb;
      pixels.set([...colour, 255], (row * world.width + col) * RGBA);
    }
  }
  return pixels;
}

export function paint(
  ctx: CanvasRenderingContext2D,
  view: View,
  map: { image: CanvasImageSource; widthM: number; heightM: number },
  drawn: DrawnFrame | null,
  palette: Palette,
): void {
  const { width, height } = ctx.canvas;
  ctx.fillStyle = palette.ground;
  ctx.fillRect(0, 0, width, height);
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(
    map.image,
    view.left,
    view.top,
    map.widthM * view.pxPerM,
    map.heightM * view.pxPerM,
  );
  if (drawn === null) return;
  const sensors = drawn.sensors.map((sensor) => ({
    origin: view.toPx(sensor.origin.x, sensor.origin.y),
    hits: sensor.hits.map((hit) => view.toPx(hit.x, hit.y)),
  }));
  ctx.strokeStyle = palette.ray;
  ctx.lineWidth = 1;
  ctx.globalAlpha = RAY_ALPHA;
  ctx.beginPath();
  for (const { origin, hits } of sensors) {
    for (const hit of hits) {
      ctx.moveTo(origin.x, origin.y);
      ctx.lineTo(hit.x, hit.y);
    }
  }
  ctx.stroke();
  ctx.globalAlpha = 1;
  ctx.fillStyle = palette.ray;
  for (const { hits } of sensors) {
    for (const hit of hits) ctx.fillRect(hit.x - 1, hit.y - 1, HIT_PX, HIT_PX);
  }
  paintRobot(ctx, view, drawn, palette);
}

function paintRobot(
  ctx: CanvasRenderingContext2D,
  view: View,
  drawn: DrawnFrame,
  palette: Palette,
): void {
  const { robotPx, robot } = drawn;
  const radius = ROBOT_RADIUS_M * view.pxPerM;
  ctx.fillStyle = palette.robot;
  ctx.beginPath();
  ctx.arc(robotPx.x, robotPx.y, radius, 0, Math.PI * 2);
  ctx.fill();
  // The heading tick starts off-centre so the centre pixel stays the robot
  // colour. Screen y grows downward, so the heading's y component flips.
  const dx = Math.cos(robot.theta);
  const dy = -Math.sin(robot.theta);
  ctx.strokeStyle = palette.ground;
  ctx.lineWidth = Math.max(1.5, radius / 5);
  ctx.beginPath();
  ctx.moveTo(
    robotPx.x + HEADING_START * radius * dx,
    robotPx.y + HEADING_START * radius * dy,
  );
  ctx.lineTo(robotPx.x + radius * dx, robotPx.y + radius * dy);
  ctx.stroke();
}
