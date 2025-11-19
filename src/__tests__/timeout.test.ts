import http from "http";

import { describe, it, expect, beforeAll, afterAll } from "vitest";

import { App } from "../router.js";
import { withTimeout } from "../middleware/timeout.js";
import { requestId } from "../middleware/requestId.js";
import { attachResponders } from "../util/response.js";

let server: any;
let base: string;

beforeAll(async () => {
  const app = new App();
  app.use(requestId());
  app.use(withTimeout(50)); // short timeout
  app.route("GET", "/slow", async (ctx) => {
    await new Promise((r) => setTimeout(r, 200));
    ctx.json(200, { ok: true });
  });
  const handler = app.compose();
  server = http.createServer((req, res) => {
    handler(req, res).catch((e) => {
      if (!res.headersSent) {
        res.statusCode = 500;
        res.end(JSON.stringify({ error: { code: "INTERNAL", message: e?.message || "Unhandled" } }));
      }
    });
  });
  server.listen(0);
  await new Promise<void>((resolve) => server.on("listening", resolve));
  const addr = server.address();
  base = `http://127.0.0.1:${addr.port}`;
});

afterAll(async () => {
  await new Promise<void>((resolve) => server.close(() => resolve()));
});

it("responds 504 on timeout", async () => {
  const r = await fetch(`${base}/slow`);
  expect(r.status).toBe(504);
});
