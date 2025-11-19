import type { IncomingMessage, ServerResponse } from "http";
// Import MeterRegistry from eva-ops
import { MeterRegistry } from "../../src/core/registry.js";

type Handler = (req: IncomingMessage, res: ServerResponse) => Promise<void> | void;

export function httpMetrics(meter: MeterRegistry) {
  const counter = meter.counter("http_requests_total", "HTTP requests", ["method", "path", "code"]);
  const hist = meter.histogram(
    "http_request_duration_seconds",
    "HTTP request duration seconds",
    ["path"],
    // default buckets in seconds
    [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
  );

  return async (req: IncomingMessage, res: ServerResponse, routeKey: string, handler: Handler) => {
    const start = process.hrtime.bigint();
    let finished = false;

    const onFinish = () => {
      if (finished) return;
      finished = true;
      const durNs = Number(process.hrtime.bigint() - start);
      const durSec = durNs / 1e9;
      const code = String(res.statusCode || 200);
      counter.inc({ method: (req.method || "GET").toUpperCase(), path: routeKey, code }, 1);
      hist.observe({ path: routeKey }, durSec);
    };

    res.once("finish", onFinish);
    res.once("close", onFinish);

    try {
      await handler(req, res);
    } catch (e: any) {
      res.statusCode = 500;
      res.setHeader("content-type", "application/json");
      res.end(JSON.stringify({ error: e?.message || "internal" }));
    } finally {
      onFinish();
    }
  };
}