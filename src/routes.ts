import type { IncomingMessage, ServerResponse } from "http";
import { createRagEventsServer } from "../../src/rag/api/events.js";
import { RagApiRouter } from "../../src/rag/api/router.js";
import { IngestionContextRegistry } from "../../src/rag/ingestion/contextRegistry.js";
import { RagIngestionOrchestratorExtended } from "../../src/rag/ingestion/orchestrator-extended.js";
import { DefaultSourceResolver } from "../../src/rag/ingestion/loadSources.js";
import { SimpleLineChunker } from "../../src/rag/ingestion/chunkPhase.js";
import { MockEmbedder } from "../../src/rag/ingestion/embedPhase.js";
import { InMemoryVectorIndex } from "../../src/rag/ingestion/indexPhase.js";
import { InMemoryManifestStore } from "../../src/rag/ingestion/manifestStore.js";
import { InMemoryIndexSnapshotStore } from "../../src/rag/ingestion/indexSnapshotStore.js";
import { NoopSafetyGate } from "../../src/rag/ingestion/safetyGate.js";
import { withEvents } from "../../src/rag/ingestion/orchestrator-hooks.js";
import { EventHub } from "../../src/rag/events/eventHub.js";
import { listJobs, jobAction } from "../../src/ops/batchApi.js";
import { BatchScheduler } from "../../src/scheduler/batchScheduler.js";
import { createLogger } from "../../src/logging/logger.js";
import { RingBufferSink } from "../../src/logging/sinks.js";
import { MeterRegistry } from "../../src/core/registry.js";
import { prometheusText } from "../../src/exporters/prometheus.js";
import { httpMetrics } from "./httpMetrics.js";
import { authorize, isPublicRoute, type AuthConfig } from "./auth.js";

export type ApiDeps = {
  meter: MeterRegistry;
  scheduler: BatchScheduler;
  registry: IngestionContextRegistry;
  orchestrator: RagIngestionOrchestratorExtended;
  ragRouter: RagApiRouter;
  sseHandler: (req: IncomingMessage, res: ServerResponse) => void;
  auth: AuthConfig;
};

export function buildApi(auth: AuthConfig = {}): ApiDeps {
  const meter = new MeterRegistry();
  const sink = new RingBufferSink(200);
  const logger = createLogger({ level: "info", sinks: [sink] });
  const scheduler = new BatchScheduler(logger, { maxConcurrent: 4 }, undefined, undefined, meter);

  const registry = new IngestionContextRegistry();
  const orchestrator = new RagIngestionOrchestratorExtended(
    scheduler,
    new DefaultSourceResolver(),
    new SimpleLineChunker(100),
    new MockEmbedder(),
    new InMemoryVectorIndex(),
    undefined,
    new InMemoryManifestStore(),
    undefined,
    new NoopSafetyGate(),
    new InMemoryIndexSnapshotStore(),
    registry,
    { metrics: meter }
  );

  const hub = new EventHub(500);
  withEvents(orchestrator, hub);
  const sse = createRagEventsServer(hub);

  const ragRouter = new RagApiRouter(
    orchestrator,
    registry,
    async (req) => authorize(req, auth)
  );

  return {
    meter,
    scheduler,
    registry,
    orchestrator,
    ragRouter,
    sseHandler: sse.handler,
    auth
  };
}

export function createRequestHandler(deps: ApiDeps) {
  const instrument = httpMetrics(deps.meter);

  return async function handler(req: IncomingMessage, res: ServerResponse) {
    const url = req.url || "/";
    const method = (req.method || "GET").toUpperCase();

    // Authorization
    if (!isPublicRoute(url, method, deps.auth)) {
      const ok = await authorize(req, deps.auth);
      if (!ok) {
        res.statusCode = 403;
        res.setHeader("content-type", "application/json");
        res.end(JSON.stringify({ error: "forbidden" }));
        return;
      }
    }

    const routeKey = routeTag(url, method);

    await instrument(req, res, routeKey, async () => {
      // Metrics
      if (url.startsWith("/ops/metrics") && method === "GET") {
        res.setHeader("content-type", "text/plain");
        res.end(prometheusText(deps.meter.snapshot()));
        return;
      }

      // Batch ops
      if (url.startsWith("/ops/batch")) {
        if (method === "GET") {
          res.setHeader("content-type", "application/json");
          res.end(JSON.stringify(listJobs(deps.scheduler)));
          return;
        }
        if (method === "POST") {
          let body = "";
          req.on("data", (c) => (body += c));
          req.on("end", () => {
            try {
              const { id, action, overrides } = JSON.parse(body || "{}");
              if (!id || !action) {
                res.statusCode = 400;
                res.end(JSON.stringify({ error: "Missing id or action" }));
                return;
              }
              const result = jobAction(deps.scheduler, id, action, overrides);
              res.setHeader("content-type", "application/json");
              res.end(JSON.stringify(result));
            } catch (e: any) {
              res.statusCode = 400;
              res.end(JSON.stringify({ error: e?.message || "Invalid JSON" }));
            }
          });
          return;
        }
      }

      // RAG events (SSE)
      if (url === "/rag/events" && method === "GET") {
        deps.sseHandler(req, res);
        return;
      }

      // RAG API (ingest/status/manifest/phases/rollback)
      if (url.startsWith("/rag/")) {
        await deps.ragRouter.handle(req, res);
        return;
      }

      res.statusCode = 404;
      res.end("Not Found");
    });
  };
}

function routeTag(url: string, method: string): string {
  if (url.startsWith("/ops/metrics")) return `${method} /ops/metrics`;
  if (url.startsWith("/ops/batch")) return `${method} /ops/batch`;
  if (url.startsWith("/rag/events")) return `${method} /rag/events`;
  if (url.startsWith("/rag/ingest") && url.endsWith("/status")) return `${method} /rag/ingest/:id/status`;
  if (url.startsWith("/rag/ingest") && url.endsWith("/manifest")) return `${method} /rag/ingest/:id/manifest`;
  if (url.startsWith("/rag/ingest") && url.endsWith("/phases")) return `${method} /rag/ingest/:id/phases`;
  if (url.startsWith("/rag/ingest") && url.endsWith("/rollback")) return `${method} /rag/ingest/:id/rollback`;
  if (url.startsWith("/rag/ingest")) return `${method} /rag/ingest`;
  return `${method} *`;
}