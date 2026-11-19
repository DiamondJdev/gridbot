import { mkdtemp, mkdir, writeFile } from "node:fs/promises";
import { request, createServer, type Server } from "node:http";
import type { AddressInfo } from "node:net";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { FoxgloveServer } from "@foxglove/ws-protocol";
import { afterEach, describe, expect, it } from "vitest";
import WebSocket, { WebSocketServer } from "ws";
import type { ServerMessage } from "../src/protocol.js";
import { startGateway, type Gateway } from "../src/server.js";

const WAIT_MS = 3000;
const RECONNECT_MS = 50;
const TELEMETRY = { stamp: { sec: 0, nanosec: 50_000_000 }, values: [1] };

async function waitUntil(check: () => boolean): Promise<void> {
  const deadline = Date.now() + WAIT_MS;
  while (!check()) {
    if (Date.now() > deadline) throw new Error("timed out");
    await new Promise((resolve) => setTimeout(resolve, 10));
  }
}

/** A Foxglove runtime that stands in for the Python runner. */
class FakeRuntime {
  readonly published: string[] = [];
  private readonly channels = new Map<string, number>();
  private subscribed = 0;
  private constructor(
    private readonly http: Server,
    private readonly wss: WebSocketServer,
    private readonly foxglove: FoxgloveServer,
  ) {}

  static async start(port = 0, clientPublish = false): Promise<FakeRuntime> {
    const foxglove = new FoxgloveServer({
      name: "fake",
      capabilities: clientPublish ? ["clientPublish"] : [],
      supportedEncodings: ["json"],
    });
    const http = createServer();
    const wss = new WebSocketServer({
      server: http,
      handleProtocols: () => FoxgloveServer.SUPPORTED_SUBPROTOCOL,
    });
    const runtime = new FakeRuntime(http, wss, foxglove);
    for (const topic of ["/telemetry", "/sim/world", "/test/hidden"]) {
      const id = foxglove.addChannel({
        topic,
        encoding: "json",
        schemaName: "object",
        schema: "{}",
      });
      runtime.channels.set(topic, id);
    }
    wss.on("connection", (ws) => foxglove.handleConnection(ws, "gateway"));
    foxglove.on("subscribe", () => runtime.subscribed++);
    foxglove.on("message", ({ channel, data }) => {
      const text = new TextDecoder().decode(data);
      runtime.published.push(`${channel.topic} ${text}`);
    });
    await new Promise<void>((resolve) =>
      http.listen(port, "127.0.0.1", resolve),
    );
    return runtime;
  }

  get port(): number {
    return (this.http.address() as AddressInfo).port;
  }

  async ready(): Promise<void> {
    await waitUntil(() => this.subscribed >= 2);
  }

  send(topic: string, message: unknown): void {
    const payload = new TextEncoder().encode(JSON.stringify(message));
    this.foxglove.sendMessage(this.channels.get(topic)!, 0n, payload);
  }

  async stop(): Promise<void> {
    for (const client of this.wss.clients) client.terminate();
    await new Promise((resolve) => this.wss.close(resolve));
    await new Promise((resolve) => this.http.close(resolve));
  }
}

class Browser {
  readonly messages: ServerMessage[] = [];
  closeCode: number | null = null;
  readonly socket: WebSocket;

  constructor(port: number, path = "/ws") {
    this.socket = new WebSocket(`ws://127.0.0.1:${port}${path}`);
    this.socket.on("message", (data) =>
      this.messages.push(JSON.parse(String(data)) as ServerMessage),
    );
    this.socket.on("close", (code) => (this.closeCode = code));
    this.socket.on("error", () => undefined);
  }

  async opened(): Promise<void> {
    await waitUntil(() => this.socket.readyState === WebSocket.OPEN);
  }

  async waitFor(check: (message: ServerMessage) => boolean): Promise<void> {
    await waitUntil(() => this.messages.some(check));
  }
}

function get(
  port: number,
  path: string,
): Promise<{ status: number; headers: Record<string, unknown>; body: string }> {
  return new Promise((resolve, reject) => {
    const req = request({ host: "127.0.0.1", port, path }, (res) => {
      let body = "";
      res.on("data", (chunk) => (body += String(chunk)));
      res.on("end", () =>
        resolve({ status: res.statusCode ?? 0, headers: res.headers, body }),
      );
    });
    req.on("error", reject);
    req.end();
  });
}

async function uiDir(): Promise<string> {
  const root = await mkdtemp(join(tmpdir(), "gridbot-ui-"));
  const ui = join(root, "ui");
  await mkdir(ui);
  await writeFile(
    join(ui, "index.html"),
    "<!doctype html><title>Gridbot</title>",
  );
  await writeFile(join(ui, "app.js"), "export {};");
  await writeFile(join(root, "secret.txt"), "secret");
  return ui;
}

const cleanups: (() => Promise<void>)[] = [];
afterEach(async () => {
  for (const cleanup of cleanups.splice(0).reverse()) await cleanup();
});

async function setup(
  options: {
    testControl?: boolean;
    maxClients?: number;
    runtime?: boolean;
  } = {},
): Promise<{ gateway: Gateway; runtime: FakeRuntime | null }> {
  const runtime =
    options.runtime === false
      ? null
      : await FakeRuntime.start(0, options.testControl);
  if (runtime) cleanups.push(() => runtime.stop());
  const gateway = await startGateway({
    host: "127.0.0.1",
    port: 0,
    uiDir: await uiDir(),
    runtimeUrl: `ws://127.0.0.1:${runtime?.port ?? 1}`,
    testControl: options.testControl ?? false,
    maxClients: options.maxClients ?? 100,
    reconnectMs: RECONNECT_MS,
  });
  cleanups.push(() => gateway.close());
  await runtime?.ready();
  return { gateway, runtime };
}

