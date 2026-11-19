import { resolve } from "node:path";
import { defineConfig, devices } from "@playwright/test";

const ROOT = resolve(import.meta.dirname, "..");
const RUNNER_PORT = 18765;
const GATEWAY_PORT = 18080;

export default defineConfig({
  testDir: "tests",
  outputDir: resolve(ROOT, "artifacts/playwright"),
  timeout: 180_000,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  reporter: [["list"]],
  use: {
    ...devices["Desktop Chrome"],
    baseURL: `http://127.0.0.1:${GATEWAY_PORT}`,
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: `uv run gridbot-run scenarios/drive-01.json --serve --test-control --port ${RUNNER_PORT}`,
      cwd: ROOT,
      port: RUNNER_PORT,
      reuseExistingServer: false,
      gracefulShutdown: { signal: "SIGTERM", timeout: 5_000 },
    },
    {
      command:
        "pnpm --filter @gridbot/ui build && pnpm --filter @gridbot/gateway build && node gateway/dist/main.js",
      cwd: ROOT,
      url: `http://127.0.0.1:${GATEWAY_PORT}/healthz`,
      reuseExistingServer: false,
      gracefulShutdown: { signal: "SIGTERM", timeout: 5_000 },
      env: {
        GRIDBOT_PORT: String(GATEWAY_PORT),
        GRIDBOT_RUNTIME_URL: `ws://127.0.0.1:${RUNNER_PORT}`,
        GRIDBOT_TEST_CONTROL: "1",
      },
    },
  ],
});
