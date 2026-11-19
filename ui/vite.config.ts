import { defineConfig } from "vite";

// The dev server forwards /ws to a gateway on GRIDBOT_PORT (default 8080).
const gatewayPort = process.env.GRIDBOT_PORT ?? "8080";

export default defineConfig({
  build: { outDir: "dist", emptyOutDir: true },
  server: {
    proxy: { "/ws": { target: `ws://127.0.0.1:${gatewayPort}`, ws: true } },
  },
});
