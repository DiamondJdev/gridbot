/** Browser entry: connect to the gateway and draw the newest complete tick. */

import "./styles.css";
import type { ServerMessage } from "../../gateway/src/protocol.js";
import {
  initialState,
  reduce,
  type CompleteFrame,
  type ViewState,
  type World,
} from "./frames.js";
import {
  drawnFrame,
  mapPixels,
  paint,
  type DrawnFrame,
  type Palette,
} from "./render.js";
import { installTestApi, type TestApi } from "./testApi.js";
import { fitView } from "./view.js";

const RECONNECT_MS = 1000;
const TICK_S = 0.05;
const CONNECTION_LABEL = {
  connecting: "Connecting",
  connected: "Live",
  offline: "Offline",
} as const;

declare global {
  interface Window {
    __gridbot?: TestApi;
  }
}

function element<T extends HTMLElement = HTMLElement>(selector: string): T {
  const found = document.querySelector<T>(selector);
  if (found === null) throw new Error(`missing ${selector}`);
  return found;
}

const canvas = element<HTMLCanvasElement>("#stage");
const ctx = canvas.getContext("2d");
if (ctx === null) throw new Error("2D canvas is unavailable");
const fields = {
  tick: element("#tick"),
  time: element("#time"),
  collisions: element("#collisions"),
  path: element("#path"),
  connection: element("#connection"),
  empty: element("#empty"),
};

let state: ViewState = initialState();
let socket: WebSocket | null = null;
let drawn: DrawnFrame | null = null;
let painted: {
  frame: CompleteFrame | null;
  size: string;
  map: World | null;
} | null = null;
let mapCache: { world: World; image: HTMLCanvasElement } | null = null;

function palette(): Palette {
  const css = getComputedStyle(document.documentElement);
  const token = (name: string) => css.getPropertyValue(name).trim();
  return {
    ground: token("--stage"),
    free: token("--map-free"),
    wall: token("--map-wall"),
    robot: token("--text"),
    ray: token("--accent"),
  };
}

function mapImage(world: World, colours: Palette): HTMLCanvasElement {
  if (mapCache?.world === world) return mapCache.image;
  const image = document.createElement("canvas");
  image.width = world.width;
  image.height = world.height;
  const pixels = mapPixels(world, colours.free, colours.wall);
  image
    .getContext("2d")
    ?.putImageData(new ImageData(pixels, world.width, world.height), 0, 0);
  mapCache = { world, image };
  return image;
}

function resizeCanvas(world: World): string {
  const widthM = world.width * world.resolution;
  const heightM = world.height * world.resolution;
  canvas.style.aspectRatio = `${widthM} / ${heightM}`;
  const scale = window.devicePixelRatio || 1;
  const width = Math.round(canvas.clientWidth * scale);
  const height = Math.round(canvas.clientHeight * scale);
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  return `${width}x${height}`;
}

function updateHeader(): void {
  const frame = state.latest;
  fields.tick.textContent =
    frame === null ? "–" : frame.tick.toLocaleString("en-US");
  fields.time.textContent =
    frame === null ? "–" : (frame.tick * TICK_S).toFixed(2);
  fields.collisions.textContent =
    frame === null ? "–" : String(frame.collisions);
  fields.collisions.classList.toggle("bad", (frame?.collisions ?? 0) > 0);
  fields.path.textContent = frame === null ? "–" : frame.pathLengthM.toFixed(2);
  fields.connection.textContent = CONNECTION_LABEL[state.runtime];
  fields.connection.dataset.state = state.runtime;
  fields.empty.hidden = frame !== null;
  fields.empty.textContent =
    state.runtime === "offline"
      ? "The simulator is offline. Reconnecting…"
      : "Waiting for the simulator…";
}

function draw(): void {
  requestAnimationFrame(draw);
  const world = state.world;
  if (world === null) {
    drawn = null;
    painted = null;
    updateHeader();
    return;
  }
  const size = resizeCanvas(world);
  if (
    painted?.frame === state.latest &&
    painted.size === size &&
    painted.map === world
  )
    return;
  const colours = palette();
  const view = fitView(world, canvas.width, canvas.height);
  drawn = state.latest === null ? null : drawnFrame(state.latest, view);
  const map = {
    image: mapImage(world, colours),
    widthM: world.width * world.resolution,
    heightM: world.height * world.resolution,
  };
  paint(ctx!, view, map, drawn, colours);
  painted = { frame: state.latest, size, map: world };
  updateHeader();
}

function receive(event: MessageEvent): void {
  try {
    state = reduce(state, JSON.parse(String(event.data)) as ServerMessage);
  } catch (error) {
    console.error("Dropped a gateway message that was not JSON", error);
  }
}

function connect(): void {
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${scheme}://${location.host}/ws`);
  ws.addEventListener("message", receive);
  ws.addEventListener("close", () => {
    state = reduce(state, {
      type: "status",
      runtime: "offline",
      testControl: false,
    });
    socket = null;
    setTimeout(connect, RECONNECT_MS);
  });
  socket = ws;
}

installTestApi(window, location.search, {
  state: () => ({
    runtime: state.runtime,
    testControl: state.testControl,
    drawn,
  }),
  send: (text) => {
    if (socket?.readyState !== WebSocket.OPEN)
      throw new Error("gateway socket is not open");
    socket.send(text);
  },
});
connect();
requestAnimationFrame(draw);
