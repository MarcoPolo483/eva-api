import "dotenv/config";
import http from "http";
import { buildApi, createRequestHandler } from "./routes.js";

const PORT = Number(process.env.PORT || 8088);
const API_KEY = process.env.API_KEY || "";
const METRICS_PUBLIC = String(process.env.METRICS_PUBLIC || "false").toLowerCase() === "true";
const SSE_PUBLIC = String(process.env.SSE_PUBLIC || "false").toLowerCase() === "true";

async function main() {
  const deps = buildApi({ apiKey: API_KEY, metricsPublic: METRICS_PUBLIC, ssePublic: SSE_PUBLIC });
  const handler = createRequestHandler(deps);

  const server = http.createServer((req, res) => {
    void handler(req, res);
  });

  server.listen(PORT, () => {
    // eslint-disable-next-line no-console
    console.log(JSON.stringify({ msg: "eva-api listening", port: PORT, metricsPublic: METRICS_PUBLIC, ssePublic: SSE_PUBLIC }));
  });

  // Graceful shutdown
  const stop = () => {
    // eslint-disable-next-line no-console
    console.log("Shutting down eva-api...");
    server.close(() => process.exit(0));
  };
  process.on("SIGINT", stop);
  process.on("SIGTERM", stop);
}

void main();