import { fileURLToPath } from "node:url";
import { readConfig } from "./config.js";
import { startGateway } from "./server.js";

const VERSION_LINE = "gridbot-gateway 0.1.0";

async function main(): Promise<void> {
  if (process.argv.includes("--version")) {
    console.info(VERSION_LINE);
    return;
  }
  const defaultUi = fileURLToPath(new URL("../../ui/dist", import.meta.url));
  const config = readConfig(process.env, defaultUi);
  const gateway = await startGateway(config);
  console.info(
    `${VERSION_LINE} listening on ${config.host}:${gateway.port}` +
      (config.testControl ? " with test control" : ""),
  );
  const stop = () => void gateway.close().then(() => process.exit(0));
  process.on("SIGTERM", stop);
  process.on("SIGINT", stop);
}

main().catch((error: unknown) => {
  console.error(
    `gridbot-gateway: ${error instanceof Error ? error.message : String(error)}`,
  );
  process.exit(1);
});
