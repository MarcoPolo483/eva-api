import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { startServer } from "../server.js";

let server: any;
let base: string;

beforeAll(async () => {
  server = startServer({ port: 0, bodyLimitBytes: 1024, rateLimitRps: 100, corsOrigin: "*", requestTimeoutMs: 5000, supportedVersions: ["1","2"] });
  await new Promise<void>((resolve) => server.on("listening", resolve));
  const addr = server.address();
  base = `http://127.0.0.1:${addr.port}`;
});

afterAll(async () => {
  await new Promise<void>((resolve) => server.close(() => resolve()));
});

it("resolves version from path param", async () => {
  const r = await fetch(`${base}/api/v1/echo`);
  expect(r.headers.get("x-api-version")).toBe("1");
});

it("resolves version from header and still routes via path", async () => {
  const r = await fetch(`${base}/api/v2/echo`, { headers: { "x-api-version": "2" } });
  expect(r.headers.get("x-api-version")).toBe("2");
});

it("rejects unsupported version", async () => {
  const r = await fetch(`${base}/api/v9/echo`);
  expect(r.status).toBe(400);
  const j = await r.json();
  expect(j.error.code).toBe("BAD_REQUEST");
});