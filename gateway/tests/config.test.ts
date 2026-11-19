import { describe, expect, it } from "vitest";
import { readConfig } from "../src/config.js";

describe("readConfig", () => {
  it("uses local defaults", () => {
    expect(readConfig({}, "/app/ui")).toEqual({
      host: "127.0.0.1",
      port: 8080,
      uiDir: "/app/ui",
      runtimeUrl: "ws://127.0.0.1:8765",
      testControl: false,
      maxClients: 100,
      reconnectMs: 1000,
    });
  });

  it("enables test control only for the exact value 1", () => {
    expect(readConfig({ GRIDBOT_TEST_CONTROL: "1" }, "/ui").testControl).toBe(
      true,
    );
    expect(
      readConfig({ GRIDBOT_TEST_CONTROL: "true" }, "/ui").testControl,
    ).toBe(false);
  });

  it("reads overrides", () => {
    const config = readConfig(
      {
        GRIDBOT_HOST: "0.0.0.0",
        GRIDBOT_PORT: "9000",
        GRIDBOT_UI_DIR: "/srv/ui",
        GRIDBOT_RUNTIME_URL: "ws://runner:8765",
      },
      "/ui",
    );
    expect(config).toMatchObject({
      host: "0.0.0.0",
      port: 9000,
      uiDir: "/srv/ui",
      runtimeUrl: "ws://runner:8765",
    });
  });

  it.each(["0", "65536", "80a", ""])("rejects port %j", (port) => {
    expect(() => readConfig({ GRIDBOT_PORT: port }, "/ui")).toThrow(
      "GRIDBOT_PORT",
    );
  });

  it.each(["http://runner", "not a url"])("rejects runtime URL %j", (url) => {
    expect(() => readConfig({ GRIDBOT_RUNTIME_URL: url }, "/ui")).toThrow(
      "GRIDBOT_RUNTIME_URL",
    );
  });
});