function isTopic(topic: string) {
  return (message: ServerMessage) =>
    message.type === "message" && message.topic === topic;
}

describe("gateway server", () => {
  it("relays allowlisted runtime messages to browsers", async () => {
    const { gateway, runtime } = await setup();
    const browser = new Browser(gateway.port);
    await browser.waitFor(
      (m) => m.type === "status" && m.runtime === "connected",
    );
    runtime!.send("/test/hidden", { secret: true });
    runtime!.send("/telemetry", TELEMETRY);
    await browser.waitFor(isTopic("/telemetry"));
    expect(browser.messages.some(isTopic("/test/hidden"))).toBe(false);
    const health = await get(gateway.port, "/healthz");
    expect(JSON.parse(health.body)).toEqual({
      runtimeConnected: true,
      lastStamp: TELEMETRY.stamp,
    });
  });

  it("reports offline and reconnects when the runtime appears", async () => {
    const probe = await FakeRuntime.start();
    const port = probe.port;
    await probe.stop();
    const gateway = await startGateway({
      host: "127.0.0.1",
      port: 0,
      uiDir: await uiDir(),
      runtimeUrl: `ws://127.0.0.1:${port}`,
      testControl: false,
      maxClients: 100,
      reconnectMs: RECONNECT_MS,
    });
    cleanups.push(() => gateway.close());
    const browser = new Browser(gateway.port);
    await browser.waitFor(
      (m) => m.type === "status" && m.runtime === "offline",
    );
    const runtime = await FakeRuntime.start(port);
    cleanups.push(() => runtime.stop());
    await runtime.ready();
    await browser.waitFor(
      (m) => m.type === "status" && m.runtime === "connected",
    );
    runtime.send("/telemetry", TELEMETRY);
    await browser.waitFor(isTopic("/telemetry"));
  });

  it("closes visitor sockets that send data with 1008", async () => {
    const { gateway, runtime } = await setup();
    const browser = new Browser(gateway.port);
    await browser.opened();
    browser.socket.send(JSON.stringify({ op: "step", count: 1 }));
    await waitUntil(() => browser.closeCode !== null);
    expect(browser.closeCode).toBe(1008);
    expect(runtime!.published).toEqual([]);
  });

  it("forwards a valid step only with GRIDBOT_TEST_CONTROL", async () => {
    const { gateway, runtime } = await setup({ testControl: true });
    const browser = new Browser(gateway.port);
    await browser.waitFor((m) => m.type === "status" && m.testControl);
    browser.socket.send(JSON.stringify({ op: "step", count: 3 }));
    await waitUntil(() => runtime!.published.length > 0);
    expect(runtime!.published).toEqual(['/test/step {"count":3}']);
  });

  it.each([0, 1001])("rejects a step count of %i", async (count) => {
    const { gateway, runtime } = await setup({ testControl: true });
    const browser = new Browser(gateway.port);
    await browser.opened();
    browser.socket.send(JSON.stringify({ op: "step", count }));
    await waitUntil(() => browser.closeCode !== null);
    expect(browser.closeCode).toBe(1008);
    expect(runtime!.published).toEqual([]);
  });

  it("closes sockets that send oversized frames", async () => {
    const { gateway } = await setup({ testControl: true });
    const browser = new Browser(gateway.port);
    await browser.opened();
    browser.socket.send("x".repeat(2048));
    await waitUntil(() => browser.closeCode !== null);
    expect(browser.closeCode).toBe(1009);
  });

  it("refuses a connection over the client limit", async () => {
    const { gateway } = await setup({ maxClients: 1 });
    const first = new Browser(gateway.port);
    await first.opened();
    const second = new Browser(gateway.port);
    await waitUntil(() => second.closeCode !== null);
    expect(second.socket.readyState).toBe(WebSocket.CLOSED);
    expect(gateway.viewerCount).toBe(1);
  });

  it("rejects sockets on other paths", async () => {
    const { gateway } = await setup({ runtime: false });
    const browser = new Browser(gateway.port, "/other");
    await waitUntil(() => browser.closeCode !== null);
    expect(gateway.viewerCount).toBe(0);
  });

  it("serves the UI with a same-origin CSP", async () => {
    const { gateway } = await setup({ runtime: false });
    const page = await get(gateway.port, "/");
    expect(page.status).toBe(200);
    expect(page.body).toContain("Gridbot");
    expect(page.headers["content-type"]).toBe("text/html; charset=utf-8");
    expect(page.headers["content-security-policy"]).toContain(
      "default-src 'self'",
    );
    expect(page.headers["x-content-type-options"]).toBe("nosniff");
    const script = await get(gateway.port, "/app.js");
    expect(script.headers["content-type"]).toBe(
      "text/javascript; charset=utf-8",
    );
  });

  it.each([
    "/../secret.txt",
    "/%2e%2e/secret.txt",
    "/..%2fsecret.txt",
    "/missing.js",
    "/%00",
  ])("returns 404 for %s", async (path) => {
    const { gateway } = await setup({ runtime: false });
    const response = await get(gateway.port, path);
    expect(response.status).toBe(404);
    expect(response.body).not.toContain("secret");
  });
});
