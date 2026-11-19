import {
  createServer,
  type IncomingMessage,
  type ServerResponse,
} from "node:http";
import type { AddressInfo } from "node:net";
import type { Duplex } from "node:stream";
import { WebSocketServer, type WebSocket } from "ws";
import { isAllowedTopic, parseTestCommand } from "./protocol.js";
import { Relay } from "./relay.js";
import { RuntimeLink } from "./runtime.js";
import { readUiFile } from "./static.js";

export const MAX_INBOUND_BYTES = 1024;
export const MAX_BUFFERED_BYTES = 1024 * 1024;
const POLICY_VIOLATION = 1008;
const SECURITY_HEADERS = {
  "content-security-policy":
    "default-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
  "x-content-type-options": "nosniff",
  "referrer-policy": "no-referrer",
};

export type GatewayOptions = {
  host: string;
  port: number;
  uiDir: string;
  runtimeUrl: string;
  testControl: boolean;
  maxClients: number;
  reconnectMs: number;
};

export type Gateway = {
  readonly port: number;
  readonly viewerCount: number;
  close(): Promise<void>;
};

function reply(
  res: ServerResponse,
  status: number,
  body: string | Buffer,
  type: string,
): void {
  res.writeHead(status, {
    ...SECURITY_HEADERS,
    "content-type": type,
    "cache-control": "no-store",
  });
  res.end(body);
}

async function handleHttp(
  req: IncomingMessage,
  res: ServerResponse,
  relay: Relay,
  uiDir: string,
) {
  if (req.method !== "GET" && req.method !== "HEAD") {
    reply(res, 405, "Method not allowed", "text/plain; charset=utf-8");
    return;
  }
  const path = (req.url ?? "/").split("?")[0]!;
  if (path === "/healthz") {
    reply(
      res,
      200,
      JSON.stringify(relay.health()),
      "application/json; charset=utf-8",
    );
    return;
  }
  const file = await readUiFile(uiDir, path);
  if (file === null) reply(res, 404, "Not found", "text/plain; charset=utf-8");
  else
    reply(res, 200, req.method === "HEAD" ? "" : file.body, file.contentType);
}

function refuse(socket: Duplex, status: string): void {
  socket.end(`HTTP/1.1 ${status}\r\nConnection: close\r\n\r\n`);
}

function acceptViewer(
  ws: WebSocket,
  relay: Relay,
  link: RuntimeLink,
  testControl: boolean,
) {
  relay.addViewer(ws);
  ws.on("error", () => undefined);
  ws.on("close", () => relay.removeViewer(ws));
  ws.on("message", (data) => {
    const command = testControl ? parseTestCommand(String(data)) : null;
    if (command === null) ws.close(POLICY_VIOLATION, "Read-only connection");
    else link.sendStep(command.count);
  });
}

/** Start the HTTP server, browser sockets and runtime subscription. */
export async function startGateway(options: GatewayOptions): Promise<Gateway> {
  const relay = new Relay({
    testControl: options.testControl,
    maxBufferedBytes: MAX_BUFFERED_BYTES,
  });
  const link = new RuntimeLink({
    url: options.runtimeUrl,
    reconnectMs: options.reconnectMs,
    testControl: options.testControl,
    isAllowed: isAllowedTopic,
    onStatus: (connected) => relay.setRuntimeConnected(connected),
    onMessage: (topic, payload) => relay.receive(topic, payload),
  });
  const wss = new WebSocketServer({
    noServer: true,
    maxPayload: MAX_INBOUND_BYTES,
  });
  const http = createServer((req, res) => {
    handleHttp(req, res, relay, options.uiDir).catch(() =>
      reply(res, 500, "Error", "text/plain"),
    );
  });
  http.on("upgrade", (req, socket, head) => {
    if ((req.url ?? "").split("?")[0] !== "/ws")
      return refuse(socket, "404 Not Found");
    if (relay.viewerCount >= options.maxClients)
      return refuse(socket, "503 Service Unavailable");
    wss.handleUpgrade(req, socket, head, (ws) =>
      acceptViewer(ws, relay, link, options.testControl),
    );
  });
  await new Promise<void>((resolve) =>
    http.listen(options.port, options.host, resolve),
  );
  link.start();
  return {
    port: (http.address() as AddressInfo).port,
    get viewerCount() {
      return relay.viewerCount;
    },
    async close() {
      link.close();
      for (const client of wss.clients) client.terminate();
      await new Promise((resolve) => wss.close(resolve));
      await new Promise((resolve) => http.close(resolve));
    },
  };
}
