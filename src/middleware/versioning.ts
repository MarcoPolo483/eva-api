import type { Middleware } from "../types.js";
import { errors } from "../util/errors.js";

export function versionNegotiation(supported: string[], defaultVersion = "1"): Middleware {
  const set = new Set(supported);
  return async (ctx, next) => {
    let v = header(ctx.req.headers, "x-api-version");
    // Try to infer from path param `version` if present
    if (!v && ctx.params?.version) {
      const pv = ctx.params.version.replace(/^v/i, "");
      v = pv;
    }
    v = v || defaultVersion;

    if (!set.has(v)) {
      throw errors.badRequest(`Unsupported API version "${v}"`, { supported: Array.from(set) });
    }

    ctx.state.apiVersion = v;
    ctx.res.setHeader("x-api-version", v);
    await next();
  };
}

function header(headers: Record<string, string | string[] | undefined>, key: string): string | undefined {
  const v = headers[key] ?? headers[key.toLowerCase()];
  if (Array.isArray(v)) return v[0];
  return v;
}