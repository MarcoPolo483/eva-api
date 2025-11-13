import { describe, it, expect, beforeAll, afterAll } from "vitest";
import http from "http";
import { App } from "../router.js";
import { jsonBodyParser } from "../middleware/json.js";
import { validateBody } from "../middleware/validate.js";
import { errorHandler } from "../middleware/error.js";

let server: any;
let base: string;

beforeAll(async () => {
  const app = new App();
  app.use(errorHandler());
  app.use(jsonBodyParser(1024));
  app.use(
    validateBody({
      type: "object",
      properties: {
        name: { type: "string", required: true, min: 1 },
        age: { type: "number", required: true, min: 0 }
      }
    })
  );
  app.route("POST", "/submit", (ctx) => ctx.json(200, { ok: true }));
  const handler = app.compose();
  server = http.createServer((req, res) => handler(req, res).catch((e) => {
    if (!res.headersSent) {
      res.statusCode = 500;
      res.end(JSON.stringify({ error: { code: "INTERNAL", message: e?.message || "Unhandled" } }));
    }
  }));
  server.listen(0);
  await new Promise<void>((resolve) => server.on("listening", resolve));
  const addr = server.address();
  base = `http://127.0.0.1:${addr.port}`;
});

afterAll(async () => {
  await new Promise<void>((resolve) => server.close(() => resolve()));
});

it("fails validation with structured errors", async () => {
  const r = await fetch(`${base}/submit`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ name: "", age: -1 })
  });
  expect(r.status).toBe(400);
  const j = await r.json();
  expect(j.error.code).toBe("BAD_REQUEST");
  expect(Array.isArray(j.error.details?.errors)).toBe(true);
});