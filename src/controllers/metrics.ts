import type { Handler, Middleware } from "../types.js";

const counters = {
  total: 0,
  byPath: new Map<string, number>(),
  byStatus: new Map<number, number>()
};

export const metricsMiddleware: Middleware = async (ctx, next) => {
  counters.total++;
  const path = new URL(ctx.req.url || "", `http://${ctx.req.headers.host || "local"}`).pathname;
  counters.byPath.set(path, (counters.byPath.get(path) ?? 0) + 1);
  await next();
  counters.byStatus.set(ctx.res.statusCode, (counters.byStatus.get(ctx.res.statusCode) ?? 0) + 1);
};

export const metrics: Handler = (ctx) => {
  const byPath: Record<string, number> = {};
  counters.byPath.forEach((v, k) => (byPath[k] = v));
  const byStatus: Record<string, number> = {};
  counters.byStatus.forEach((v, k) => (byStatus[String(k)] = v));
  ctx.json(200, { total: counters.total, byPath, byStatus });
};