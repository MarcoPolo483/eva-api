import type { Middleware } from "../types.js";
import { getOrCreateCorrelationId } from "../util/correlation.js";

export function requestLogger(): Middleware {
  return async (ctx, next) => {
    const start = Date.now();
    const corr = getOrCreateCorrelationId(ctx.req.headers as any);
    ctx.state.correlationId = corr;
    ctx.res.setHeader("x-correlation-id", corr);
    ctx.res.setHeader("x-request-id", ctx.state.requestId);

    await next();

    const dur = Date.now() - start;
    const log = {
      ts: new Date().toISOString(),
      reqId: ctx.state.requestId,
      corrId: corr,
      method: ctx.req.method,
      path: new URL(ctx.req.url || "", `http://${ctx.req.headers.host || "local"}`).pathname,
      status: ctx.res.statusCode,
      durMs: dur
    };
    process.stdout.write(JSON.stringify(log) + "\n");
  };
}