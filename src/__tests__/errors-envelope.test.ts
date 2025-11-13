import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { startServer } from "../server.js";

let server: any;
let base: string;

beforeAll(async () => {
  server = startServer({ port: 0, bodyLimitBytes: 10, rateLimitRps: 100, corsOrigin: "*", requestTimeoutMs: 5000, supportedVersions: ["1"] });
  await new Promise<void>((resolve) => server.on("listening", resolve));
  const addr = server.address();
  base = `http://127.0.0.1:${addr.port}`;
});

afterAll(async () => {
  await new Promise<void>((resolve) => server.close(() => resolve()));
});

it("returns structured envelope on error with correlationId", async () => {
  // Exceed body limit to trigger 400
  const big = "x".repeat(1000);
  const r = await fetch(`${base}/api/v1/echo`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ big })
  });
  const j = await r.json();
  expect(j.error).toBeDefined();
  expect(j.error.code).toBeDefined();
  expect(j.correlationId).toBeDefined();
});