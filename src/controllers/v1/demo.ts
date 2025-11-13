import type { Handler } from "../../types.js";
import { parsePagination } from "../../util/pagination.js";
import { weakEtagFromString } from "../../util/etag.js";

export const getEcho: Handler = (ctx) => {
  const x = ctx.query.get("x") ?? "";
  const body = JSON.stringify({ x });
  const etag = weakEtagFromString(body);
  ctx.res.setHeader("ETag", etag);
  // Conditional GET
  const inm = ctx.req.headers["if-none-match"];
  if (typeof inm === "string" && inm === etag) {
    ctx.send(304);
    return;
  }
  ctx.json(200, { x });
};

export const postEcho: Handler = (ctx) => {
  ctx.json(200, { body: ctx.req.body ?? null });
};

export const getSecure: Handler = (ctx) => {
  const user = ctx.state.user;
  ctx.json(200, { ok: true, user, version: ctx.state.apiVersion });
};

export const listUsers: Handler = (ctx) => {
  const { limit, offset } = parsePagination(ctx.query);
  const items = Array.from({ length: limit }).map((_, i) => ({ id: `u${offset + i + 1}` }));
  ctx.json(200, { items, limit, offset });
};