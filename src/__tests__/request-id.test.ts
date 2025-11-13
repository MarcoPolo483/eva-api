import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { startServer } from "../server.js";

let server: any;
let base: string;

beforeAll(async () => {
  server = startServer({ port: 0, bodyLimitBytes: 1024, rateLimitRps: 100, corsOrigin: "*", requestTimeoutMs: 5000, supportedVersions: ["1"] });
  await new Promise<void>((resolve) => server.on("listening", resolve));
  const addr = server.address();
  base = `http://127.0.0.1:${addr.port}`;
});

afterAll(async () => {
  await new Promise<void>((resolve) => server.close(() => resolve()));
});

it("propagates x-request-id", async () => {
  const r = await fetch(`${base}/api/v1/echo`, { headers: { "x-request-id": "abc123" } });
  expect(r.headers.get("x-request-id")).toBe("abc123");
});