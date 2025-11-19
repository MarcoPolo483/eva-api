import { describe, it, expect, beforeAll, afterAll } from "vitest";
import http from "http";
import { buildApi, createRequestHandler } from "../routes";

let server: http.Server;
let base: string;

beforeAll(async () => {
  const deps = buildApi({ apiKey: "k", metricsPublic: true, ssePublic: true });
  const handler = createRequestHandler(deps);
  server = http.createServer((req, res) => void handler(req, res));
  await new Promise<void>((r) => server.listen(0, r));
  const addr = server.address() as any;
  base = `http://127.0.0.1:${addr.port}`;
});

afterAll(async () => {
  await new Promise<void>((r) => server.close(() => r()));
});

it("serves metrics without auth when public", async () => {
  const r = await fetch(`${base}/ops/metrics`);
  expect(r.ok).toBe(true);
  const text = await r.text();
  expect(text).toMatch(/http_requests_total/);
});

it("protects ops/batch without API key", async () => {
  const r = await fetch(`${base}/ops/batch`);
  expect(r.status).toBe(403);
});

it("allows ops/batch with API key", async () => {
  const r = await fetch(`${base}/ops/batch`, { headers: { "x-api-key": "k" } });
  expect(r.ok).toBe(true);
  const json = await r.json();
  expect(json.counts).toBeDefined();
});

it("RAG ingest requires auth and returns id", async () => {
  const r = await fetch(`${base}/rag/ingest`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-api-key": "k" },
    body: JSON.stringify({ tenant: "t", inputs: [{ type: "text", content: "Hello" }] })
  });
  expect(r.ok).toBe(true);
  const j = await r.json();
  expect(j.ingestionId).toBeTruthy();
});

it("SSE events is public when enabled", async () => {
  const r = await fetch(`${base}/rag/events`);
  expect(r.ok).toBe(true);
});