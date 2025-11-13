import type { Middleware } from "../types.js";
import { generateId } from "../util/correlation.js";

export function requestId(): Middleware {
  return async (ctx, next) => {
    const incoming = ctx.req.headers["x-request-id"];
    ctx.state.requestId = (Array.isArray(incoming) ? incoming[0] : incoming) || generateId();
    ctx.res.setHeader("x-request-id", ctx.state.requestId);
    await next();
  };
}