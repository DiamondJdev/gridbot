/** Turn a complete frame into canvas geometry and paint it. */

import type { CompleteFrame, Pose2D, World } from "./frames.js";
import type { View } from "./view.js";

/** Drawn robot radius in metres, matching the simulator's default robot. */
const ROBOT_RADIUS_M = 0.25;
const OCCUPIED = 100;
const RGBA = 4;
const HIT_PX = 3;
const RAY_ALPHA = 0.22;

type Point = { x: number; y: number };

export type DrawnFrame = {
  tick: number;
  robot: Pose2D;
  /** Metres in the map frame. */
  lidarOrigin: Point;
  /** Metres in the map frame; one per non-null range. */
  rayHits: Point[];
  robotPx: Point;
};

export type Palette = {
  ground: string;
  free: string;
  wall: string;
  robot: string;
  ray: string;
};

/** Geometry for one frame. Rays start at the first mounted sensor. */
export function drawnFrame(frame: CompleteFrame, view: View): DrawnFrame {
  const { robot } = frame;
  const cos = Math.cos(robot.theta);
  const sin = Math.sin(robot.theta);
  let lidarOrigin = { x: robot.x, y: robot.y };
  const rayHits: Point[] = [];
  for (const { mount, scan } of frame.scans) {
    const origin = {
      x: robot.x + mount.x * cos - mount.y * sin,
      y: robot.y + mount.x * sin + mount.y * cos,
    };
    if (rayHits.length === 0) lidarOrigin = origin;
    scan.ranges.forEach((range, i) => {
      if (range === null) return;
      const angle =
        robot.theta + mount.yaw + scan.angleMin + i * scan.angleIncrement;
      rayHits.push({
        x: origin.x + range * Math.cos(angle),
        y: origin.y + range * Math.sin(angle),
      });
    });
  }
  return {
    tick: frame.tick,
    robot,
    lidarOrigin,
    rayHits,
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
  const origin = view.toPx(drawn.lidarOrigin.x, drawn.lidarOrigin.y);
  const hits = drawn.rayHits.map((hit) => view.toPx(hit.x, hit.y));
  ctx.strokeStyle = palette.ray;
  ctx.lineWidth = 1;
  ctx.globalAlpha = RAY_ALPHA;
  ctx.beginPath();
  for (const hit of hits) {
    ctx.moveTo(origin.x, origin.y);
    ctx.lineTo(hit.x, hit.y);
  }
  ctx.stroke();
  ctx.globalAlpha = 1;
  ctx.fillStyle = palette.ray;
  for (const hit of hits) ctx.fillRect(hit.x - 1, hit.y - 1, HIT_PX, HIT_PX);
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
  // Screen y grows downward, so the heading's y component flips.
  ctx.strokeStyle = palette.ground;
  ctx.lineWidth = Math.max(1.5, radius / 5);
  ctx.beginPath();
  ctx.moveTo(robotPx.x, robotPx.y);
  ctx.lineTo(
    robotPx.x + radius * Math.cos(robot.theta),
    robotPx.y - radius * Math.sin(robot.theta),
  );
  ctx.stroke();
}
