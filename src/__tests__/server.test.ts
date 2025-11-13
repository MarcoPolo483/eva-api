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

it("health endpoints", async () => {
  const r = await fetch(`${base}/healthz`);
  expect(r.status).toBe(200);
  const j = await r.json();
  expect(j.ok).toBe(true);
});

it("echo endpoints", async () => {
  const r1 = await fetch(`${base}/api/v1/echo?x=42`);
  expect(r1.status).toBe(200);
  const j1 = await r1.json();
  expect(j1.x).toBe("42");

  const r2 = await fetch(`${base}/api/v1/echo`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ a: 1 })
  });
  expect(r2.status).toBe(200);
  const j2 = await r2.json();
  expect(j2.body).toEqual({ a: 1 });
});

it("cors preflight", async () => {
  const r = await fetch(`${base}/api/v1/echo`, { method: "OPTIONS" });
  expect(r.status).toBe(204);
  expect(r.headers.get("access-control-allow-origin")).toBe("*");
});

it("body limit", async () => {
  const big = "x".repeat(5000);
  const r = await fetch(`${base}/api/v1/echo`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ big })
  });
  expect(r.status).toBe(400); // parser throws BAD_REQUEST "Payload too large"
});

it("secure endpoint requires role", async () => {
  const r1 = await fetch(`${base}/api/v1/secure`);
  expect(r1.status).toBe(401);

  const r2 = await fetch(`${base}/api/v1/secure`, {
    headers: { "x-user-id": "u1", "x-roles": "admin" }
  });
  expect(r2.status).toBe(200);
  const j = await r2.json();
  expect(j.user.id).toBe("u1");
});