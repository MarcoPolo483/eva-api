import type { Handler } from "../types.js";

export const healthz: Handler = (ctx) => ctx.json(200, { ok: true });
export const readyz: Handler = (ctx) => ctx.json(200, { ok: true });