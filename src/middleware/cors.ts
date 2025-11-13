import type { Middleware } from "../types.js";

export function cors(origin: string): Middleware {
  return async (ctx, next) => {
    const res = ctx.res;
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Vary", "Origin");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Correlation-Id, X-User-Id, X-Roles, X-Request-Id, X-Api-Version");
    res.setHeader("Access-Control-Allow-Methods", "GET,POST,PUT,PATCH,DELETE,OPTIONS");
    res.setHeader("Access-Control-Expose-Headers", "X-Correlation-Id, X-Request-Id, ETag");

    if (ctx.req.method?.toUpperCase() === "OPTIONS") {
      res.statusCode = 204;
      res.end();
      return;
    }

    await next();
  };
}