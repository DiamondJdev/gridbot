import { createRequire } from "node:module";
import type * as WsProtocol from "@foxglove/ws-protocol";
import WebSocket from "ws";

// Node loads this package's CommonJS build, whose named exports it cannot detect, so require it.
const { FoxgloveClient } = createRequire(import.meta.url)(
  "@foxglove/ws-protocol",
) as typeof WsProtocol;
type FoxgloveClient = WsProtocol.FoxgloveClient;

/** The Python SDK speaks foxglove.sdk.v1; foxglove_bridge speaks the other. */
export const SUBPROTOCOLS = [
  "foxglove.sdk.v1",
  FoxgloveClient.SUPPORTED_SUBPROTOCOL,
];
export const STEP_TOPIC = "/test/step";

export type RuntimeOptions = {
  url: string;
  reconnectMs: number;
  testControl: boolean;
  isAllowed: (topic: string) => boolean;
  onStatus: (connected: boolean) => void;
  onMessage: (topic: string, payload: string) => void;
};

/** One subscription to the runtime, reconnecting after every disconnect. */
export class RuntimeLink {
  private client: FoxgloveClient | null = null;
  private stepChannel: number | null = null;
  private retry: NodeJS.Timeout | null = null;
  private connected = false;
  private closed = false;
  private readonly decoder = new TextDecoder();

  constructor(private readonly options: RuntimeOptions) {}

  start(): void {
    const ws = new WebSocket(this.options.url, SUBPROTOCOLS);
    const client = new FoxgloveClient({ ws });
    const topics = new Map<number, string>();
    this.client = client;
    client.on("serverInfo", (info) => {
      this.setConnected(true);
      if (
        this.options.testControl &&
        info.capabilities.includes("clientPublish")
      ) {
        this.stepChannel = client.advertise({
          topic: STEP_TOPIC,
          encoding: "json",
          schemaName: "gridbot/TestStep",
        });
      }
    });
    client.on("advertise", (channels) => {
      for (const channel of channels) {
        if (
          channel.encoding === "json" &&
          this.options.isAllowed(channel.topic)
        ) {
          topics.set(client.subscribe(channel.id), channel.topic);
        }
      }
    });
    client.on("message", ({ subscriptionId, data }) => {
      const topic = topics.get(subscriptionId);
      if (topic) this.options.onMessage(topic, this.decoder.decode(data));
    });
    client.on("error", () => undefined);
    client.on("close", () => this.handleClose(client));
  }

  /** Forward a test step. Returns false when the runtime cannot take it. */
  sendStep(count: number): boolean {
    if (this.client === null || this.stepChannel === null) return false;
    const payload = new TextEncoder().encode(JSON.stringify({ count }));
    this.client.sendMessage(this.stepChannel, payload);
    return true;
  }

  close(): void {
    this.closed = true;
    if (this.retry) clearTimeout(this.retry);
    this.client?.close();
  }

  private handleClose(client: FoxgloveClient): void {
    if (this.client !== client) return;
    this.client = null;
    this.stepChannel = null;
    this.setConnected(false);
    if (!this.closed) {
      this.retry = setTimeout(() => this.start(), this.options.reconnectMs);
    }
  }

  private setConnected(connected: boolean): void {
    if (this.connected === connected) return;
    this.connected = connected;
    this.options.onStatus(connected);
  }
}
