import type { Context } from "../types.js";

export function attachResponders(ctx: Context) {
  ctx.send = (status, payload, headers) => {
    if (ctx.res.headersSent) return;
    if (headers) for (const [k, v] of Object.entries(headers)) ctx.res.setHeader(k, v);
    if (payload === undefined || payload === null) {
      ctx.res.statusCode = status;
      ctx.res.end();
      return;
    }
    if (typeof payload === "string" || payload instanceof Uint8Array) {
      ctx.res.statusCode = status;
      ctx.res.end(payload);
      return;
    }
    const body = JSON.stringify(payload);
    ctx.res.statusCode = status;
    ctx.res.setHeader("content-type", "application/json; charset=utf-8");
    ctx.res.end(body);
  };

  ctx.json = (status, payload, headers) => ctx.send(status, payload, headers);
  ctx.text = (status, payload, headers) => {
    if (headers) for (const [k, v] of Object.entries(headers)) ctx.res.setHeader(k, v);
    ctx.res.statusCode = status;
    ctx.res.setHeader("content-type", "text/plain; charset=utf-8");
    ctx.res.end(payload);
  };

  ctx.notFound = () => ctx.json(404, { error: { code: "NOT_FOUND", message: "Not Found" }, correlationId: ctx.state.correlationId });
  ctx.unauthorized = (m = "Unauthorized") => ctx.json(401, { error: { code: "UNAUTHORIZED", message: m }, correlationId: ctx.state.correlationId });
  ctx.forbidden = (m = "Forbidden") => ctx.json(403, { error: { code: "FORBIDDEN", message: m }, correlationId: ctx.state.correlationId });
  ctx.badRequest = (m = "Bad Request") => ctx.json(400, { error: { code: "BAD_REQUEST", message: m }, correlationId: ctx.state.correlationId });
}