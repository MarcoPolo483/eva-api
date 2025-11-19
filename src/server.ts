import http from "http";

import { App } from "./router.js";
import { loadConfig } from "./util/config.js";
import { cors } from "./middleware/cors.js";
import { jsonBodyParser } from "./middleware/json.js";
import { rateLimit } from "./middleware/rateLimit.js";
import { authFromHeaders, requireRole } from "./middleware/auth.js";
import { requestLogger } from "./middleware/logging.js";
import { errorHandler } from "./middleware/error.js";
import { healthz, readyz } from "./controllers/health.js";
import { metrics, metricsMiddleware } from "./controllers/metrics.js";
import { getEcho, postEcho, getSecure, listUsers } from "./controllers/v1/demo.js";
import { getUserById } from "./controllers/v1/users.js";
import { requestId } from "./middleware/requestId.js";
import { withTimeout } from "./middleware/timeout.js";
import { securityHeaders } from "./middleware/security.js";
import { versionNegotiation } from "./middleware/versioning.js";

export function createApp(cfg = loadConfig()) {
  const app = new App();

  app.use(errorHandler());
  app.use(requestId());
  app.use(requestLogger());
  app.use(metricsMiddleware);
  app.use(securityHeaders());
  app.use(cors(cfg.corsOrigin));
  app.use(rateLimit(cfg.rateLimitRps));
  app.use(authFromHeaders());
  app.use(withTimeout(cfg.requestTimeoutMs));
  app.use(jsonBodyParser(cfg.bodyLimitBytes));
  app.use(versionNegotiation(cfg.supportedVersions, cfg.supportedVersions[0] || "1"));

  // Health and metrics
  app.route("GET", "/healthz", healthz);
  app.route("GET", "/readyz", readyz);
  app.route("GET", "/metrics", metrics);

  // Versioned API (uses :version param; header x-api-version also supported)
  app.route("GET", "/api/:version/echo", getEcho);
  app.route("POST", "/api/:version/echo", postEcho);
  app.route("GET", "/api/:version/users", listUsers);
  app.route("GET", "/api/:version/users/:id", getUserById);

  // Secure endpoints (requires admin) - wrap handler with auth check
  const secureMiddleware = requireRole("admin");
  app.route("GET", "/api/:version/secure", async (ctx) => {
    await secureMiddleware(ctx, async () => getSecure(ctx));
  });

  return app;
}

export function startServer(cfg = loadConfig()) {
  const app = createApp(cfg);
  const handler = app.compose();
  const server = http.createServer((req, res) => {
    (req as any).ip = req.socket.remoteAddress;
    handler(req, res).catch((e) => {
      res.statusCode = 500;
      res.end(JSON.stringify({ error: { code: "INTERNAL", message: e?.message || "Unhandled" } }));
    });
  });
  server.listen(cfg.port, () => {

    console.log(`eva-api listening on :${cfg.port}`);
  });
  return server;
}

if (process.argv[1] && process.argv[1].endsWith("server.js")) {
  startServer();
}
