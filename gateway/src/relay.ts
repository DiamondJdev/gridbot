import { isAllowedTopic, type ServerMessage, type Stamp } from "./protocol.js";

/** The part of a browser socket the relay needs. */
export interface Viewer {
  send(data: string): void;
  readonly bufferedAmount: number;
}

export type RelayOptions = { testControl: boolean; maxBufferedBytes: number };
export type Health = { runtimeConnected: boolean; lastStamp: Stamp | null };

/** Latched topics are cached for new viewers and never dropped. */
const LATCHED_TOPICS = new Set(["/sim/world", "/tf_static"]);

function telemetryStamp(message: Record<string, unknown>): Stamp | null {
  const stamp = message.stamp as Partial<Stamp> | undefined;
  return Number.isInteger(stamp?.sec) && Number.isInteger(stamp?.nanosec)
    ? { sec: stamp!.sec!, nanosec: stamp!.nanosec! }
    : null;
}

/** Fans runtime messages out to browsers with fixed work per message. */
export class Relay {
  private readonly viewers = new Set<Viewer>();
  private readonly latched = new Map<string, string>();
  private connected = false;
  private lastStamp: Stamp | null = null;

  constructor(private readonly options: RelayOptions) {}

  get viewerCount(): number {
    return this.viewers.size;
  }

  addViewer(viewer: Viewer): void {
    this.viewers.add(viewer);
    viewer.send(this.status());
    for (const envelope of this.latched.values()) viewer.send(envelope);
  }

  removeViewer(viewer: Viewer): void {
    this.viewers.delete(viewer);
  }

  setRuntimeConnected(connected: boolean): void {
    this.connected = connected;
    if (!connected) {
      this.latched.clear();
      this.lastStamp = null;
    }
    const status = this.status();
    for (const viewer of this.viewers) viewer.send(status);
  }

  /** Forward one runtime message. Invalid or blocked messages are dropped. */
  receive(topic: string, payload: string): void {
    if (!isAllowedTopic(topic)) return;
    let message: unknown;
    try {
      message = JSON.parse(payload);
    } catch {
      return;
    }
    if (
      typeof message !== "object" ||
      message === null ||
      Array.isArray(message)
    )
      return;
    if (topic === "/telemetry") {
      this.lastStamp =
        telemetryStamp(message as Record<string, unknown>) ?? this.lastStamp;
    }
    const envelope = JSON.stringify({
      type: "message",
      topic,
      message,
    } satisfies ServerMessage);
    if (LATCHED_TOPICS.has(topic)) {
      if (this.latched.get(topic) === envelope) return;
      this.latched.set(topic, envelope);
    }
    for (const viewer of this.viewers) {
      const slow = viewer.bufferedAmount > this.options.maxBufferedBytes;
      if (!slow || LATCHED_TOPICS.has(topic)) viewer.send(envelope);
    }
  }

  health(): Health {
    return { runtimeConnected: this.connected, lastStamp: this.lastStamp };
  }

  private status(): string {
    return JSON.stringify({
      type: "status",
      runtime: this.connected ? "connected" : "offline",
      testControl: this.options.testControl,
    } satisfies ServerMessage);
  }
}
