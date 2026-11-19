import type { GatewayOptions } from "./server.js";

const MAX_PORT = 65535;
const DEFAULT_PORT = "8080";
const MAX_CLIENTS = 100;
const RECONNECT_MS = 1000;

function port(text: string): number {
  const value = /^\d+$/.test(text) ? Number(text) : Number.NaN;
  if (!Number.isInteger(value) || value < 1 || value > MAX_PORT) {
    throw new Error(`GRIDBOT_PORT must be 1 to ${MAX_PORT}`);
  }
  return value;
}

function runtimeUrl(text: string): string {
  let url: URL;
  try {
    url = new URL(text);
  } catch {
    throw new Error("GRIDBOT_RUNTIME_URL must be a ws:// or wss:// URL");
  }
  if (url.protocol !== "ws:" && url.protocol !== "wss:") {
    throw new Error("GRIDBOT_RUNTIME_URL must be a ws:// or wss:// URL");
  }
  return text;
}

/** Read gateway settings from the environment, failing fast on bad values. */
export function readConfig(
  env: Record<string, string | undefined>,
  defaultUiDir: string,
): GatewayOptions {
  return {
    host: env.GRIDBOT_HOST ?? "127.0.0.1",
    port: port(env.GRIDBOT_PORT ?? DEFAULT_PORT),
    uiDir: env.GRIDBOT_UI_DIR ?? defaultUiDir,
    runtimeUrl: runtimeUrl(env.GRIDBOT_RUNTIME_URL ?? "ws://127.0.0.1:8765"),
    testControl: env.GRIDBOT_TEST_CONTROL === "1",
    maxClients: MAX_CLIENTS,
    reconnectMs: RECONNECT_MS,
  };
}
